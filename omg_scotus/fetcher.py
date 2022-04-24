from __future__ import annotations

import json
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from enum import auto
from enum import Enum
from typing import Any

import bs4
import pdfplumber
import requests
from bs4 import BeautifulSoup

from omg_scotus.helpers import create_docket_number
from omg_scotus.helpers import get_term_year
from omg_scotus.helpers import read_pdf
from omg_scotus.helpers import remove_newline_from_list
from omg_scotus.helpers import require_non_none
from omg_scotus.helpers import suffix_base_url


class FetcherStrategy(ABC):
    """Strategy to be used by Fetcher class."""
    base_url: str
    url: str | None
    most_recent: bool
    soup: bs4.BeautifulSoup

    def get_soup(self) -> bs4.BeautifulSoup:
        """Get BeautifulSoup object."""
        payload = requests.get(self.base_url)
        return BeautifulSoup(payload.text, 'html.parser')

    @abstractmethod
    def get_url_for_term(self) -> None:
        pass

    @abstractmethod
    def get_most_recent_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        pass

    @abstractmethod
    def get_specified_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        pass

    @abstractmethod
    def get_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        pass


class OrdersFetcherStrategy(FetcherStrategy):
    def __init__(
        self,
        most_recent: bool = False,
        url: str | None = None,
    ) -> None:
        self.most_recent = most_recent
        self.url = url
        self.base_url = 'https://www.supremecourt.gov/orders/ordersofthecourt/'
        self.get_url_for_term()
        self.soup = self.get_soup()

    def get_most_recent_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        """Return Dict with the most recent Order Date, Title, and PDF."""
        div_orders = self.soup.find_all('div', class_='column2')[
            0
        ]  # there is one for "More" orders

        spans = div_orders.contents[1].find_all('span')
        date = spans[0].text.strip()
        date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
        title = spans[1].text.strip()
        url = (
            f'https://www.supremecourt.gov/'
            f"{spans[1].contents[0]['href']}"
        )
        retv = {
            'date': date,
            'title': title,
            'pdf': read_pdf(url),
        }
        return retv

    def get_specified_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        """Return Dict with the Order Date, Title, and PDF for a specified URL.
        """
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
        date: str = require_non_none(
            match[0].parent.parent.contents[1].text.strip(),
        )
        title = match[0].text
        url = require_non_none(self.url)

        retv = {
            'date': date,
            'title': title,
            'pdf': read_pdf(url),
        }
        return retv

    def get_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        """Return Dict with Order Date, Order Title, and Order PDF"""
        return (
            self.get_most_recent_payload() if self.most_recent
            else self.get_specified_payload()
        )

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
    def __init__(
        self,
        most_recent: bool = False,
        url: str | None = None,
    ) -> None:
        self.most_recent = most_recent
        self.url = url
        self.base_url = 'https://www.supremecourt.gov/opinions/slipopinion/'
        self.get_url_for_term()
        self.soup = self.get_soup()

    def get_most_recent_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        """Return Dict with the most recent Opinion Date, Title, and PDF."""
        # contents have \n's intercalated, so they get removed
        latest_opinion_row = list(
            filter(
                ('\n').__ne__,
                self.soup.find_all('tr')[2].contents,
            ),
        )

        date = latest_opinion_row[1].text
        docket_number = latest_opinion_row[2].text
        date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
        title = latest_opinion_row[3].text.strip()
        author_initials = latest_opinion_row[5].strip()
        holding = latest_opinion_row[3].contents[0]['title']
        url = (
            f'https://www.supremecourt.gov'
            f"{latest_opinion_row[3].next['href']}"
        )

        docket_json = self.get_docket_json(
            create_docket_number(docket_number),
        )
        petitioner = docket_json['PetitionerTitle']
        respondent = docket_json['RespondentTitle']
        lower_court = docket_json['LowerCourt']

        retv = {
            'date': date,
            'title': title,
            'petitioner': petitioner,
            'respondent': respondent,
            'lower_court': lower_court,
            'holding': holding,
            'is_per_curiam': author_initials == 'PC',
            'pdf': read_pdf(url),
        }
        return retv

    def get_specified_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        """Return Dict with the Order Date, Title, and PDF for a specified URL.

        Input: PDF url
        ----------------
        https://www.supremecourt.gov/opinions/18pdf/17-1672_5hek.pdf

        """
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
        date = remove_newline_from_list(
            match[0].parent.parent.contents,
        )[1].text
        docket_number = remove_newline_from_list(
            match[0].parent.parent.contents,
        )[2].text

        author_initials = remove_newline_from_list(
            match[0].parent.parent.contents,
        )[5].text

        title = match[0].text
        holding = match[0]['title']
        url = require_non_none(self.url)

        docket_json = self.get_docket_json(
            create_docket_number(docket_number),
        )
        petitioner = docket_json['PetitionerTitle']
        respondent = docket_json['RespondentTitle']
        lower_court = docket_json['LowerCourt']
        case_number = docket_json['CaseNumber']

        retv = {
            'date': date,
            'title': title,
            'petitioner': petitioner,
            'respondent': respondent,
            'lower_court': lower_court,
            'case_number': case_number,
            'holding': holding,
            'is_per_curiam': author_initials == 'PC',
            'pdf': read_pdf(url),
        }
        return retv

    def get_url_for_term(self) -> None:
        """Get URL with Term Year suffix."""
        if not self.url:
            # Grabbing most recent date, so get today's Term.
            self.base_url += get_term_year(datetime.today().date())
        else:
            # self.base_url = self.url.replace('')
            term_year = self.url.split('/')[-2][:2]
            self.base_url = (
                f'https://www.supremecourt.gov/opinions/'
                f'slipopinion/{term_year}'
            )

    def get_payload(self) -> dict[str, Stream | str | pdfplumber.pdf.PDF]:
        """Return Dict with Order Date, Order Title, and Order PDF"""
        return (
            self.get_most_recent_payload() if self.most_recent
            else self.get_specified_payload()
        )

    @staticmethod
    def get_docket_json(docket_number: str) -> dict[str, Any]:
        """Return case JSON from SCOTUS online docket."""
        url = (
            f'https://www.supremecourt.gov/rss/cases/json/{docket_number}.json'
        )
        return json.loads(requests.get(url).text)


