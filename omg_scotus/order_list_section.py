from __future__ import annotations

import re

from omg_scotus._enums import OrderListSectionType
from omg_scotus.case import Case


class OrderListSection:
    type: OrderListSectionType
    label: str
    text: str
    cases: list[Case]

    def __init__(self, label: str, type: OrderListSectionType, text: str):
        self.label = label
        self.type = type
        self.text = text
        self.cases = []
        self.get_cases()

    def get_cases(self) -> None:
        pattern = r'(\d+.*?\d|\d+.*?ORIG.)\s+(.*?V.*?$|IN RE.*?$)'
        matches = re.findall(pattern=pattern, string=self.text, flags=re.M)

        self.cases = [Case(number=m[0], name=m[1]) for m in matches]

    def __str__(self) -> str:
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
