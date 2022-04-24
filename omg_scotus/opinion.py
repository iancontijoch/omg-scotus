from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from enum import auto
from enum import Enum
from typing import Any

from omg_scotus.case import Case
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import remove_hyphenation
from omg_scotus.helpers import remove_notice
from omg_scotus.helpers import require_non_none
from omg_scotus.justice import extract_justice
from omg_scotus.justice import JusticeTag


class OpinionType(Enum):
    STATEMENT = auto()
    DISSENT = auto()
    CONCURRENCE = auto()
    STAY = auto()
    SYLLABUS = auto()
    PLURALITY = auto()
    MAJORITY = auto()


class Judgment(Enum):
    AFFIRMED = auto()
    REVERSED = auto()
    REMANDED = auto()
    DISMISSED_AS_IMPROVIDENTLY_GRANTED = auto()


class Opinion(ABC):
    text: str
    date: str
    case_name: str
    cases: list[Case]
    case_number: str
    petitioner: str
    respondent: str
    court_below: str | None
    author: JusticeTag
    joiners: list[JusticeTag] | None
    type: OpinionType
    _regex_patterns: dict[str, tuple[str, tuple[re._FlagsType, ...]]]

    def __init__(
        self, text: str, petitioner: str, respondent: str,
        lower_court: str, case_number: str,
    ) -> None:
        """Init Opinion"""
        self.text = text
        self.joiners = None
        self.petitioner, self.respondent = petitioner, respondent
        self.case_number = case_number
        self.court_below = lower_court
        # self.date = self.get_date()
        self.case_name = self.get_case_name()
        self.cases = [Case(number=self.case_number, name=self.case_name)]

        # self.court_below = self.get_court()
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

    def get_date(self) -> str:
        """Return date Opinion was decided."""
        pattern = r'^No\. +.*?Decided\s(.*?)$'
        match = require_non_none(
            re.compile(pattern, re.DOTALL | re.M)
            .search(self.text),
        )
        return match.groups()[0].strip()

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

    @staticmethod
    def get_type(text: str) -> OpinionType:
        """Return opinion type."""
        STATEMENT_PATTERN = r'writ of certiorari is denied\.\s+Statement'
        DISSENT_PATTERN = r'(?:dissent)\w+\b'
        CONCURRENCE_PATTERN = r'(?:concurr)\w+\b'
        SYLLABUS_PATTERN = r'Syllabus'
        PLURALITY_PATTERN = r'delivered\s+an\s+opinion'
        MAJORITY_PATTERN = r'delivered\s+the\s+opinion'
        PER_CURIAM_PATTERN = r'PER CURIAM'

        d = {
            STATEMENT_PATTERN: OpinionType.STATEMENT,
            DISSENT_PATTERN: OpinionType.DISSENT,
            CONCURRENCE_PATTERN: OpinionType.CONCURRENCE,
            SYLLABUS_PATTERN: OpinionType.SYLLABUS,
            PLURALITY_PATTERN: OpinionType.PLURALITY,
            MAJORITY_PATTERN: OpinionType.MAJORITY,
            PER_CURIAM_PATTERN: OpinionType.MAJORITY,
        }

        text = remove_hyphenation(text)  # remove artifacts
        for k, v in d.items():
            if bool(re.search(k, text)):
                return v
        raise NotImplementedError

    def __str__(self) -> str:
        retv = (
            f'\n{"-"*72}\nOPINION SUMMARY: {self.type}\n{"-"*72}'
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
            'date': (r'^No\. +.*?Decided\s(.*?)$', (re.M, re.DOTALL)),
        }
        super().__init__(text=text)  # type: ignore
        # self.type = self.get_type(text=text)

    def get_author(self) -> None:
        """Return opinion author."""
        # regex matches first occurrence of Justice Name/Chief Justice/Curiam
        pattern = (
            r'(?ms)(?:CHIEF\s+)*JUSTICE\s+[A-Z]+.+?[a-z]+\.|PER CURIAM'
        )
        first_sent = require_non_none(re.search(pattern, self.text)).group()
        author, *joiners = re.findall(r'\b(?!CHIEF|JUSTICE)[A-Z]+', first_sent)

        self.author = JusticeTag.from_string(remove_extra_whitespace(author))
        self.joiners = [
            JusticeTag.from_string(
                remove_extra_whitespace(j),
            )
            for j in joiners
        ]


