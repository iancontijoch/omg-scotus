from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timedelta
from io import BytesIO
from typing import TypeVar

import pdfplumber
import requests

T = TypeVar('T')


def require_non_none(x: T | None) -> T:
    if x is None:
        raise AssertionError('Expected non None value.')
    else:
        return x


def get_term_year(dt: date) -> str:
    """Return Term Year given a date

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
    if not url:
        return base_url
    mmddyy = url.split('/')[-1][:6]
    term_yr = get_term_year(datetime.strptime(mmddyy, '%m%d%y').date())
    return base_url + term_yr


def read_pdf(url: str) -> pdfplumber.PDF:
    """Return pages object from url."""
    rq = requests.get(require_non_none(url))
    with pdfplumber.open(BytesIO(rq.content)) as pdf:
        return pdf


def get_pdf_text(pdf: pdfplumber.pdf.PDF) -> str:
    return ''.join([p.extract_text() for p in pdf.pages])


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
