from __future__ import annotations

import json
import re
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from enum import auto
from enum import Enum
from json import JSONDecodeError
from typing import Any

import bs4
import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup
from spacy import Language

from omg_scotus.helpers import create_docket_number
from omg_scotus.helpers import get_term_year
from omg_scotus.helpers import read_pdf
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import require_non_none
from omg_scotus.helpers import suffix_base_url


class Stream(Enum):
    ORDERS = auto()
    SLIP_OPINIONS = auto()
    OPINIONS_RELATING_TO_ORDERS = auto()
    DEBUG = auto()


class FetcherStrategy(ABC):
    """Strategy to be used by Fetcher class."""
    stream: Stream
    most_recent: bool
    date: str | None
    term_year: str | None
    url: str | None
    base_url: str
    soup: bs4.BeautifulSoup

    def __init__(
        self,
        stream: Stream,
        date: str | None,
        most_recent: bool = False,
        term_year: str | None = None,
        url: str | None = None,

    ) -> None:
        self.stream = stream
        self.most_recent = most_recent
        self.url = url
        self.term_year = term_year
        self.date = date
        self.base_url = self.set_base_url()
        self.soup = self.get_soup()

    def set_base_url(self) -> str:
        """Set base URL from which to find Opinion."""
        if self.stream is Stream.ORDERS:
            href = 'https://www.supremecourt.gov/orders/ordersofthecourt/'
        elif self.stream is Stream.OPINIONS_RELATING_TO_ORDERS:
            href = 'https://www.supremecourt.gov/opinions/relatingtoorders/'
        elif self.stream is Stream.SLIP_OPINIONS:
            href = 'https://www.supremecourt.gov/opinions/slipopinion/'
        else:
            raise NotImplementedError
        return f'{href}{self.get_term_for_url()}'

    def get_term_for_url(self) -> str:
        """Get URL with Term Year suffix."""
        if self.term_year:
            term_year = self.term_year
        elif not self.url:
            # We are grabbing most recent date, so get today's Term.
            term_year = get_term_year(datetime.today().date())
        elif self.url.split('/')[-1].startswith('fr'):
            # frbk22 -> 22 - 1
            term_year = str(int(self.url.split('/')[-1][4:6]) - 1)
        elif self.url.split('/')[-3] == 'opinions':
            term_year = self.url.split('/')[-2][:2]
        elif self.url.split('/')[-3] == 'orders':
            url_date = self.url.split('/')[-1][:6]
            term_year = get_term_year(
                datetime.strptime(url_date, '%m%d%y').date(),
            )
        else:
            raise NotImplementedError
        return term_year

    def get_soup(self) -> bs4.BeautifulSoup:
        """Get BeautifulSoup object."""
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0)'
                'Gecko/20100101 Firefox/50.0'
            ),
        }
        payload = requests.get(self.base_url, headers=headers)
        return BeautifulSoup(payload.text, 'html.parser')

    @abstractmethod
    def get_contents(self) -> BeautifulSoup.contents: pass

    @abstractmethod
    def get_payload(self) -> list[dict[str, str | pdfplumber.pdf.PDF]]:
        pass


class OrdersFetcherStrategy(FetcherStrategy):

    def get_contents(self) -> BeautifulSoup.contents:
        if self.url:
            match: BeautifulSoup.contents = require_non_none(
                self.soup.find_all(
                    attrs={
                        'href': require_non_none(self.url).replace(
                            'https://www.supremecourt.gov',
                            '',
                        ),
                    },
                ),
            )
        else:
            match = self.soup.find_all(
                'div', class_='column2',
            )[0].contents[1].find_all('span')
        return match

    def get_payload(self) -> list[dict[str, str | pdfplumber.pdf.PDF]]:
        match = self.get_contents()

        if self.url:
            date: str = require_non_none(
                match[0].parent.parent.contents[1].text.strip(),
            )
            title = match[0].text
            url = require_non_none(self.url)

        else:
            date = match[0].text.strip()
            title = match[1].text.strip()
            url = (
                f'https://www.supremecourt.gov/'
                f"{match[1].contents[0]['href']}"
            )

        retv = {
            'date': datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d'),
            'title': title,
            'url': url,
            'pdf': read_pdf(url),
        }
        return [retv]

    def get_url_for_term(self) -> None:
        """Get URL with Term Year suffix."""
        if not self.url:
            # Grabbing most recent date, so get today's Term.
            self.base_url += get_term_year(datetime.today().date())
        else:
            self.base_url = suffix_base_url(
                self.base_url, self.url,
            )


