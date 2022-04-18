from __future__ import annotations

import re

from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.opinion import Opinion
from omg_scotus.opinion import OrderOpinion
from omg_scotus.order_list_section import OrderListSection
from omg_scotus.order_list_section import OrderListSectionType


class OrderList:
    text: str
    sections: list[OrderListSection]
    opinions: list[Opinion]

    def __init__(self, orders_text: str, opinions_text: str | None):
        self.orders_text = orders_text
        self.opinions_text = opinions_text
        self.title = self.get_title()
        self.date = self.get_date()
        self.sections, self.opinions = [], []
        self.get_sections()
        self.get_opinions()

    def get_title(self) -> str:
        return self.orders_text.splitlines()[1]

    def get_date(self) -> str:
        return self.orders_text.splitlines()[4]

    def __str__(self) -> str:
        """Return string representation of OrderList."""
        s = '\n\n--------ORDER LIST SUMMARY--------'
        s += f'\n{self.title}\n{self.date}'
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
            string=self.orders_text, flags=re.DOTALL,
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

    def get_opinions(self) -> None:
        """Create and append opinions embedded in OrderList."""
        # regex pattern looks for text between
        # SUPREME COURT OF THE UNITED STATES
        if not self.opinions_text:
            return None

        pattern = (
            r'(SUPREME COURT OF THE UNITED STATES\s\s)(.*?(?=SUPREME COURT '
            r'OF THE UNITED STATES\s\s)|.*$)'
        )
        matches = re.finditer(
            pattern=pattern,
            string=self.opinions_text,
            flags=re.DOTALL,
        )

        for m in matches:
            opinion_text = self.opinions_text[m.span()[0]: m.span()[1]]
            self.opinions.append(OrderOpinion(text=opinion_text))
