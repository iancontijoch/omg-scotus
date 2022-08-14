from __future__ import annotations

import re
from datetime import date
from datetime import datetime
from datetime import timedelta
from io import BytesIO
from typing import Any
from typing import TypeVar

import pdfplumber
import requests

from omg_scotus._enums import Disposition
from omg_scotus.justice import JusticeTag

T = TypeVar('T')


def require_non_none(x: T | None) -> T:
    if x is None:
        raise AssertionError('Expected non None value.')
    else:
        return x


def get_term_year(dt: date) -> str:
    """Return Term Year given a date in XX format.

    The U.S. Supreme Court's term begins on the first Monday in October and
    goes through the Sunday before the first Monday in October of the
    following year.

    """
    def get_first_monday_in_october(year: int) -> date:
        """Return date of first Monday in October."""
        d = datetime(year, 10, 1)
        offset = -d.weekday()
        if offset < 0:
            offset += 7
        return (d + timedelta(offset)).date()

    t0 = get_first_monday_in_october(dt.year-1)
    t1 = get_first_monday_in_october(dt.year)

    if t0 <= dt < t1:
        return str(dt.year - 1)[2:]  # get prior year's first Monday in Oct.
    else:  # between Oct-Dec
        return str(dt.year)[2:]


def suffix_base_url(base_url: str, url: str | None) -> str:
    """Append year to base URL."""
    # URL was passed, so get Term from extracted URL date
    mmddyy = require_non_none(url).split('/')[-1][:6]
    term_yr = get_term_year(datetime.strptime(mmddyy, '%m%d%y').date())
    return base_url + term_yr


def read_pdf(url: str) -> pdfplumber.PDF:
    """Return pages object from url."""
    rq = requests.get(require_non_none(url))
    with pdfplumber.open(BytesIO(rq.content)) as pdf:
        return pdf


def get_pdf_text(
    pdf: pdfplumber.pdf.PDF, from_pg: int | None = None,
    to_pg: int | None = None,
) -> str:
    """Return pdf text in PDF document pages."""
    return ''.join([p.extract_text() for p in pdf.pages[from_pg:to_pg]])


def is_stay_order(order_title: str, pdf: pdfplumber.pdf.PDF) -> bool:
    """Distinguish between Stay Order vs. Single Order List order.

    SCOTUS publishes Stay orders under the 'Miscellaneous Order' title,
    but the format is different from an Order List Misc. Order.
    """

    cond1 = order_title.upper() == 'MISCELLANEOUS ORDER'
    cond2 = len(pdf.pages) == 1
    cond3 = ' '.join(
        get_pdf_text(pdf).splitlines()[0]
        .split(),
    ) == 'Supreme Court of the United States'
    return cond1 and cond2 and cond3


def remove_extra_whitespace(s: str) -> str:
    """Remove extra whitespace."""
    return ' '.join(s.split())


def remove_hyphenation(text: str) -> str:
    return re.sub(
        pattern=r'(\w+)-$\n(\w+)', repl=r'\1\2',
        string=text, flags=re.M,
    )


def remove_char_from_list(lst: list[Any], char: str) -> list[Any]:
    return list(filter((char).__ne__, lst))


def remove_notice(text: str) -> str:
    """Remove NOTICE disclaimer from Syllabus text."""
    return re.sub(r'(?s)NOTICE:.+', '', text)


def create_docket_number(string: str) -> str:
    """Return a docket number to fetch JSON from."""
    match = re.match(r'(\d+)(?=.+Orig\.)', string)
    if match:
        return f'22O{match.groups()[0]}'
    else:
        return string.strip()


def remove_justice_titles(string: str) -> str:
    """Removes JUSTICE, J., J. J., C . J ."""
    pattern = (
        r'\,\s*J\s*\.\,|\,\s*J\s*J\s*\.\,|\,\s*C\s*\.\s*J\s*\.\,|'
        r'JUSTICE\s+|THE\s+(?=CHIEF)|CHIEF\s+JUSTICE'
    )
    s = re.sub(pattern, '', string)
    return s


def add_padding_to_periods(string: str) -> str:
    """Converts 'II-C. Blah' --> 'II-C . Blah'"""
    return string.replace('.', ' . ')


def chief_justice_to_last_name(string: str) -> str:
    """Replace CHIEF JUSTICE with the current Chief Justice's name."""
    return string.replace('CHIEF JUSTICE', 'ROBERTS')


def get_justices_from_sent(
    sent: str,
) -> list[JusticeTag]:
    """Return a list of JusticeTag from str and regex."""
    sent = remove_hyphenation(sent)
    sent = remove_justice_titles(sent)
    sent = remove_extra_whitespace(sent)
    sent = chief_justice_to_last_name(sent)
    if bool(re.search(r'\bPER\s+CURIAM', sent)):
        return [JusticeTag.PER_CURIAM]
    # matches any 3 or more capital letters together within word boundary.
    # Part-III was matching because it's three caps. Lol.
    pattern = r'\b(?!III)[A-Z]{4,}\b'
    return [
        JusticeTag.from_string(remove_extra_whitespace(m))
        for m in re.findall(
            pattern,
            sent,
        )
    ]


def get_disposition_type(string: str) -> list[str]:
    """Return Disposition from holding text."""

    retv = []
    d = {i: disposition for i, disposition in enumerate(Disposition)}
    p = (
        r'(AFFIRMED(?!\s+IN\s+PART))|(AFFIRMED\s+IN\s+PART)|DISMISSED(?!\s'
        r'+IN\s+PART|\s+as\s+improvidently\s+granted)|(DISMISSED\s+IN\s+'
        r'PART)|(DISMISSED\s+as\s+improvidently\s+granted)|(DISMISSED\s+'
        r'for\s+want\s+of\s+jurisdiction)|(REMANDED(?!\s+IN\s+PART))|(REM'
        r'ANDED\s+IN\s+PART)|(REVERSED(?!\s+IN\s+PART))|(REVERSED\s+IN\s+P'
        r'ART)|(VACATED(?!\s+IN\s+PART))|(VACATED\s+IN\s+PART)|(applications'
        r'*\s+for\s+stays*[^.!?]+granted\.)'
    )
    for m in re.finditer(p, string):
        for i, _ in enumerate(m.groups()):
            if _:
                retv.append(d[i].name)
    return retv