class Stream(Enum):
    ORDERS = auto()
    OPINIONS = auto()
    DEBUG = auto()


class Fetcher:
    stream: Stream
    strategy: FetcherStrategy
    payload: str
    url: str | None

    def __init__(
        self, stream: Stream | None,
        url: str | None = None, most_recent: bool = True,
    ) -> None:
        self.url = url
        self.most_recent = most_recent
        self.stream = stream if stream else self.set_stream()
        self.payload = ''
        self.set_strategy()

    @classmethod
    def from_url(cls, url: str) -> Fetcher:
        return cls(stream=None, url=url, most_recent=False)

    def set_stream(self) -> Stream:
        url_type = require_non_none(self.url).replace(
            'https://www.supremecourt.gov/', '',
        ).split('/')[0]
        if url_type == 'orders':
            return Stream.ORDERS
        elif url_type == 'opinions':
            return Stream.OPINIONS
        else:
            raise NotImplementedError

    def get_payload(self) -> dict[str, Stream | str | pdfplumber.pdf.PDF]:
        fs = self.strategy
        retv = fs.get_payload()
        retv['stream'] = self.stream
        return retv

    def set_strategy(self) -> None:
        if self.stream is Stream.ORDERS:
            self.strategy = OrdersFetcherStrategy(
                most_recent=self.most_recent, url=self.url,
            )
        elif self.stream is Stream.OPINIONS:
            self.strategy = OpinionsFetcherStrategy(
                most_recent=self.most_recent, url=self.url,
            )
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
