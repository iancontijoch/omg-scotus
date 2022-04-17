from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from typing import Any

from omg_scotus.helpers import get_pdf_text
from omg_scotus.helpers import is_stay_order
from omg_scotus.helpers import require_non_none
from omg_scotus.order_list import OrderList


class ParserStrategy(ABC):

    def __init__(self, msg: dict[str, Any]) -> None:
        self.msg = msg

    @abstractmethod
    def parse(self) -> str | defaultdict[str, str | None]: pass

    @abstractmethod
    def get_object(self) -> Any: pass


class OrderListParserStrategy(ParserStrategy):

    def parse(self) -> defaultdict[str, str | None]:
        """ Return dict of Order Text and Opinion Text.

        Order Lists include Orders, which are formatted with page
        numbers at the footer. However, they can also include Opinions
        relating to orders, which have the same format as opinions. This
        method extracts both.
        """
        retv: defaultdict[str, str | None] = defaultdict(lambda: None)
        first_opinion_page = True

        for start, end in self.msg['pdf_page_indices']:
            segment = self.msg['pdf_text'][start:end]

            if segment.splitlines()[-1].strip().isnumeric():
                # ends w/ page num, so it's an order page
                segment = '\n'.join(segment.splitlines()[:-1])  # crop Pg Num
                if 'orders_text' in retv:
                    retv['orders_text'] += segment
                else:
                    retv['orders_text'] = segment
            else:
                # it's an opinion page
                segment = '\n'.join(segment.splitlines()[3:])  # omit header
                if first_opinion_page:
                    # transition from orders to opinions missing space before
                    segment = '\n' + segment  # readd
                    first_opinion_page = False
                if 'opinions_text' in retv:
                    retv['opinions_text'] += segment
                else:
                    retv['opinions_text'] = segment

        return retv

    def get_object(self) -> OrderList:
        """Create OrderList."""
        parsed_dict = self.parse()
        order_list = OrderList(
            orders_text=require_non_none(parsed_dict['orders_text']),
            opinions_text=parsed_dict['opinions_text'],
        )
        return order_list


class MiscOrderParserStrategy(ParserStrategy):

    def parse(self) -> str:
        """Return Misc Order text."""
        retv = ''
        for start, end in self.msg['pdf_page_indices']:
            segment = self.msg['pdf_text'][start:end]
            retv += segment
        return retv

    def get_object(self) -> Any:
        pass


class StayOrderParserStrategy(ParserStrategy):

    def parse(self) -> str:
        """Return Stay Order text."""
        retv = ''
        for start, end in self.msg['pdf_page_indices']:
            segment = self.msg['pdf_text'][start:end]
            retv += segment
        return retv

    def get_object(self) -> None:
        pass


class Parser:
    """Accept Fetcher payload and determine strategy"""
    parser_strategy: ParserStrategy

    def __init__(
        self,
        msg: dict[str, Any],
    ) -> None:
        self.msg = msg
        self.msg['pdf_text'] = get_pdf_text(self.msg['pdf'])
        self.msg['pdf_page_indices'] = self.get_pdf_page_indices()
        self.set_parser_strategy()

    def get_pdf_page_indices(self) -> list[tuple[int, int]]:
        """Return start and end indices for each page in PDF."""
        retv, start, pdf_text = [], 0, self.msg['pdf_text']
        for p in self.msg['pdf'].pages:
            pg_len = len(p.extract_text())
            end = start + pg_len
            assert pdf_text[start:end] == p.extract_text()
            retv.append((start, end))
            start += pg_len
        return retv

    def set_parser_strategy(self) -> None:
        """Set parser strategy depending on payload received.
        """
        if self.msg['order_title'] == 'Order List':
            self.parser_strategy = OrderListParserStrategy(self.msg)
        elif self.msg['order_title'] == 'Miscellaneous Order':
            if is_stay_order(
                order_title=self.msg['order_title'],
                pdf=self.msg['pdf'],
            ):
                self.parser_strategy = StayOrderParserStrategy(self.msg)
            else:
                self.parser_strategy = MiscOrderParserStrategy(self.msg)
        else:
            raise NotImplementedError

    def parse(self) -> str | defaultdict[str, str | None]:
        """Use strategy parser."""
        ps = self.parser_strategy
        return ps.parse()

    def get_object(self) -> Any:
        ps = self.parser_strategy
        return ps.get_object()
