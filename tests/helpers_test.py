from __future__ import annotations

from datetime import date

import pytest

from omg_scotus.helpers import get_term_year


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
