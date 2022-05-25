from __future__ import annotations

from datetime import date

import pytest

from omg_scotus._enums import Disposition
from omg_scotus.helpers import create_docket_number
from omg_scotus.helpers import get_disposition_type
from omg_scotus.helpers import get_justices_from_sent
from omg_scotus.helpers import get_term_year
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import remove_hyphenation
from omg_scotus.justice import JusticeTag


@pytest.mark.parametrize(
    ('dt', 'expected'),
    (
        (date(2020, 12, 3), '20'),
        (date(2019, 8, 3), '18'),
        (date(2021, 10, 15), '21'),
        (date(2022, 4, 16), '21'),
        (date(2019, 10, 6), '18'),
        (date(2019, 10, 7), '19'),
    ),
)
def test_get_term_year(dt, expected):
    assert get_term_year(dt) == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        ('FOO  BAR', 'FOO BAR'),
        ('  FOO BAR', 'FOO BAR'),
        ('  FOO  BAR ', 'FOO BAR'),
    ),
)
def test_remove_extra_whitespace(s, expected):
    assert remove_extra_whitespace(s) == expected


def test_remove_hyphenation():
    text = """The State acknowledges that the Court of Criminal Ap-
peals “never reached the federal issues Love raises,” Brief
in Opposition 13, but the State contends that the court’s
harmless-error analysis constitutes an independent and ad-
equate  ground  for  the  judgment  below,  precluding  this
Court’s jurisdiction.  See Foster v. Chatman, 578 U. S. 488,
497 (2016). As already shown, however, the state harmless-
error rule was not “an ‘adequate’  basis for the court’s deci-
sion” on Love’s federal claim.  Ibid.  Indeed, in this situa-
tion, the rule is entirely beside the point.  The State’s juris-
dictional argument therefore fails. """

    expected = """The State acknowledges that the Court of Criminal Appeals “never reached the federal issues Love raises,” Brief
in Opposition 13, but the State contends that the court’s
harmless-error analysis constitutes an independent and adequate  ground  for  the  judgment  below,  precluding  this
Court’s jurisdiction.  See Foster v. Chatman, 578 U. S. 488,
497 (2016). As already shown, however, the state harmlesserror rule was not “an ‘adequate’  basis for the court’s decision” on Love’s federal claim.  Ibid.  Indeed, in this situation, the rule is entirely beside the point.  The State’s jurisdictional argument therefore fails. """

    assert remove_hyphenation(text) == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        ('143, Orig.', '22O143'),
        ('19-1257', '19-1257'),
    ),
)
def test_create_docket_number(s: str, expected: str) -> None:
    assert create_docket_number(s) == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        (
            """KAVANAUGH, J., delivered the opinion of the Court, in which ROBERTS,
C. J., and THOMAS, BREYER, SOTOMAYOR, KAGAN, and GORSUCH, JJ.,
joined.""", [
                JusticeTag.KAVANAUGH, JusticeTag.CHIEF, JusticeTag.THOMAS,
                JusticeTag.BREYER, JusticeTag.SOTOMAYOR, JusticeTag.KAGAN,
                JusticeTag.GORSUCH,
            ],
        ),
        ("""Statement of BREYER, J.""", [JusticeTag.BREYER]),
        (
            """  Statement  of  JUSTICE  ALITO,  with  whom  JUSTICE
THOMAS, JUSTICE KAVANAUGH, and JUSTICE BARRETT join,
respecting the denial of certiorari
Statment of BREYER, J.""", [
                JusticeTag.ALITO, JusticeTag.THOMAS,
                JusticeTag.KAVANAUGH, JusticeTag.BARRETT,
                JusticeTag.BREYER,
            ],
        ),
    ),
)
def test_get_justices_from_sent(s: str, expected: str) -> None:
    assert get_justices_from_sent(s) == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        (
            'Adjudged to be AFFIRMED IN PART, REVERSED IN PART, and case REMANDED.',
            [
                Disposition.AFFIRMED_IN_PART, Disposition.REVERSED_IN_PART,
                Disposition.REMANDED,
            ],
        ),
        (
            'Judgment REVERSED and case REMANDED.', [
                Disposition.REVERSED,
                Disposition.REMANDED,
            ],
        ),
        (
            'Writ of certiorari DISMISSED as improvidently granted.',
            [Disposition.DISMISSED_AS_IMPROVIDENTLY_GRANTED],
        ),
        (
            'Petition GRANTED.  Determination of United States Court of Appeals for the Ninth Circuit that Rivas-Villegas is not entitled to qualified immunity REVERSED.',
            [Disposition.REVERSED],
        ),
    ),
)
def test_get_disposition_type(s, expected):
    assert get_disposition_type(s) == expected
