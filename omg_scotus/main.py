from __future__ import annotations

import re

import pdfplumber

from omg_scotus.fetcher import Fetcher
from omg_scotus.helpers import require_non_none
from omg_scotus.order import OrderType
from omg_scotus.order_list_section import OrderListSection


def get_case_num_and_name(txt: str | None) -> list[str]:
    """Return case numbers/names XXX-XXXX
    e.g. BOB v. ALICE or IN RE BOB"""

    #  123-4567, 12A34, 123, ORIG., IN RE .... BOB V. ALICE
    if txt is None:
        return ['No cases.']
    pattern = r'(\d+.*?\d|\d+.*?ORIG.)\s+(.*?V.*?$|IN RE.*?$)'
    matches = re.findall(pattern=pattern, string=txt, flags=re.M)
    return matches


def print_section_cases(section_name: str, cases: list[str]) -> None:
    """Prints the output for found cases"""
    if cases[0] == 'No cases.':
        num_cases = 0
        cases_text = cases[0]
    else:
        num_cases = len(cases)
        cases_text = '\n'.join(['  '.join(m).strip() for m in cases])
    print(
        f'\n{section_name}: {num_cases} case'
        f"{(num_cases > 1 or num_cases == 0)*'s'}"
        f"\n{'-'*72}\n{cases_text}\n{'-'*72}\n",
    )


def get_section_cases(
    section_matches: dict[OrderListSection, str | None],
) -> None:
    """Return cases for each section of the Order List"""

    for section in OrderListSection:
        section_text = section_matches[section]
        section_cases = get_case_num_and_name(section_text)
        print_section_cases(str(section), section_cases)


def create_order_summary(
    section_matches: dict[OrderListSection, str | None],
    date: str,
    order_type: OrderType,
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
    OrderListSection,
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

        retv[OrderListSection.from_string(section_title)] = section_content

    for section in OrderListSection:
        if section not in retv:
            retv[section] = None

    return retv


def split_order_list_text(
    pages_text: str,
    page_indices: list[tuple[int, int]],
    order_type: OrderType,
) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Split Opinion List into orders and opinions and remove page numbers from
    orders and headers from opinions.
    """
    full_text, order_text, opinion_text, stays_text = None, None, None, None
    if order_type is OrderType.MISCELLANEOUS_ORDER and len(page_indices) == 1:
        start, end = page_indices[0]
        full_text = pages_text[start:end]
        # if stay order vs regular order
        if (
            ' '.join(
                pages_text.splitlines()[0]
                .split(),
            ) == 'Supreme Court of the United States'
        ):
            stays_text = pages_text[start:end]
        else:
            order_text = pages_text[start:end]
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
                if order_text:
                    order_text += segment
                else:
                    order_text = segment
            else:
                # omit header info in opinions
                segment = '\n'.join(segment.splitlines()[3:])
                if first_op_page:
                    # transition from orders to opinions missing space before
                    segment = '\n' + segment  # readd
                    first_op_page = False
                if opinion_text:
                    opinion_text += segment
                else:
                    opinion_text = segment
                if full_text:
                    full_text += segment
                else:
                    full_text = segment
    return full_text, order_text, opinion_text, stays_text


def main() -> int:
    # fetcher = Fetcher(
    #     url=(
    #         'https://www.supremecourt.gov'
    #         + '/orders/courtorders/011422zr_21o2.pdf'
    #     ),
    # )
    fetcher = Fetcher()
    pgs = fetcher.read_pdf()

    pgs_txt = ''.join([p.extract_text() for p in pgs])

    # opinions = get_opinions_from_orders(pgs_txt)

    # op1, op2 = Opinion(opinions[0]), Opinion(opinions[1])
    indices = get_page_indices(pgs)

    order_date, order_type, order_url = fetcher.get_latest_order_data()
    # order_date, order_type, order_url = fetcher.get_order_data()

    _, orders, opinions, stays = split_order_list_text(
        pgs_txt, indices, order_type,
    )

    order_section_matches = get_order_section_matches(require_non_none(orders))

    # if stays != '':
    #     order_section_matches =

    create_order_summary(order_section_matches, order_date, order_type)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
