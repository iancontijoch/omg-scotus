from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from typing import Any

from omg_scotus._enums import Disposition
from omg_scotus._enums import OrderSectionType
from omg_scotus.fetcher import Stream
from omg_scotus.helpers import get_disposition_type
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import require_non_none
from omg_scotus.opinion import Opinion
from omg_scotus.opinion import OpinionType
from omg_scotus.opinion import OrderOpinion
from omg_scotus.opinion import SlipOpinion
from omg_scotus.opinion import Syllabus
from omg_scotus.section import OrderSection
from omg_scotus.section import Section


class DocumentList(ABC):
    text: str
    date: str
    url: str
    stream: Stream
    sections: list[Opinion | OrderSection | Section]

    def __init__(self, text: str, date: str, stream: Stream, url: str):
        self.text = text
        self.date = date
        self.stream = stream
        self.url = url

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
    dispositions: list[Disposition]

    def __init__(
        self, stream: Stream,
        url: str,
        text: str, date: str, holding: str,
        disposition_text: str,
        petitioner: str, respondent: str,
        lower_court: str, case_number: str,
        is_per_curiam: bool,
    ) -> None:
        super().__init__(text=text, date=date, stream=stream, url=url)
        self.holding = holding
        self.disposition_text = disposition_text
        self.petitioner = petitioner
        self.respondent = respondent
        self.lower_court = lower_court
        self.case_number = case_number
        self.is_per_curiam = is_per_curiam
        self.title = self.get_title()
        self.sections = []
        self.get_sections()
        self.dispositions = get_disposition_type(self.disposition_text)

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

        # the majority opinion (index 1) doesn't contain joiner/recusal info
        # so we grab joiners and recusals from the syllabus, which does.
        # note: Per Curiams have no syllabi.

        for i, m in enumerate(matches):
            section_text = self.text[m.span()[0]: m.span()[1]]
            if (
                i == 0 and not self.is_per_curiam
                and self.stream is Stream.SLIP_OPINIONS
            ):  # syllabus
                syll = Syllabus(
                    text=section_text, url=self.url,
                    petitioner=self.petitioner,
                    respondent=self.respondent,
                    lower_court=self.lower_court,
                    case_number=self.case_number,
                )
                majority_joiners = syll.joiners
                recusals = syll.recusals
                self.sections.append(syll)
            elif self.stream is Stream.SLIP_OPINIONS:
                slip = SlipOpinion(
                    text=section_text,
                    url=self.url,
                    petitioner=self.petitioner,
                    respondent=self.respondent,
                    lower_court=self.lower_court,
                    case_number=self.case_number,
                )
                if i == 1 and not self.is_per_curiam:
                    slip.joiners = majority_joiners
                    slip.recusals = recusals
                self.sections.append(slip)
            elif self.stream is Stream.OPINIONS_RELATING_TO_ORDERS:
                self.sections.append(
                    OrderOpinion(
                        text=section_text,
                        url=self.url,
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
                    url=self.url,
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
        s += f'\nLink  {self.url}'
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

            section = OrderSection(
                label=section_title,
                type=OrderSectionType.from_string(
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
