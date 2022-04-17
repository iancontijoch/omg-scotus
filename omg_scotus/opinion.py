from __future__ import annotations

import re

from omg_scotus._enums import Justice
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import require_non_none


class Opinion():
    opinion_text: str
    case_name: str
    case_number: str
    petitioner: str
    respondent: str
    court_below: str
    author: Justice
    joiners: list[Justice] | None
    text: str

    def __init__(self, opinion_text: str) -> None:
        """Init Opinion."""
        self.opinion_text = opinion_text
        self.petitioner, self.respondent = self.get_parties()
        self.case_name = self.get_case_name()
        self.case_number = self.get_case_number()
        self.court_below = self.get_court()
        self.get_opinion_author()

    def get_opinion_author(self) -> None:
        """Return opinion author."""
        # regex matches first occurrence of Justice Name/Chief Justice/Curiam
        pattern = (
            r'JUSTICE\s+\w+|CHIEF JUSTICE|PER CURIAM'
        )
        match = re.compile(pattern).findall(self.opinion_text)
        self.author = Justice.from_string(remove_extra_whitespace(match[0]))
        self.joiners = [
            Justice.from_string(
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
                self.opinion_text,
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
            .search(self.opinion_text),
        )
        return (
            match.groups()[0]
            .replace('\n', '')
            .replace('  ', ' ')
        ).strip()

    def get_case_name(self) -> str:
        """Return {petitioner} v. {respondent} case format."""
        return ' v. '.join([self.petitioner, self.respondent])

    def get_case_number(self) -> str:
        """Return case number."""
        pattern = r'No. +(.*?)\.'
        match = require_non_none(
            re.compile(pattern, re.DOTALL)
            .search(self.opinion_text),
        )
        return match.groups()[0].strip()
