from __future__ import annotations

import re
from datetime import datetime
from enum import auto
from enum import Enum
from io import BytesIO
from typing import TypeVar

import bs4
import pdfplumber
import requests
from bs4 import BeautifulSoup
# import hashlib

T = TypeVar('T')


def require_non_none(x: T | None) -> T:
    if x is None:
        raise AssertionError('Expected non None value.')
    else:
        return x


class OrderType(Enum):
    ORDER_LIST = auto()
    MISCELLANEOUS_ORDER = auto()

    @staticmethod
    def from_string(label: str) -> OrderType:
        """Return OrderType from string."""
        if label.upper() == 'MISCELLANOUS ORDER':
            return OrderType.MISCELLANEOUS_ORDER
        elif label.upper() == 'ORDER LIST':
            return OrderType.ORDER_LIST
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        """Return string representation of OrderType."""
        return self.name.replace('_', ' ')


class OrderSection(Enum):
    CERTIORARI_SUMMARY_DISPOSITIONS = auto()
    ORDERS_IN_PENDING_CASES = auto()
    CERTIORARI_GRANTED = auto()
    CERTIORARI_DENIED = auto()
    HABEAS_CORPUS_DENIED = auto()
    MANDAMUS_DENIED = auto()
    REHEARINGS_DENIED = auto()

    @staticmethod
    def from_string(label: str) -> OrderSection:
        if label in (
            'CERTIORARI -- SUMMARY DISPOSITIONS',
            'CERTIORARI -- SUMMARY DISPOSITION',
        ):
            return OrderSection.CERTIORARI_SUMMARY_DISPOSITIONS
        elif label in ('ORDERS IN PENDING CASES', 'ORDER IN PENDING CASE'):
            return OrderSection.ORDERS_IN_PENDING_CASES
        elif label == 'CERTIORARI GRANTED':
            return OrderSection.CERTIORARI_GRANTED
        elif label == 'CERTIORARI DENIED':
            return OrderSection.CERTIORARI_DENIED
        elif label == 'HABEAS CORPUS DENIED':
            return OrderSection.HABEAS_CORPUS_DENIED
        elif label == 'MANDAMUS DENIED':
            return OrderSection.MANDAMUS_DENIED
        elif label in ('REHEARINGS DENIED', 'REHEARING DENIED'):
            return OrderSection.REHEARINGS_DENIED
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        """Return string representation of OrderSection."""
        if self.name == 'CERTIORARI_SUMMARY_DISPOSITIONS':
            return 'CERTIORARI -- SUMMARY DISPOSITIONS'
        else:
            return self.name.replace('_', ' ').strip()


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


def latest_order(div: bs4.element.Tag) -> tuple[
    str,
    OrderType,
    str,
]:
    """Return latest order date and type."""
    spans = div.contents[1].find_all('span')

    date = spans[0].text.strip()
    date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')
    order_type = OrderType.from_string(spans[1].text.strip())
    order_url = f"https://www.supremecourt.gov/{spans[1].contents[0]['href']}"

    return (date, order_type, order_url)


def read_pdf(url: str) -> pdfplumber.PDF.pages:
    """Return pages object from url."""
    rq = requests.get(url)
    with pdfplumber.open(BytesIO(rq.content)) as pdf:
        return pdf.pages


def get_case_num_and_name(txt: str | None) -> list[str]:
    """Return case numbers/names XXX-XXXX
    e.g. BOB v. ALICE or IN RE BOB"""

    #  123-4567, 12A34, 123, ORIG., IN RE .... BOB V. ALICE
    if txt is None:
        return ['No cases.']
    pattern = r'(\d+.*?\d|\d+.*?ORIG.)\s+(.*?V.*?$|IN RE.*?$)'
    matches = re.findall(pattern=pattern, string=txt, flags=re.M)
    return matches


def print_section_cases(section_name: str, cases: list[str] | str) -> None:
    """Prints the output for found cases"""
    num_cases = 0
    if isinstance(cases, list):
        num_cases = len(cases)
        cases = '\n'.join(['  '.join(m).strip() for m in cases])
    print(
        f'\n{section_name}: {num_cases} case'
        f"{(num_cases > 1 or cases == 'No cases.')*'s'}"
        f"\n{'-'*72}\n{cases}\n{'-'*72}\n",
    )


def get_section_cases(section_matches: dict[OrderSection, str | None]) -> None:
    """Return cases for each section of the Order List"""

    for section in OrderSection:
        section_text = section_matches[section]
        section_cases = get_case_num_and_name(section_text)
        print_section_cases(str(section), section_cases)


