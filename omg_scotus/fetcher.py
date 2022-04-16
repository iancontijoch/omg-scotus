from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from enum import auto
from enum import Enum

import bs4
import pdfplumber
import requests
from bs4 import BeautifulSoup

from omg_scotus.helpers import read_pdf
from omg_scotus.helpers import require_non_none
from omg_scotus.helpers import suffix_base_url


class FetcherStrategy(ABC):
    """Strategy to be used by Fetcher class."""
    base_url: str
    url: str | None
    most_recent: bool
    soup: bs4.BeautifulSoup

    def get_soup(self) -> bs4.BeautifulSoup:
        payload = requests.get(self.base_url)
        return BeautifulSoup(payload.text, 'html.parser')

    @abstractmethod
    def get_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]: pass


class OrdersFetcherStrategy(FetcherStrategy):
    def __init__(
        self,
        most_recent: bool = False,
        url: str | None = None,
    ) -> None:
        self.most_recent = most_recent
        self.url = url
        self.base_url = 'https://www.supremecourt.gov/orders/ordersofthecourt/'
        self.base_url = suffix_base_url(
            self.base_url, self.url,
        )  # add year to base_url
        self.soup = self.get_soup()

    def get_most_recent_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        """Return Dict with the most recent Order Date, Title, and PDF."""
        div_orders = self.soup.find_all('div', class_='column2')[
            0
        ]  # there is one for "More" orders

        spans = div_orders.contents[1].find_all('span')
        date = spans[0].text.strip()
        date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
        order_title = spans[1].text.strip()
        order_url = (
            f'https://www.supremecourt.gov/'
            f"{spans[1].contents[0]['href']}"
        )
        retv = {
            'date': date,
            'order_title': order_title,
            'pdf': read_pdf(order_url),
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
        order_title = match[0].text
        order_url = require_non_none(self.url)

        retv = {
            'date': date,
            'order_title': order_title,
            'pdf': read_pdf(order_url),
        }
        return retv

    def get_payload(self) -> dict[str, str | pdfplumber.pdf.PDF]:
        """Return Dict with Order Date, Order Title, and Order PDF"""
        return (
            self.get_most_recent_payload() if self.most_recent
            else self.get_specified_payload()
        )


class OpinionsFetcherStrategy(FetcherStrategy):
    def __init__(self) -> None:
        self.url = 'https://www.supremecourt.gov/opinions/slipopinion/21'

    def get_payload(self) -> dict[str, Stream | str | pdfplumber.pdf.PDF]:
        raise NotImplementedError


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
            self.strategy = OpinionsFetcherStrategy()
        else:
            raise NotImplementedError


# class Fetcher2():
#     """Fetch data from https://www.supremecourt.gov"""
#     url: str | None
#     soup: BeautifulSoup
#     order_payload: tuple[str, str, pdfplumber.PDF]
#     order_creator: OrderCreator

#     def __init__(self, url: str | None = None):
#         self.soup = self.get_soup()
#         # self.url = url if url else self.get_latest_order_html()[2]
#         # self.order_data = (
#         #     self.get_order_data() if url
#         #     else self.get_latest_order_html()
#         # )
#         self.order_creator = self.get_order_creator()

#     @staticmethod
#     def get_order_metadata(
#         spans: BeautifulSoup.contents,
#     ) -> tuple[str, OrderType, str]:
#         date = spans[0].text.strip()
#         date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
#         order_title = spans[1].text.strip()
#         order_type = OrderType.from_string(order_title)
#         order_url = (
#             f'https://www.supremecourt.gov/'
#             f"{spans[1].contents[0]['href']}"
#         )

#         return (date, order_type, order_url)

#     @staticmethod
#     def read_pdf(url: str) -> pdfplumber.PDF:
#         """Return pages object from url."""
#         rq = requests.get(require_non_none(url))
#         with pdfplumber.open(BytesIO(rq.content)) as pdf:
#             return pdf

#     def get_order_payload(self) -> tuple(str, str, pdfplumber.pdf):
#         """Return Tuple with Order Date, Order Title, and Order PDF"""
#         spans = self.get_latest_order_html()
#         date = spans[0].text.strip()
#         date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
#         order_title = spans[1].text.strip()
#         order_url = (
#             f'https://www.supremecourt.gov/'
#             f"{spans[1].contents[0]['href']}"
#         )
#         return (date, order_title, self.read_pdf(order_url))

#     def get_order_creator(self) -> OrderCreator:
#         """Return an Order Creator Factory."""
#         date, order_title, pdf = self.get_order_payload()
#         pdf_text = ''.join([p.extract_text() for p in pdf.pages])

#         creator = None

#         if order_title.upper() == 'MISCELLANEOUS ORDER':
#             # Distinguish between Stay Order vs. Single Order List order
#             cond1 = len(pdf.pages) == 1
#             cond2 = ' '.join(
#                 pdf_text.splitlines()[0]
#                 .split(),
#             ) == 'Supreme Court of the United States'
#             if cond1 and cond2:
#                 creator = StayOrderCreator
#             else:
#                 creator = MiscellaneousOrderCreator
#         elif order_title.upper() == 'ORDER LIST':
#             creator = OrderListCreator
#         elif order_title.upper() == 'RULES OF APPELLATE PROCEDURE':
#             creator = RulesOrderCreator(
#                 rules_type=RulesType.RULES_OF_APPELLATE_PROCEDURE,
#             )
#         elif order_title.upper() == 'RULES OF BANKRUPTCY PROCEDURE':
#             creator = RulesOrderCreator(
#                 rules_type=RulesType.RULES_OF_BANKRUPTCY_PROCEDURE,
#             )
#         elif order_title.upper() == 'RULES OF CIVIL PROCEDURE':
#             creator = RulesOrderCreator(
#                 rules_type=RulesType.RULES_OF_CIVIL_PROCEDURE,
#             )
#         elif order_title.upper() == 'RULES OF CRIMINAL PROCEDURE':
#             creator = RulesOrderCreator(
#                 rules_type=RulesType.RULES_OF_CRIMINAL_PROCEDURE,
#             )
#         else:
#             raise NotImplementedError

#         return (
#             creator().set_date(date=date)
#             .set_order_title(order_title=order_title)
#         )

#     def create_order(self) -> Order:
#         return self.order_creator.get_text()

#     def get_soup(self) -> BeautifulSoup:
#         # https://www.supremecourt.gov/orders/courtorders/011422zr_21o2.pdf
#         ORDERS_URL = 'https://www.supremecourt.gov/orders/ordersofthecourt'

#         payload = requests.get(ORDERS_URL)
#         return BeautifulSoup(payload.text, 'html.parser')

#     def get_order_dgata(self) -> tuple[str, OrderType, str]:
#         """Includes optional url fetching"""
#         match: BeautifulSoup.contents = require_non_none(
#             self.soup.find_all(
#                 attrs={
#                     'href': require_non_none(self.url).replace(
#                         'https://www.supremecourt.gov',
#                         '',
#                     ),
#                 },
#             ),
#         )
#         order_date: str = require_non_none(
#             match[0].parent.parent.contents[1].text.strip(),
#         )
#         order_type = OrderType.from_string(match[0].text)
#         order_url = require_non_none(self.url)
#         return order_date, order_type, order_url

#     def get_latest_order_html(self) -> tuple[str, OrderType, str]:
#         # div with current orders
#         div_orders = self.soup.find_all('div', class_='column2')[
#             0
#         ]  # there is one for "More" orders
#         return div_orders.contents[1].find_all('span')

#     def detect_changes(self) -> str:
#         """TODO: Implement"""
#         # to check for changes to order section
#         div_orders = self.soup.find_all('div', class_='column2')[
#             0
#         ]  # there is one for "More" orders
#         hash = hashlib.sha256(div_orders.text.encode('utf-8')).hexdigest()
#         return hash
