from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from enum import Enum

from omg_scotus.case import Case
from omg_scotus.helpers import remove_extra_whitespace
# from omg_scotus._enums import OrderSectionType


class Section(ABC):
    type: Enum
    label: str
    text: str
    cases: list[Case]

    def __init__(self, label: str, type: Enum, text: str):
        self.label = label
        self.type = type
        self.text = text
        self.cases = []
        self.set_cases()

    @abstractmethod
    def set_cases(self) -> None:
        pass

    @abstractmethod
    def compose_tweet(self) -> str:
        pass


class OrderSection(Section):

    def set_cases(self) -> None:
        """Get all cases in Section."""
        pattern = r'(\d+.*?\d|\d+.*?ORIG\.)\s+(.*?V.*?$|IN\s+RE.*?$)'
        matches = re.findall(pattern=pattern, string=self.text, flags=re.M)

        self.cases = [
            Case(
                number=m[0],
                name=remove_extra_whitespace(m[1]),
            )
            for m in matches
        ]

    def get_cases_text(self) -> tuple[int, list[str]]:
        """Get number of cases and case listing."""
        cases_text = ['No cases.']
        num_cases = 0
        if len(self.cases) > 0:
            num_cases = len(self.cases)
            cases_text = [
                '  '.join([c.number, c.name]).strip()
                for c in self.cases
            ]

        return num_cases, cases_text

    def compose_tweet(self) -> str:
        """Return tweetable summary."""
        num_cases, cases_text = self.get_cases_text()
        # cases_text = '  *  ' + '\n  *  '.join(cases_text)
        s = (
            f'\n{self.label}: {num_cases} case'
            f'{(num_cases > 1 or num_cases == 0)*"s"}'
        )
        # if self.type is OrderSectionType.CERTIORARI_GRANTED:
        #     s += f'\n{cases_text}'
        return s

    def __str__(self) -> str:
        """Print all cases in Section."""
        num_cases, cases_text = self.get_cases_text()
        cases_string = '\n'.join(cases_text)
        return (
            f'\n{"-"*72}'
            f'\n{self.label}: {num_cases} case'
            f'{(num_cases > 1 or num_cases == 0)*"s"}'
            f'\n{"-"*72}\n{cases_string}\n{"-"*72}\n'
        )
