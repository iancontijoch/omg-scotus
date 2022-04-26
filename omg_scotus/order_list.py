from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from typing import Any

from omg_scotus._enums import OrderListSectionType
from omg_scotus.fetcher import Stream
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import require_non_none
from omg_scotus.opinion import Opinion
from omg_scotus.opinion import OpinionType
from omg_scotus.opinion import OrderOpinion
from omg_scotus.opinion import SlipOpinion
from omg_scotus.opinion import Syllabus
from omg_scotus.order_list_section import OrderListSection
from omg_scotus.order_list_section import Section


class DocumentList(ABC):
    text: str
    date: str
    stream: Stream
    sections: list[Opinion | OrderListSection | Section]

    def __init__(self, text: str, date: str, stream: Stream):
        self.text = text
        self.date = date
        self.stream = stream

    @abstractmethod
    def get_title(self) -> str: pass

    @abstractmethod
    def get_sections(self) -> None: pass

    def get_header_name(self) -> str:
        classname = self.__class__.__name__
        if classname == 'OpinionList':
            return 'OPINION LIST'
        elif classname == 'OrderOpinionList':
            return 'OPINION ORDER'
        elif classname == 'OrderList':
            return 'ORDER LIST'
        else:
            raise ValueError


class OpinionList(DocumentList):
    def __init__(
        self, stream: Stream,
        text: str, date: str, holding: str,
        petitioner: str, respondent: str,
        lower_court: str, case_number: str,
        is_per_curiam: bool,
    ) -> None:
        super().__init__(text=text, date=date, stream=stream)
        self.holding = holding
        self.petitioner = petitioner
        self.respondent = respondent
        self.lower_court = lower_court
        self.case_number = case_number
        self.is_per_curiam = is_per_curiam
        self.title = self.get_title()
        self.sections = []
        self.get_sections()

    def get_title(self) -> str:
        """Return Overall Case Name"""
        # TODO
        return 'GET CASE NAME'

    def get_sections(self) -> None:
        """Create and append opinions in Opinion List."""
        # regex pattern looks for text between
        # SUPREME COURT OF THE UNITED STATES
        pattern = (
            r'(SUPREME COURT OF THE UNITED STATES\s\s)(.*?(?=SUPREME COURT '
            r'OF THE UNITED STATES\s\s)|.*$)'
        )
        matches = re.finditer(
            pattern=pattern,
            string=self.text,
            flags=re.DOTALL,
        )

        # the majority opinion (index 1) doesn't contain joiner info
        # so we grab joiners from the syllabus, which does.

        # note: Per Curiams have no syllabi.

        # TODO: Original opinions are being treated as Syllabi. Fix!
        # TODO: Search for original opinions with dissents/concurrences

        for i, m in enumerate(matches):
            section_text = self.text[m.span()[0]: m.span()[1]]
            if (
                i == 0 and not self.is_per_curiam
                and self.stream is Stream.SLIP_OPINIONS
            ):  # syllabus
                syll = Syllabus(
                    text=section_text, petitioner=self.petitioner,
                    respondent=self.respondent,
                    lower_court=self.lower_court,
                    case_number=self.case_number,
                )
                majority_joiners = syll.joiners
                self.sections.append(syll)
            elif self.stream is Stream.SLIP_OPINIONS:
                slip = SlipOpinion(
                    text=section_text,
                    petitioner=self.petitioner,
                    respondent=self.respondent,
                    lower_court=self.lower_court,
                    case_number=self.case_number,
                )
                if i == 1 and not self.is_per_curiam:
                    slip.joiners = majority_joiners
                self.sections.append(slip)
            elif self.stream is Stream.OPINIONS_RELATING_TO_ORDERS:
                self.sections.append(
                    OrderOpinion(
                        text=section_text,
                        petitioner=self.petitioner,
                        respondent=self.respondent,
                        lower_court=self.lower_court,
                        case_number=self.case_number,
                    ),
                )

    def __str__(self) -> str:
        """Return string representation of OpinionList."""
        s = f'{self.date}\n\n'
        s += f"{'OPINION SUMMARY':~^{72}}"
        s += f'\nHeld:\n\t{self.holding}\n\n'
        s += '\n'.join([
            str(s) for s in self.sections
            if s.type is not OpinionType.SYLLABUS
        ])
        return s


