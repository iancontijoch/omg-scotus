from __future__ import annotations

import re
from abc import ABC

import pdfplumber

from omg_scotus.helpers import remove_extra_whitespace


class Order(ABC):
    date: str
    text: str
    order_title: str
    url: str

    def __init__(
        self,
        date: str,
        order_title: str,
        text: str,
        url: str,
    ) -> None:
        self.date = date
        self.order_title = order_title
        self.url = url
        self.text = text


class Rule():
    number: str
    title: str
    contents: str

    def __init__(self, number: str, title: str) -> None:
        self.number = number
        self.title = title


class RulesOrder(Order):
    rules: list[Rule]

    def __init__(
        self,
        date: str,
        order_title: str,
        text: str,
        url: str,
        pdf: pdfplumber.pdf.PDF,
    ) -> None:
        super().__init__(date, order_title, text, url)
        self.pdf = pdf
        self.rules = []
        self.get_rules()

    def get_bolded_text(self) -> str:
        """Get bolded text to find Rule # and Titles."""
        return ''.join(
            [
                c['text'] for p in self.pdf.pages[3:]
                for c in p.chars
                if c['fontname'] == 'TimesNewRomanPS-BoldMT'
            ],
        )

    def get_rules(self) -> None:
        """Create Rule from rule, title in bolded text."""
        pattern = r'Rule\s+([\d\.]+\.)(.+?)(?=Rule|$)'
        for m in re.finditer(pattern, self.get_bolded_text()):
            number, title = m.groups()
            title = remove_extra_whitespace(title)
            title = re.sub(r'\s\*', '', title)  # elim asterisks
            rule = Rule(number=number, title=title)
            self.rules.append(rule)
        self.set_rule_content()

    def set_rule_content(self) -> None:
        """Set text of rule."""
        pattern = r'(?ms)^Rule\s+[\d\.]+\.(.+?)(?=^Rule|\Z)'
        for i, m in enumerate(re.finditer(pattern, self.text)):
            self.rules[i].contents = m.group()
