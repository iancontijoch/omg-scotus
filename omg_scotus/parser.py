from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from typing import Any

from omg_scotus.document_list import DocumentList
from omg_scotus.document_list import OpinionList
from omg_scotus.document_list import OrderList
from omg_scotus.fetcher import Stream
from omg_scotus.helpers import get_pdf_text
from omg_scotus.helpers import is_stay_order
from omg_scotus.helpers import require_non_none
from omg_scotus.opinion import StayOpinion


class ParserStrategy(ABC):

    def __init__(self, msg: dict[str, Any]) -> None:
        self.msg = msg

    @abstractmethod
    def parse(self) -> str | defaultdict[str, str | None]: pass

    @abstractmethod
    def get_object(self) -> Any: pass


class SlipOpinionParserStrategy(ParserStrategy):
    def parse(self) -> str:
        retv = ''
        for start, end in self.msg['pdf_page_indices']:
            segment = self.msg['pdf_text'][start:end]
            retv += '\n'.join(segment.splitlines()[3:])  # omit header
        if retv == '':
            raise ValueError('No opinion text was parsed.')
        return retv

    def get_object(self) -> list[DocumentList]:
        parsed_text = self.parse()
        date = self.msg['date']
        holding = self.msg['holding']
        petitioner = self.msg['petitioner']
        respondent = self.msg['respondent']
        lower_court = self.msg['lower_court']
        case_number = self.msg['case_number']
        is_per_curiam = self.msg['is_per_curiam']
        stream = self.msg['stream']
        url = self.msg['url']

        return [
            OpinionList(
                stream,
                parsed_text, date, holding, petitioner,
                respondent, lower_court, case_number,
                is_per_curiam, url,
            ),
        ]


class OrderListParserStrategy(ParserStrategy):

    def parse(self) -> defaultdict[str, str | None]:
        """ Return dict of Order Text and Opinion Text.

        Order Lists include Orders, which are formatted with page
        numbers at the footer. However, they can also include Opinions
        relating to orders, which have the same format as opinions. This
        method extracts both.

        A Miscellaneous Order that isn't a stay order is essentially
        an OrderList with a single order. The OrderList Strategy is used. Minor
        formatting differences exist and are addressed.
        """
        retv: defaultdict[str, str | None] = defaultdict(lambda: None)

        is_misc_order = self.msg['title'] == 'Miscellaneous Order'
        is_order_list = self.msg['title'] == 'Order List'

        for start, end in self.msg['pdf_page_indices']:
            segment = self.msg['pdf_text'][start:end]
            # Miscellaneous Orders aren't numbered, but OrderLists are
            if (
                is_misc_order or
                (
                    is_order_list
                    and segment.splitlines()[-1].strip().isnumeric()
                )
            ):
                # ends w/ page num, so it's an order page
                if is_order_list:
                    segment = '\n'.join(segment.splitlines()[:-1])  # crop Pg#
                if 'orders_text' in retv:
                    retv['orders_text'] += segment
                else:
                    retv['orders_text'] = segment
        return retv

    def get_object(self) -> list[DocumentList]:
        """Create OrderList and OrderOpinionList."""
        parsed_dict = self.parse()
        date = self.msg['date']
        url = self.msg['url']
        stream = self.msg['stream']

        retv: list[DocumentList] = []
        retv.append(
            OrderList(
                text=require_non_none(parsed_dict['orders_text']),
                date=date, url=url, stream=stream,
            ),
        )

        return retv


# class OpinionRelatedToOrderStrategy(ParserStrategy):
#     def parse(self) -> str:
#         """Return Stay Order text."""
#         retv = ''
#         for start, end in self.msg['pdf_page_indices']:
#             segment = self.msg['pdf_text'][start:end]
#             retv += '\n'.join(segment.splitlines()[3:])  # omit header
#         return retv

#     def get_object(self) -> list[Any]:
#         parsed_text = self.parse()
#         date = self.msg['date']
#         holding = self.msg['holding']
#         petitioner = self.msg['petitioner']
#         respondent = self.msg['respondent']
#         lower_court = self.msg['lower_court']
#         case_number = self.msg['case_number']
#         is_per_curiam = self.msg['is_per_curiam']
#         stream = self.msg['stream']
#         return [
#             OpinionList(
#                 stream, parsed_text, date, holding, petitioner,
#                 respondent, lower_court, case_number,
#                 is_per_curiam,
#             ),
#         ]


class StayOrderParserStrategy(ParserStrategy):

    def parse(self) -> str:
        """Return Stay Order text."""
        retv = ''
        for start, end in self.msg['pdf_page_indices']:
            segment = self.msg['pdf_text'][start:end]
            retv += segment
        return retv

    def get_object(self) -> list[Any]:
        parsed_order = self.parse()
        return [StayOpinion(text=parsed_order, url=self.msg['url'])]


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
        if self.msg['stream'] is Stream.ORDERS:
            if self.msg['title'] == 'Order List':
                self.parser_strategy = OrderListParserStrategy(self.msg)
            elif self.msg['title'] == 'Miscellaneous Order':
                if is_stay_order(
                    order_title=self.msg['title'],
                    pdf=self.msg['pdf'],
                ):
                    self.parser_strategy = StayOrderParserStrategy(self.msg)
                else:
                    self.parser_strategy = OrderListParserStrategy(self.msg)
            else:
                raise NotImplementedError
        elif self.msg['stream'] in (
            Stream.SLIP_OPINIONS,
            Stream.OPINIONS_RELATING_TO_ORDERS,
        ):
            self.parser_strategy = SlipOpinionParserStrategy(self.msg)
        # elif self.msg['stream'] is Stream.OPINIONS_RELATING_TO_ORDERS:
        #     self.parser_strategy = OpinionRelatedToOrderStrategy(self.msg)
        else:
            raise NotImplementedError

    def parse(self) -> str | defaultdict[str, str | None]:
        """Use strategy parser."""
        ps = self.parser_strategy
        return ps.parse()

    def get_object(self) -> Any:
        ps = self.parser_strategy
        return ps.get_object()
