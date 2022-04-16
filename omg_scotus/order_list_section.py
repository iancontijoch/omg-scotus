from __future__ import annotations

import re
from enum import auto
from enum import Enum

from omg_scotus.case import Case


class OrderListSectionType(Enum):
    CERTIORARI_SUMMARY_DISPOSITIONS = auto()
    ORDERS_IN_PENDING_CASES = auto()
    CERTIORARI_GRANTED = auto()
    CERTIORARI_DENIED = auto()
    HABEAS_CORPUS_DENIED = auto()
    MANDAMUS_DENIED = auto()
    REHEARINGS_DENIED = auto()

    @staticmethod
    def from_string(label: str) -> OrderListSectionType:
        if label in (
            'CERTIORARI -- SUMMARY DISPOSITIONS',
            'CERTIORARI -- SUMMARY DISPOSITION',
        ):
            return OrderListSectionType.CERTIORARI_SUMMARY_DISPOSITIONS
        elif label in ('ORDERS IN PENDING CASES', 'ORDER IN PENDING CASE'):
            return OrderListSectionType.ORDERS_IN_PENDING_CASES
        elif label == 'CERTIORARI GRANTED':
            return OrderListSectionType.CERTIORARI_GRANTED
        elif label == 'CERTIORARI DENIED':
            return OrderListSectionType.CERTIORARI_DENIED
        elif label == 'HABEAS CORPUS DENIED':
            return OrderListSectionType.HABEAS_CORPUS_DENIED
        elif label == 'MANDAMUS DENIED':
            return OrderListSectionType.MANDAMUS_DENIED
        elif label in ('REHEARINGS DENIED', 'REHEARING DENIED'):
            return OrderListSectionType.REHEARINGS_DENIED
        else:
            raise NotImplementedError


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


class OrderList:
    text: str
    sections: list[OrderListSection]

    def __init__(self, text: str):
        self.text = text
        self.title = self.get_title()
        self.date = self.get_date()
        self.sections = []
        self.set_sections()

    def get_title(self) -> str:
        return self.text.splitlines()[1]

    def get_date(self) -> str:
        return self.text.splitlines()[4]

    def __str__(self) -> str:
        """Return string representation of OrderList."""
        s = '\n\n--------ORDER LIST SUMMARY--------'
        s += f'\n{self.title}\n{self.date}'
        s += '\n'.join([str(s) for s in self.sections])
        return s

    def set_sections(self) -> None:
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
            section_title, section_content = ' '.join(
                m.groups()[0].split(),
            ), m.groups()[1]  # remove whitespace noise

            section = OrderListSection(
                label=section_title,
                type=OrderListSectionType.from_string(
                    section_title,
                ),
                text=section_content,
            )
            self.sections.append(section)
