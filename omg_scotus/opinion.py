from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from enum import auto
from enum import Enum
from typing import Any

from omg_scotus.case import Case
from omg_scotus.helpers import get_justices_from_sent
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
    recusals: list[JusticeTag] | None
    type: OpinionType
    _regex_patterns: dict[str, str]

    def __init__(
        self, text: str, petitioner: str, respondent: str,
        lower_court: str, case_number: str,
    ) -> None:
        """Init Opinion"""
        self.text = text
        self.joiners = None
        self.recusals = None
        self.petitioner, self.respondent = petitioner, respondent
        self.case_number = case_number
        self.court_below = lower_court
        self.case_name = self.get_case_name()
        self.cases = [Case(number=self.case_number, name=self.case_name)]
        self.get_author()

    @abstractmethod
    def get_author(self) -> None: pass

    def get_case_name(self) -> str:
        """Return {petitioner} v. {respondent} case format."""
        return ' v. '.join([self.petitioner, self.respondent])

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
        if self.recusals:
            retv += f'\nRecused:  {self.recusals}'
        retv += (
            f'\nType:  {self.type}'
            f'\nCase:  {self.case_name}'
            f'\nNo.:  {self.case_number}\n'
        )
        if self.court_below:
            retv += f'From:  {self.court_below}\n'
        return retv


class OrderOpinion(Opinion):
    noted_dissents: list[JusticeTag] | None

    def __init__(
        self, text: str, petitioner: str, respondent: str,
        lower_court: str, case_number: str,
    ) -> None:
        super().__init__(
            text, petitioner, respondent, lower_court,
            case_number,
        )
        self.type = Opinion.get_type(self.text)
        self.noted_dissents = None

    def get_author(self) -> None:
        """Return opinion author."""
        # matches justices that would deny/grant order
        noted_dissent_sent = re.search(
            r'[^?!.]+(JUSTICE).+?would\s(?:grant|deny)[^?!.]+', self.text,
        )
        # matches justices signing on to statements
        statement_sent = re.search(
            r'[^.?!]+Statement.+?(?=JUSTICE)[^.?!]+', self.text,
        )
        # matches justices dissenting/concurring from order
        dissent_concurr_sent = re.search(
            r'[^.?!]+(?=JUSTICE).+?(?=dissent|concurr)[^.?!]+', self.text,
        )

        if noted_dissent_sent:
            self.noted_dissents = get_justices_from_sent(
                noted_dissent_sent.group(),
            )

        if dissent_concurr_sent:
            author, *joiners = get_justices_from_sent(
                dissent_concurr_sent.group(),
            )
        elif statement_sent:
            author, *joiners = get_justices_from_sent(statement_sent.group())
        self.author = author
        self.joiners = joiners
        self.type = Opinion.get_type(self.text)


class StayOpinion(Opinion):

    def __init__(self, text: str) -> None:
        """Init Opinion."""
        self._regex_patterns = {
            'parties': r'(?m)(.*)\,\s+Applicant\s+v.\s+(.*$)',
            'court': r'(?s)the\smandate\sof\sthe\s(.*?)\,\scase',
            'case_num': r'\bNo.\s+([A-Z\d]+)',
        }
        self.text = text
        petitioner, respondent = self.get_attr('parties', text)
        court_below = self.get_attr('court', text)[0]
        case_number = self.get_attr('case_num', text)[0]

        super().__init__(
            text=text, petitioner=petitioner,
            respondent=respondent, lower_court=court_below,
            case_number=case_number,
        )
        self.type = OpinionType.STAY

    def get_attr(self, attr: str, text: str) -> tuple[str, ...]:
        """Get attributes from Stay Order."""
        matches = (
            require_non_none(
                re.search(
                    self._regex_patterns[attr],
                    text,
                ),
            ).groups()
        )

        return tuple(
            map(
                lambda x: str(
                    x.replace('\n', '')
                    .replace('  ', ' ')
                    .strip(),
                ), matches,
            ),
        )

    def get_author(self) -> None:
        """Return opinion author."""
        self.author = extract_justice(self.text)


class Syllabus(Opinion):
    holding: str
    alignment_str: str

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
        # author, *joiners = re.findall(r'[A-Z]{3,}', first_sent)

        recusal_sent = re.search(
            r'[^.?!]+\b[A-Z]{3,}.+took\s+no\s+part[^.?!]+',
            text,
        )
        if recusal_sent:
            self.recusals = get_justices_from_sent(recusal_sent.group())

        author, *joiners = get_justices_from_sent(first_sent)
        self.author = author
        if joiners:
            self.joiners = joiners
        elif bool(re.search('unanimous', first_sent)):
            self.joiners = [
                j for j in JusticeTag
                if j not in (
                    self.author,
                    JusticeTag.PER_CURIAM,
                )
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
