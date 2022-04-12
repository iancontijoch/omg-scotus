from __future__ import annotations

import hashlib
from datetime import datetime
from io import BytesIO

import pdfplumber
import requests
from bs4 import BeautifulSoup

from omg_scotus.helpers import require_non_none
from omg_scotus.order import OrderType


class Fetcher():
    """Fetch data from https://www.supremecourt.gov"""
    url: str | None
    soup: BeautifulSoup
    order_data: tuple[str, OrderType, str]

    def __init__(self, url: str | None = None):
        self.soup = self.get_soup()
        self.url = url if url else self.get_latest_order_data()[2]
        self.order_data = (
            self.get_order_data() if url
            else self.get_latest_order_data()
        )

    @staticmethod
    def get_order_metadata(
        spans: BeautifulSoup.contents,
    ) -> tuple[str, OrderType, str]:
        date = spans[0].text.strip()
        date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
        order_title = spans[1].text.strip()
        order_type = OrderType.from_string(order_title)
        order_url = (
            f'https://www.supremecourt.gov/'
            f"{spans[1].contents[0]['href']}"
        )

        return (date, order_type, order_url)

    def get_soup(self) -> BeautifulSoup:
        # https://www.supremecourt.gov/orders/courtorders/011422zr_21o2.pdf
        ORDERS_URL = 'https://www.supremecourt.gov/orders/ordersofthecourt'

        payload = requests.get(ORDERS_URL)
        return BeautifulSoup(payload.text, 'html.parser')

    def get_order_data(self) -> tuple[str, OrderType, str]:
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
        order_date: str = require_non_none(
            match[0].parent.parent.contents[1].text.strip(),
        )
        order_type = OrderType.from_string(match[0].text)
        order_url = require_non_none(self.url)
        return order_date, order_type, order_url

    def get_latest_order_data(self) -> tuple[str, OrderType, str]:
        # div with current orders
        div_orders = self.soup.find_all('div', class_='column2')[
            0
        ]  # there is one for "More" orders
        spans = div_orders.contents[1].find_all('span')
        return self.get_order_metadata(spans)

    def read_pdf(self) -> pdfplumber.PDF.pages:
        """Return pages object from url."""
        rq = requests.get(require_non_none(self.url))
        with pdfplumber.open(BytesIO(rq.content)) as pdf:
            return pdf.pages

    def detect_changes(self) -> str:
        """TODO: Implement"""
        # to check for changes to order section
        div_orders = self.soup.find_all('div', class_='column2')[
            0
        ]  # there is one for "More" orders
        hash = hashlib.sha256(div_orders.text.encode('utf-8')).hexdigest()
        return hash