def create_order_summary(
    section_matches: dict[OrderSection, str | None],
    date: str,
    order_type: str,
) -> None:
    print('\n\n--------ORDER LIST SUMMARY--------')
    print(date)
    print(order_type)
    get_section_cases(section_matches)


def get_page_indices(pages: pdfplumber.PDF.pages) -> list[tuple[int, int]]:
    """Return start and end indices for each page."""
    retv = []
    start = 0
    full_txt = ''.join([p.extract_text() for p in pages])
    for pg in pages:
        pg_len = len(pg.extract_text())
        end = start + pg_len
        assert full_txt[start:end] == pg.extract_text()
        retv.append((start, end))
        start += pg_len
    return retv


def get_order_section_matches(order_text: str) -> dict[
    OrderSection,
    str | None,
]:
    """Return dict of (Order Section: Order Section Text) for Order List"""
    retv = {}
    # regex pattern looks text between section headers and between
    # last section header and EOF
    pattern = (
        r'(CERTIORARI +-- +SUMMARY +DISPOSITIONS*|ORDERS* +IN +PENDING'
        r' +CASES*|CERTIORARI +GRANTED|CERTIORARI +DENIED|HABEAS +'
        r'CORPUS +DENIED|MANDAMUS +DENIED|REHEARINGS* +DENIED)'
        r'(.*?(?=CERTIORARI +-- +SUMMARY +DISPOSITIONS*|ORDERS* +IN '
        r'+PENDING +CASES*|CERTIORARI +GRANTED|CERTIORARI +DENIED'
        r'| HABEAS + CORPUS + DENIED | MANDAMUS + DENIED | REHEARINGS'
        r' * +DENIED)|.*$)'
    )
    matches = re.finditer(
        pattern=pattern,
        string=order_text, flags=re.DOTALL,
    )

    for m in matches:
        section_title, section_content = ' '.join(
            m.groups()[0].split(),
        ), m.groups()[1]  # remove whitespace noise

        retv[OrderSection.from_string(section_title)] = section_content

    for section in OrderSection:
        if section not in retv:
            retv[section] = None

    return retv


def split_order_list_text(
    pages_text: str,
    page_indices: list[tuple[int, int]],
    order_type: OrderType,
) -> tuple[str, str, str]:
    """
    Split Opinion List into orders and opinions and remove page numbers from
    orders and headers from opinions.
    """
    full_text, order_text, opinion_text = ('', '', '')
    if order_type is OrderType.MISCELLANEOUS_ORDER and len(page_indices) == 1:
        start, end = page_indices[0]
        full_text, order_text = pages_text[start:end], pages_text[start:end]
    else:
        first_op_page = True
        for start, end in page_indices:
            segment = pages_text[start:end]
            # ends w/ page num (not an opinion)
            if segment.splitlines()[-1].strip().isnumeric():
                segment = '\n'.join(
                    segment.splitlines()[
                        :-1
                    ],
                )  # crop out page num
                order_text += segment
            else:
                # omit header info in opinions
                segment = '\n'.join(segment.splitlines()[3:])
                if first_op_page:
                    # transition from orders to opinions missing space before
                    segment = '\n' + segment  # readd
                    first_op_page = False
                opinion_text += segment
            full_text += segment
    return full_text, order_text, opinion_text


def main() -> int:
    url_orders = 'https://www.supremecourt.gov/orders/ordersofthecourt/21'

    page = requests.get(url_orders)
    soup = BeautifulSoup(page.text, 'html.parser')

    # div with current orders
    div_orders = soup.find_all('div', class_='column2')[
        0
    ]  # there is one for "More" orders
    # to check for changes to order section
    # hash = hashlib.sha256(div_orders.text.encode('utf-8')).hexdigest()

    # most recent order
    date, order_type, order_url = latest_order(div_orders)
    pgs = read_pdf(order_url)
    pgs = read_pdf(
        'https://www.supremecourt.gov/orders/courtorders/080421zr_lkgn.pdf',
    )
    order_type = OrderType.MISCELLANEOUS_ORDER

    # TODO: In chambers orders
    # (https://www.supremecourt.gov/orders/courtorders/080421zr_lkgn.pdf)

    pgs_txt = ''.join([p.extract_text() for p in pgs])
    # opinions = get_opinions_from_orders(pgs_txt)

    # op1, op2 = Opinion(opinions[0]), Opinion(opinions[1])
    indices = get_page_indices(pgs)

    _, orders, opinions = split_order_list_text(pgs_txt, indices, order_type)

    print(_)

    # order_section_matches = get_order_section_matches(orders)

    # create_order_summary(order_section_matches, date, order_type)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
