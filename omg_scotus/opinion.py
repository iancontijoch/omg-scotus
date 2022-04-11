from __future__ import annotations

import re

import pdfplumber

from omg_scotus.helpers import require_non_none


class Opinion():
    opinion_pg_ix: int
    op_pages: list[pdfplumber.pdf.Page]
    case_name: str
    petitioner: str
    respondent: str
    court_below: str
    author: str
    joiners: list[str] | None
    text: str

    def __init__(self, opinion_text_raw: str) -> None:
        """Init Opinion."""
        self.opinion_txt_raw = opinion_text_raw
        self.petitioner, self.respondent = self.get_op_parties()
        self.case_name = self.get_case_name()
        self.court_below = self.get_op_court()
        self.author = self.get_opinion_author()
        self.court_below = self.get_op_court()
        self.text = self.get_opinion_text()

    def get_opinion_author(self) -> str:
        """Returns author for opinion"""
        author_line = self.opinion_txt_raw.splitlines()[2]
        if author_line.strip() == 'Per Curiam':
            return 'Per Curiam'
        else:
            return (
                self.opinion_txt_raw
                .splitlines()[2]
                .split()[2]
                .replace(',', '')
            )

    def get_op_parties(self) -> tuple[str, str]:
        pattern = (
            'SUPREME COURT OF THE UNITED STATES '
            + '\n(.*) v. (.*)ON PETITION'
        )

        petitioner, respondent = require_non_none(
            re.compile(pattern, re.DOTALL).search(
                self.opinion_txt_raw,
            ),
        ).groups()

        petitioner = petitioner.replace('\n', '').replace('  ', ' ').strip()
        respondent = respondent.replace('\n', '').replace('  ', ' ').strip()

        return petitioner, respondent

    def get_op_court(self) -> str:
        pattern = '\nON.*TO THE (.*)No.'
        match = require_non_none(
            re.compile(pattern, re.DOTALL)
            .search(self.opinion_txt_raw),
        )
        return (
            match.groups()[0]
            .replace('\n', '')
            .replace('  ', ' ')
        ).strip()

    def get_case_name(self) -> str:
        """Print {petitioner} v. {respondent} case format."""
        return ' v. '.join([self.petitioner, self.respondent])

    def get_opinion_text(self) -> str:
        """Return cleaned opinion text."""
        # TODO: Implement remove opinion headed
        # for each page using text
        return self.clean_opinion_text(self.opinion_txt_raw)

    def clean_opinion_text(self, text: str) -> str:
        """Clean up text"""
        #  remove newline whitespace
        text = re.sub(r'(\n* *\n)(\w+)', ' \\2', text)
        #  join hyphenated spillovers
        text = re.sub(r'(\w)(- )(\w)', '\\1\\3', text)
        #  remove extra spaces between punctuation.
        text = re.sub(r'([\.\,])  ', '\\1 ', text)
        #  remove newlines after header removal
        text = re.sub(r'( \n )(\w)', ' \2', text)
        #  remove hyphenated spillovers after header removal
        text = re.sub(r'(\w)-\n ', '\\1', text)
        #  remove newline when not followed by whitespace
        text = re.sub(r'  \n(\S)', ' \\1', text)

        return text
