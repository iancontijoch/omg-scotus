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
from omg_scotus.helpers import remove_char_from_list
from omg_scotus.helpers import require_non_none
from omg_scotus.helpers import suffix_base_url


class FetcherStrategy(ABC):
    """Strategy to be used by Fetcher class."""
    stream: Stream
    most_recent: bool
    url: str | None
    base_url: str
    soup: bs4.BeautifulSoup

    def __init__(
        self,
        stream: Stream,
        most_recent: bool = False,
        url: str | None = None,

    ) -> None:
        self.stream = stream
        self.most_recent = most_recent
        self.url = url
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
        return f'{href}{self.get_term_for_url(self.url)}'

    @staticmethod
    def get_term_for_url(url: str | None) -> str:
        """Get URL with Term Year suffix."""
        if not url:
            # We are grabbing most recent date, so get today's Term.
            term_year = get_term_year(datetime.today().date())
        elif url.split('/')[-3] == 'opinions':
            term_year = url.split('/')[-2][:2]
        elif url.split('/')[-3] == 'orders':
            url_date = url.split('/')[-1][:6]
            term_year = get_term_year(
                datetime.strptime(url_date, '%m%d%y').date(),
            )
        else:
            raise NotImplementedError
        return term_year

    def get_soup(self) -> bs4.BeautifulSoup:
        """Get BeautifulSoup object."""
        payload = requests.get(self.base_url)
        return BeautifulSoup(payload.text, 'html.parser')

    @abstractmethod
    def get_contents(self) -> BeautifulSoup.contents: pass

    @abstractmethod
    def get_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
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

    def get_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        match = self.get_contents()

        if self.url:
            date: str = require_non_none(
                match[0].parent.parent.contents[1].text.strip(),
            )
            title = match[0].text
            url = require_non_none(self.url)

        else:
            date = match.text.strip()
            title = match[1].text.strip()
            url = (
                f'https://www.supremecourt.gov/'
                f"{match[1].contents[0]['href']}"
            )

        retv = {
            'date': datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d'),
            'title': title,
            'pdf': read_pdf(url),
        }
        return retv

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
            match = remove_char_from_list(
                self.soup.find_all('tr')[2].contents, '\n',
            )
        return match

    def get_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:

        match = self.get_contents()
        # Slip Opinions have an extra column with an R number.
        offset = 1 if self.stream is Stream.SLIP_OPINIONS else 0

        if self.url:
            date = remove_char_from_list(
                match[0].parent.parent.contents, '\n',
            )[1].text
            docket_number = remove_char_from_list(
                match[0].parent.parent.contents, '\n',
            )[2].text

            author_initials = remove_char_from_list(
                match[0].parent.parent.contents, '\n',
            )[5].text

            title = match[0].text
            holding = match[0]['title']
            url = require_non_none(self.url)
        else:
            date = match[offset].text
            docket_number = match[offset+1].text
            title = match[offset+2].text.strip()
            author_initials = match[offset+4].text.strip()
            if self.stream is Stream.SLIP_OPINIONS:
                holding = match[offset+2].contents[0]['title']
            else:
                holding = None
            url = (
                f'https://www.supremecourt.gov'
                f"{match[offset+2].next['href']}"
            )

        docket_json = self.get_docket_json(
            create_docket_number(docket_number),
        )

        petitioner = docket_json['PetitionerTitle']
        respondent = docket_json['RespondentTitle']
        lower_court = docket_json['LowerCourt']
        case_number = docket_json['CaseNumber']

        retv = {
            'date': datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d'),
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

    @staticmethod
    def get_docket_json(docket_number: str) -> dict[str, Any]:
        """Return case JSON from SCOTUS online docket."""
        url = (
            f'https://www.supremecourt.gov/rss/cases/json/{docket_number}.json'
        )
        return json.loads(requests.get(url).text)


class Stream(Enum):
    ORDERS = auto()
    SLIP_OPINIONS = auto()
    OPINIONS_RELATING_TO_ORDERS = auto()
    DEBUG = auto()


class Fetcher:
    stream: Stream
    strategy: FetcherStrategy
    payload: str
    url: str | None

    def __init__(
        self, stream: Stream,
        url: str | None = None, most_recent: bool = True,
    ) -> None:
        self.stream = stream
        self.url = url
        self.most_recent = most_recent
        self.payload = ''
        self.set_strategy()

    @classmethod
    def from_url(cls, url: str, stream: Stream) -> Fetcher:
        return cls(stream=stream, url=url, most_recent=False)

    def get_payload(self) -> dict[str, Stream | str | pdfplumber.pdf.PDF]:
        fs = self.strategy
        retv = fs.get_payload()
        retv['stream'] = self.stream
        return retv

    def set_strategy(self) -> None:
        if self.stream is Stream.ORDERS:
            self.strategy = OrdersFetcherStrategy(
                stream=self.stream, most_recent=self.most_recent, url=self.url,
            )
        elif self.stream in (
            Stream.SLIP_OPINIONS,
            Stream.OPINIONS_RELATING_TO_ORDERS,
        ):
            self.strategy = OpinionsFetcherStrategy(
                stream=self.stream, most_recent=self.most_recent, url=self.url,
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
