from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from enum import auto
from enum import Enum

from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import remove_hyphenation
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
    court_below: str | None
    author: JusticeTag
    joiners: list[JusticeTag] | None
    type: OpinionType
    _regex_patterns: dict[str, tuple[str, tuple[re._FlagsType]]]

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

    def get_parties(self) -> tuple[str, ...]:
        """Get parties to case."""
        # TODO: Abstract get_parties and get_court into get_regex method.
        flag = 0
        pattern, flags = require_non_none(self._regex_patterns['parties'])
        if flags:
            for f in flags:
                flag |= f
        matches = (
            require_non_none(
                re.compile(pattern, flag)
                .search(self.text),
            ).groups()
        )
        # petitioner, respondent
        return tuple(
            map(
                lambda x: str(
                    x.replace('\n', '')
                    .replace('  ', ' ')
                    .strip(),
                ), matches,
            ),
        )

    def get_case_name(self) -> str:
        """Return {petitioner} v. {respondent} case format."""
        return ' v. '.join([self.petitioner, self.respondent])

    def get_case_number(self) -> str:
        """Return case number."""
        pattern = r'^No. +(.*?)\.'
        match = require_non_none(
            re.compile(pattern, re.DOTALL | re.M)
            .search(self.text),
        )
        return match.groups()[0].strip()

    def get_court(self) -> str | None:
        """Get court below."""
        flag = 0
        pattern, flags = require_non_none(self._regex_patterns['court'])
        if flags:
            for f in flags:
                flag |= f
        match = re.compile(pattern, flag).search(self.text)
        if match:
            return (
                match.groups()[0]
                .replace('\n', '')
                .replace('  ', ' ')
            ).strip()
        else:
            return None

    def prepare_text(self) -> str:
        """Remove extra spaces, newlines, overflow hyphens from text."""
        text = self.text
        # Step 1 - remove overflow hyphens:
        text = remove_hyphenation(text)
        return text

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
        if self.court_below:
            retv += f'From:  {self.court_below}\n'
        return retv


class OrderOpinion(Opinion):

    def __init__(self, text: str) -> None:
        """Init Opinion."""
        self._regex_patterns = {
            'parties': (
                r'SUPREME COURT OF THE UNITED STATES '
                r'\n(.*) v. (.*)ON PETITION', (re.DOTALL,),
            ),
            'court': (r'\nON.*TO THE (.*?)No.', (re.DOTALL,)),
        }
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

    def get_type(self) -> OpinionType:
        """Return opinion type."""
        STATEMENT_PATTERN = r'writ of certiorari is denied\.\s+Statement'
        DISSENT_PATTERN = r'dissenting from the denial [\w\s\-]+'
        CONCURRENCE_PATTERN = r'concurring'
        text = self.prepare_text()  # remove artifacts that hinder analysis
        if bool(re.search(STATEMENT_PATTERN, text)):
            return OpinionType.STATEMENT
        elif bool(re.search(DISSENT_PATTERN, text)):
            return OpinionType.DISSENT
        elif bool(re.search(CONCURRENCE_PATTERN, text)):
            return OpinionType.CONCURRENCE
        else:
            raise NotImplementedError


class StayOpinion(Opinion):

    def __init__(self, text: str) -> None:
        """Init Opinion."""
        self._regex_patterns = {
            'parties': (
                r'(.*)\,\s+Applicant\s+v.\s+(.*$)', (re.M,),
            ),
            'court': (r'the\smandate\sof\sthe\s(.*?)\,\scase', (re.DOTALL,)),
        }
        super().__init__(text=text)
        self.type = OpinionType.STAY

    def get_author(self) -> None:
        """Return opinion author."""
        self.author = extract_justice(self.text)
