from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from typing import Any

from spacy.language import Language

from omg_scotus._enums import DocumentType
from omg_scotus.fetcher import Stream
from omg_scotus.helpers import get_pdf_text
from omg_scotus.helpers import is_stay_order
from omg_scotus.helpers import require_non_none
from omg_scotus.opinion import StayOpinion
from omg_scotus.release import OpinionRelatingToOrder
from omg_scotus.release import OrderRelease
from omg_scotus.release import Release
from omg_scotus.release import SlipOpinion


class ParserStrategy(ABC):

    def __init__(
        self, msg: dict[str, Any],
        document_type: DocumentType,
        nlp: Language,
    ) -> None:
        self.msg = msg
        self.nlp = nlp
        self.document_type = document_type

    @abstractmethod
    def parse(self) -> str | defaultdict[str, str | None]: pass

    @abstractmethod
    def get_object(self) -> Any: pass


class OpinionParserStrategy(ParserStrategy):
    def parse(self) -> str:
        retv = ''
        for start, end in self.msg['pdf_page_indices']:
            segment = self.msg['pdf_text'][start:end]
            lines = segment.splitlines()
            # if the first line is a space, it is a decree with short header
            if len(lines) > 0:
                header_end_idx = 2 if lines[0].isspace() else 3
                # omit header
                retv += '\n' + '\n'.join(lines[header_end_idx:])
        if retv == '':
            raise ValueError('No opinion text was parsed.')
        return retv

    def get_object(self) -> Release:
        parsed_text = self.parse()
        date = self.msg['date']
        holding = self.msg['holding']
        disposition_text = self.msg['disposition_text']
        petitioner = self.msg['petitioner']
        respondent = self.msg['respondent']
        lower_court = self.msg['lower_court']
        case_number = self.msg['case_number']
        title = self.msg['title']
        is_per_curiam = self.msg['is_per_curiam']
        is_decree = self.msg['is_decree']
        url = self.msg['url']
        nlp = self.nlp
        document_type = self.document_type

        if document_type is DocumentType.SLIP_OPINION:
            return SlipOpinion(
                date=date,
                url=url,
                text=parsed_text,
                document_type=self.document_type,
                holding=holding,
                disposition_text=disposition_text,
                petitioner=petitioner, respondent=respondent,
                lower_court=lower_court, case_number=case_number,
                is_per_curiam=is_per_curiam,
                is_decree=is_decree,
                title=title,
                nlp=nlp,
            )
        elif document_type is DocumentType.OPINION_RELATING_TO_ORDERS:
            return OpinionRelatingToOrder(
                date=date,
                text=parsed_text,
                case_number=case_number,
                url=url,
                document_type=self.document_type,
                petitioner=petitioner,
                respondent=respondent,
                lower_court=lower_court,
                title=title,
                nlp=nlp,
            )
        else:
            raise NotImplementedError('DocumentType not expected for Opinion.')


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

    def get_object(self) -> list[Release]:
        """Create OrderList and OrderOpinionList."""
        parsed_dict = self.parse()
        date = self.msg['date']
        url = self.msg['url']
        title = self.msg['title']
        pdf = self.msg['pdf']
        document_type = self.document_type

        retv: list[Release] = []
        retv.append(
            OrderRelease(
                text=require_non_none(parsed_dict['orders_text']),
                date=date, url=url, title=title, document_type=document_type,
                pdf=pdf, nlp=self.nlp,
            ),
        )
        return retv


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


class RulesParserStrategy(ParserStrategy):

    def parse(self) -> str:
        retv = get_pdf_text(self.msg['pdf'], 3)
        retv = re.sub(
            r'(?m)^\s+FEDERAL\s+RULES\s+OF\s+[A-Z]+\s+PROCEDURE\s+\d+\s+|\s+'
            r'\d+\s+FEDERAL\s+RULES\s+OF\s+[A-Z]+\s+PROCEDURE\s+$', '', retv,

        )  # eliminate footer and header
        return retv

    def get_object(self) -> Release:
        """Create RulesOrder."""
        text = self.parse()
        date = self.msg['date']
        url = self.msg['url']
        title = self.msg['title']
        pdf = self.msg['pdf']

        return OrderRelease(
            date=date, title=title, url=url,
            text=text, pdf=pdf, document_type=self.document_type,
            nlp=self.nlp,
        )


class Parser:
    """Accept Fetcher payload and determine strategy"""
    parser_strategy: ParserStrategy
    document_type: DocumentType
    nlp: Language

    def __init__(
        self,
        msg: dict[str, Any],
        nlp: Language,
    ) -> None:
        self.msg = msg
        self.nlp = nlp
        self.document_type = self.set_document_type()
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

    def set_document_type(self) -> DocumentType:
        """Set document type for parsing strategy to consume."""
        if self.msg['stream'] is Stream.ORDERS:
            if self.msg['title'] == 'Order List':
                return DocumentType.ORDER_LIST
            elif self.msg['title'] == 'Miscellaneous Order':
                if is_stay_order(
                    order_title=self.msg['title'],
                    pdf=self.msg['pdf'],
                ):
                    return DocumentType.STAY_ORDER
                else:
                    return DocumentType.ORDER_LIST
            elif self.msg['title'].startswith('Rules'):
                return DocumentType.RULES_ORDER
            else:
                raise NotImplementedError
        elif self.msg['stream'] is Stream.SLIP_OPINIONS:
            return DocumentType.SLIP_OPINION
        elif self.msg['stream'] is Stream.OPINIONS_RELATING_TO_ORDERS:
            return DocumentType.OPINION_RELATING_TO_ORDERS
        else:
            raise NotImplementedError

    def set_parser_strategy(self) -> None:
        """Set parser strategy depending on payload received.
        """
        if self.document_type in (
            DocumentType.ORDER_LIST,
            DocumentType.MISCELLANEOUS_ORDER,
        ):
            self.parser_strategy = OrderListParserStrategy(
                self.msg,
                self.document_type,
                self.nlp,
            )
        elif self.document_type is DocumentType.STAY_ORDER:
            self.parser_strategy = StayOrderParserStrategy(
                self.msg,
                self.document_type,
                self.nlp,
            )
        elif self.document_type is DocumentType.RULES_ORDER:
            self.parser_strategy = RulesParserStrategy(
                self.msg,
                self.document_type,
                self.nlp,
            )
        elif self.document_type in (
            DocumentType.SLIP_OPINION,
            DocumentType.OPINION_RELATING_TO_ORDERS,
        ):
            self.parser_strategy = OpinionParserStrategy(
                self.msg,
                self.document_type,
                self.nlp,
            )
        else:
            raise NotImplementedError

    def parse(self) -> str | defaultdict[str, str | None]:
        """Use strategy parser."""
        ps = self.parser_strategy
        return ps.parse()

    def get_object(self) -> Any:
        ps = self.parser_strategy
        return ps.get_object()
