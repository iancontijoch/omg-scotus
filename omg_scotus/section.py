from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from enum import Enum

from omg_scotus.case import Case
from omg_scotus.helpers import remove_extra_whitespace


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
        self.get_cases()

    @abstractmethod
    def get_cases(self) -> None:
        pass


class OrderSection(Section):

    def get_cases(self) -> None:
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

    def __str__(self) -> str:
        """Print all cases in Section."""
        cases_text = 'No cases.'
        num_cases = 0
        if len(self.cases) > 0:
            num_cases = len(self.cases)
            cases_text = '\n'.join(
                ['  '.join([c.number, c.name]).strip() for c in self.cases],
            )
        return (
            f'\n{"-"*72}'
            f'\n{self.label}: {num_cases} case'
            f'{(num_cases > 1 or num_cases == 0)*"s"}'
            f'\n{"-"*72}\n{cases_text}\n{"-"*72}\n'
        )
