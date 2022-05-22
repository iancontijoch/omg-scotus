# Implementation of Website checker
import datetime
import hashlib
import time

import bs4
import requests

from omg_scotus.fetcher import Stream
from omg_scotus.helpers import get_term_year


class ChangeDetector:
    stream: Stream
    url: str
    watch_element: bs4.BeautifulSoup
    scrape_interval: int

    def __init__(self, stream: Stream, scrape_interval: int = 30):
        self.stream = stream
        self.url = self.set_url()
        self.response = self.get_response()
        self.watch_element = self.set_watch_element()
        self.scrape_interval = scrape_interval

    def set_url(self) -> str:
        """Set URL."""
        year = get_term_year(datetime.date.today())

        if self.stream is Stream.ORDERS:
            return 'https://www.supremecourt.gov/orders/ordersofthecourt/'
        elif self.stream is Stream.SLIP_OPINIONS:
            return f'https://www.supremecourt.gov/opinions/slipopinion/{year}'
        elif self.stream is Stream.OPINIONS_RELATING_TO_ORDERS:
            return (
                f'https://www.supremecourt.gov/opinions'
                f'/relatingtoorders/{year}'
            )
        else:
            raise NotImplementedError

    def get_response(self) -> requests.Response:
        """Get HTML response."""
        return requests.get(self.url)

    def set_watch_element(self) -> bs4.BeautifulSoup:
        """Set element to monitor for changes."""
        soup = bs4.BeautifulSoup(self.response.text, 'html.parser')
        if self.stream is Stream.ORDERS:
            return soup.find_all('div', class_='column2')[0]
        elif self.stream in (
            Stream.SLIP_OPINIONS,
            Stream.OPINIONS_RELATING_TO_ORDERS,
        ):
            return soup.find_all('tr')[2]
        else:
            raise NotImplementedError

    def get_hash(self) -> str:
        """Get hash from watched element."""
        return hashlib.sha256(
            self.watch_element.text.encode('utf-8'),
        ).hexdigest()

    def start_detection(self) -> bool:
        """Detect whether an element has had a change."""
        print(f'\nMonitoring {self.stream}...\n')
        hash = self.get_hash()
        while True:
            try:
                time.sleep(self.scrape_interval)
                new_hash = self.get_hash()
                print(f'Last checked: {datetime.datetime.now()}')
                if hash == new_hash:
                    continue
                else:
                    print('CHANGE DETECTED!!!')

            except Exception:
                raise ValueError


cd1 = ChangeDetector(stream=Stream.OPINIONS_RELATING_TO_ORDERS)
cd2 = ChangeDetector(stream=Stream.ORDERS)

# cd1.start_detection()
cd2.start_detection()