class OrderOpinionList(OpinionList):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.title = self.get_title()
        self.sections = []
        self.get_sections()

    def get_title(self) -> str:
        """Return Cite as: (596 U.S.)"""
        # TODO
        pass

    def __str__(self) -> str:
        """Return string representation of OrderOpinionList."""
        s = f'{self.date}\n\n'
        s += f"{'ORDER LIST OPINION SUMMARY':~^{72}}"
        s += '\n'.join([
            str(s) for s in self.sections
            if s.type is not OpinionType.SYLLABUS
        ])
        return s

    def get_sections(self) -> None:
        """Create and append opinions embedded in Order List."""
        # regex pattern looks for text between
        # SUPREME COURT OF THE UNITED STATES
        pattern = (
            r'(SUPREME COURT OF THE UNITED STATES\s\s)(.*?(?=SUPREME COURT '
            r'OF THE UNITED STATES\s\s)|.*$)'
        )
        matches = re.finditer(
            pattern=pattern,
            string=self.text,
            flags=re.DOTALL,
        )
        for m in matches:
            section_text = self.text[m.span()[0]: m.span()[1]]
            self.sections.append(
                OrderOpinion(
                    text=section_text,
                    petitioner=self.petitioner,
                    respondent=self.respondent,
                    lower_court=self.lower_court,
                    case_number=self.case_number,
                ),
            )


class OrderList(DocumentList):
    text: str
    opinions: list[Opinion]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.title = self.get_title()
        self.sections = []
        self.get_sections()

    def get_title(self) -> str:
        """Return Order Title (first non space character through EOL."""
        pattern = r'\S.*\n'
        match = require_non_none(re.search(pattern, self.text))
        return remove_extra_whitespace(match.group())

    def get_date(self) -> str:
        """Return the date of the Order."""
        pattern = r'[A-Z]+DAY\s*\,.*\d\d\d\d'
        match = require_non_none(re.search(pattern, self.text))
        return remove_extra_whitespace(match.group())

    def __str__(self) -> str:
        """Return string representation of OrderList."""
        s = f'\n{self.title}\n{self.date}\n\n'
        s += f"{'ORDER LIST SUMMARY':~^{72}}"
        s += '\n'.join([str(s) for s in self.sections])
        return s

    def get_sections(self) -> None:
        """Create and append OrderListSections for OrderList."""
        # regex pattern looks text between section headers and between
        # last section header and EOF
        pattern = (
            r'(CERTIORARI +-- +SUMMARY +DISPOSITIONS*|ORDERS* +IN +PENDING '
            r'+CASES*|CERTIORARI +GRANTED|CERTIORARI +DENIED|HABEAS +CORPUS '
            r'+DENIED|MANDAMUS +DENIED|REHEARINGS* +DENIED)(.*?(?=CERTIORARI +'
            r'-- +SUMMARY +DISPOSITIONS*|ORDERS* +IN +PENDING +CASES*|CERTIORA'
            r'RI +GRANTED|CERTIORARI +DENIED|HABEAS +CORPUS +DENIED|MANDAMUS +'
            r'DENIED|REHEARINGS* +DENIED)|.*$)'
        )
        matches = re.finditer(
            pattern=pattern,
            string=self.text, flags=re.DOTALL,
        )

        for m in matches:
            section_title, section_content = remove_extra_whitespace(
                m.groups()[0],
            ), m.groups()[1]  # remove whitespace noise

            section = OrderListSection(
                label=section_title,
                type=OrderListSectionType.from_string(
                    section_title,
                ),
                text=section_content,
            )
            self.sections.append(section)

    def get_cases(self) -> list[str]:
        """Return all cases in an orderlist, regardless of section."""
        return [
            str(case.number) for section in self.sections
            for case in section.cases
        ]