class StayOpinion(Opinion):

    def __init__(self, text: str) -> None:
        """Init Opinion."""
        self._regex_patterns = {
            'parties': (
                r'(.*)\,\s+Applicant\s+v.\s+(.*$)', (re.M,),
            ),
            'court': (r'the\smandate\sof\sthe\s(.*?)\,\scase', (re.DOTALL,)),
        }
        super().__init__(text=text)  # type: ignore
        self.type = OpinionType.STAY

    def get_author(self) -> None:
        """Return opinion author."""
        self.author = extract_justice(self.text)


class Syllabus(Opinion):
    holding: str
    alignment_str: str

    # def __init__(self, text: str, petitioner: str, respondent:str,
    #              lower_court: str, case_number: str) -> None:
    #     super().__init__(text=remove_notice(text),
    #                      petitioner=petitioner,
    #                      respondent=respondent,
    #                      lower_court=lower_court,
    #                      case_number=case_number)
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.text = remove_notice(self.text)
        self.validate()
        self.type = OpinionType.SYLLABUS
        self.holding = self.get_holding()
        self.alignment_str = self.get_alignment_str()

    def validate(self) -> None:
        """Validate it's a syllabus."""
        _ = require_non_none(re.search('Syllabus', self.text))

    def get_holding(self) -> str:
        """Get syllabus holding."""
        pattern = r'Held:(.*?)Pp\.'
        return require_non_none(
            re.search(
                pattern,
                self.text,
                re.DOTALL | re.M,
            ),
        ).groups()[0]

    def get_alignment_str(self) -> str:
        """Return syllabus Justice alignment string.

        Search for a line starting with 3+ capital letters, followed
        by 'delivered' or 'announced' and grab through end of string.

        e.g. 'KAGAN, J. delivered the opinion of... in which ... joined.'
        """
        pattern = r'(?m)^\s*[A-Z]{3,}.+?(?=delivered|announced)[\W\w]+'
        return require_non_none(
            re.search(
                pattern,
                remove_notice(self.text),
            ),
        ).group()

    def get_author(self) -> None:
        """Return the author, joiners for the majority/plurality opinion."""
        text = self.get_alignment_str()
        # get everything through the first period that comes after a lowercase
        # excludes period after JJ or J or CJ
        first_sent = require_non_none(
            re.search(r'(?s).+?[a-z]\.', text),
        ).group()
        author, *joiners = re.findall(r'[A-Z]{3,}', first_sent)

        self.author = JusticeTag.from_string(remove_extra_whitespace(author))
        if joiners:
            self.joiners = [
                JusticeTag.from_string(
                    remove_extra_whitespace(j),
                )
                for j in joiners
            ]
        else:
            self.joiners = None


class SlipOpinion(Opinion):

    def get_opinion_type(self) -> OpinionType:
        """Return opinion type."""
        pass

    def get_author(self) -> None:
        """Return opinion author."""
        # regex matches first occurrence of Justice Name/Chief Justice/Curiam
        pattern = (
            r'(?ms)(?:CHIEF\s+)*JUSTICE\s+[A-Z]{3,}.+?[a-z]+\.|PER CURIAM'
        )
        first_sent = require_non_none(re.search(pattern, self.text)).group()
        if bool(re.search('PER CURIAM', first_sent)):
            author, joiners = 'PER CURIAM', ['PER CURIAM']
        else:
            author, *joiners = re.findall(
                r'\b(?!CHIEF|JUSTICE)[A-Z]{3,}',
                first_sent,
            )

        self.author = JusticeTag.from_string(remove_extra_whitespace(author))
        if joiners:
            self.joiners = [
                JusticeTag.from_string(
                    remove_extra_whitespace(j),
                )
                for j in joiners
            ]
        else:
            self.joiners = None

        self.type = Opinion.get_type(first_sent)
