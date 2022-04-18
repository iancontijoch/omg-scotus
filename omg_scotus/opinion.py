from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from enum import auto
from enum import Enum

from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import require_non_none
from omg_scotus.justice import extract_justice
from omg_scotus.justice import JusticeTag


class OpinionType(Enum):
    STATEMENT = auto()
    DISSENT = auto()
    CONCURRENCE = auto()
    STAY = auto()


class Opinion(ABC):
    text: str
    case_name: str
    case_number: str
    petitioner: str
    respondent: str
    court_below: str
    author: JusticeTag
    joiners: list[JusticeTag] | None
    type: OpinionType

    def __init__(self, text: str) -> None:
        """Init Opinion"""
        self.text = text
        self.joiners = None
        self.petitioner, self.respondent = self.get_parties()
        self.case_name = self.get_case_name()
        self.case_number = self.get_case_number()
        self.court_below = self.get_court()
        self.get_author()

    @abstractmethod
    def get_author(self) -> None: pass

    @abstractmethod
    def get_parties(self) -> tuple[str, str]: pass

    @abstractmethod
    def get_court(self) -> str: pass

    def get_case_name(self) -> str:
        """Return {petitioner} v. {respondent} case format."""
        return ' v. '.join([self.petitioner, self.respondent])

    def get_case_number(self) -> str:
        """Return case number."""
        pattern = r'No. +(.*?)\.'
        match = require_non_none(
            re.compile(pattern, re.DOTALL)
            .search(self.text),
        )
        return match.groups()[0].strip()

    def __str__(self) -> str:
        retv = (
            f'{"-"*72}\nOPINION SUMMARY\n{"-"*72}'
            f'\nAuthor:  {self.author}'
        )
        if self.joiners:
            retv += f'\nJoined by:  {self.joiners}'
        retv += (
            f'\nType:  {self.type}'
            f'\nCase:  {self.case_name}'
            f'\nNo.:  {self.case_number}\n'
        )
        return retv


class OrderOpinion(Opinion):

    def __init__(self, text: str) -> None:
        """Init Opinion."""
        super().__init__(text=text)
        self.type = self.get_type()

    def get_author(self) -> None:
        """Return opinion author."""
        # regex matches first occurrence of Justice Name/Chief Justice/Curiam
        pattern = (
            r'JUSTICE\s+\w+|CHIEF JUSTICE|PER CURIAM'
        )
        match = re.compile(pattern).findall(self.text)
        self.author = JusticeTag.from_string(remove_extra_whitespace(match[0]))
        self.joiners = [
            JusticeTag.from_string(
                remove_extra_whitespace(
                    m,
                ),
            ) for m in match[1:]
        ] if len(match) > 1 else None

    def get_parties(self) -> tuple[str, str]:
        """Get parties to case."""
        pattern = (
            r'SUPREME COURT OF THE UNITED STATES '
            r'\n(.*) v. (.*)ON PETITION'
        )

        petitioner, respondent = require_non_none(
            re.compile(pattern, re.DOTALL).search(
                self.text,
            ),
        ).groups()

        petitioner = petitioner.replace('\n', '').replace('  ', ' ').strip()
        respondent = respondent.replace('\n', '').replace('  ', ' ').strip()

        return petitioner, respondent

    def get_court(self) -> str:
        """Get court below."""
        pattern = r'\nON.*TO THE (.*?)No.'
        match = require_non_none(
            re.compile(pattern, re.DOTALL)
            .search(self.text),
        )
        return (
            match.groups()[0]
            .replace('\n', '')
            .replace('  ', ' ')
        ).strip()

    def get_type(self) -> OpinionType:
        """Return opinion type."""
        STATEMENT_PATTERN = r'writ of certiorari is denied\.\s+Statement'
        DISSENT_PATTERN = r'dissenting from the denial [\w\s\-]+'
        CONCURRENCE_PATTERN = r'concurring'
        if bool(re.search(STATEMENT_PATTERN, self.text)):
            return OpinionType.STATEMENT
        elif bool(re.search(DISSENT_PATTERN, self.text)):
            return OpinionType.DISSENT
        elif bool(re.search(CONCURRENCE_PATTERN, self.text)):
            return OpinionType.CONCURRENCE
        else:
            raise NotImplementedError

        # TODO:
        # Guard against following scenario (w/ hyphens)
        #  JUSTICE SOTOMAYOR, dissenting from the denial of certi-
        #  orari.


class StayOpinion(Opinion):

    def __init__(self, text: str) -> None:
        """Init Opinion."""
        super().__init__(text=text)
        self.type = OpinionType.STAY

    def get_author(self) -> None:
        """Return opinion author."""
        self.author = extract_justice(self.text)

    def get_parties(self) -> tuple[str, str]:
        """Get parties to case."""
        pattern = (
            r'(.*)\,\s+Applicant\s+v.\s+(.*$)'
        )

        petitioner, respondent = require_non_none(
            re.compile(pattern, re.M).search(
                self.text,
            ),
        ).groups()

        petitioner = petitioner.replace('\n', '').replace('  ', ' ').strip()
        respondent = respondent.replace('\n', '').replace('  ', ' ').strip()

        return petitioner, respondent

    def get_court(self) -> str:
        """Get court below."""
        return 'Dummy Court'