class OpinionsFetcherStrategy(FetcherStrategy):

    def get_disposition(self, docket_json: Any, date: str) -> str | None:
        if self.stream is Stream.SLIP_OPINIONS:
            disposition_text = [
                entry['Text']
                for entry in docket_json['ProceedingsandOrder']
                if bool(
                    re.search(
                        r'AFFIRMED|DISMISSED|REMANDED|REVERSED|VACATED',
                        entry['Text'],
                    ),
                ) and (
                    datetime.strptime(
                        entry['Date'], '%b %d %Y',
                    ) == datetime.strptime(
                        date,
                        '%m/%d/%y',
                    )
                )
            ]
            if len(disposition_text) > 1:
                raise ValueError(
                    'Multiple matches for disposition entries.',
                )
            elif len(disposition_text) == 0:  # applications for stays
                retv = (
                    docket_json['ProceedingsandOrder'][-1]['Text']
                )
            else:
                retv = disposition_text[0]
        else:
            retv = None

        return retv

    def get_contents(self) -> pd.DataFrame:

        tbls = self.soup.find_all('table', class_='table table-bordered')
        dfs = pd.read_html(str(tbls))
        for i, df in enumerate(dfs):
            links = [row.find_all('a') for row in tbls[i].find_all('tr')]
            # get last link in row (i.e. the Revised opinion if it exists)
            hrefs = [
                f'https://www.supremecourt.gov{link[-1].get("href")}'
                for link in links if len(link) > 0
            ]
            df['url'] = hrefs
            # get holding from first link (NOT revised opinion)
            if self.stream is Stream.SLIP_OPINIONS:
                # Opinions relating to orders do not have holdings
                holdings = [
                    link[0].get('title') for link in links if len(link) > 0
                ]
                df['holding'] = holdings

        return pd.concat(dfs).reset_index()

    def get_payload(self) -> list[dict[str, str | pdfplumber.pdf.PDF]]:
        retv = []
        table = self.get_contents()

        if self.url:
            selected_rows = table[table['url'] == self.url]
        elif self.term_year:
            selected_rows = table
        elif self.date:
            selected_rows = table[table['Date'] == self.date]
        else:
            selected_rows = table.head(1)
        for _, row in selected_rows.iterrows():
            date = row['Date'].strip()
            docket_number = row['Docket'].strip()
            author_initials = row['J.'].strip()
            title = row['Name'].strip()
            if 'holding' in table.columns:
                holding = row['holding'].strip()
            else:
                holding = None
            url = row['url'].strip()

            try:
                docket_json = self.get_docket_json(
                    create_docket_number(
                        re.sub(
                            r'\s\(.+\)',
                            '',
                            docket_number,
                        ),
                    ),
                )
                petitioner = docket_json['PetitionerTitle']
                respondent = docket_json['RespondentTitle']
                lower_court = docket_json['LowerCourt']
                case_number = docket_json['CaseNumber']
                disposition_text = self.get_disposition(docket_json, date)
            except JSONDecodeError:
                value = 'No JSON case data. Case too old.'
                petitioner = value
                respondent = value
                lower_court = value
                case_number = value
                disposition_text = value
            finally:
                d = {
                    'date': (
                        datetime.strptime(date, '%m/%d/%y').strftime(
                            '%Y-%m-%d',
                        )
                    ),
                    'title': title,
                    'petitioner': petitioner,
                    'respondent': respondent,
                    'lower_court': lower_court,
                    'case_number': remove_extra_whitespace(case_number),
                    'holding': holding,
                    'disposition_text': disposition_text,
                    'is_per_curiam': author_initials == 'PC',
                    'url': url,
                    'pdf': read_pdf(url),
                }
                retv.append(d)
        return retv

    @staticmethod
    def get_docket_json(docket_number: str) -> dict[str, Any]:
        """Return case JSON from SCOTUS online docket."""
        url = (
            f'https://www.supremecourt.gov/rss/cases/json/{docket_number}.json'
        )
        return json.loads(requests.get(url).text)


class Fetcher:
    stream: Stream
    strategy: type[FetcherStrategy]
    payload: str
    url: str | None
    term_year: str | None
    date: str | None
    most_recent: bool
    nlp: Language

    def __init__(
        self, stream: Stream, date: str | None = None,
        url: str | None = None, term_year: str | None = None,
        most_recent: bool = False,
    ) -> None:
        self.stream = stream
        self.url = url
        self.term_year = term_year
        self.date = date
        self.most_recent = most_recent
        self.set_strategy()

    @classmethod
    def from_url(cls, url: str, stream: Stream) -> Fetcher:
        return cls(stream=stream, url=url)

    def get_payload(
        self,
    ) -> list[dict[str, Stream | str | pdfplumber.pdf.PDF]]:
        fs = self.strategy(
            stream=self.stream,
            most_recent=self.most_recent,
            url=self.url,
            term_year=self.term_year,
            date=self.date,
        )
        retv = fs.get_payload()
        for d in retv:
            d['stream'] = self.stream
        return retv

    def set_strategy(self) -> None:
        if self.stream is Stream.ORDERS:
            self.strategy = OrdersFetcherStrategy
        elif self.stream in (
            Stream.SLIP_OPINIONS,
            Stream.OPINIONS_RELATING_TO_ORDERS,
        ):
            self.strategy = OpinionsFetcherStrategy
        else:
            raise NotImplementedError

#     def detect_changes(self) -> str:
#         """TODO: Implement"""
#         # to check for changes to order section
#         div_orders = self.soup.find_all('div', class_='column2')[
#             0
#         ]  # there is one for "More" orders
#         hash = hashlib.sha256(div_orders.text.encode('utf-8')).hexdigest()
#         return hash
