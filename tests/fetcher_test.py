from __future__ import annotations

import pytest

from omg_scotus.fetcher import FetcherStrategy


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        (
            'https://www.supremecourt.gov/opinions/21pdf/21a632_o7jq.pdf',
            '21',
        ),
        (
            'https://www.supremecourt.gov/opinions/19pdf/21a632_o7jq.pdf',
            '19',
        ),
        (
            (
                'https://www.supremecourt.gov/orders/courtorders/'
                '041822zor_19m2.pdf'
            ),
            '21',
        ),
    ),
)
def test_get_term_for_url(s: str, expected: str) -> None:
    assert FetcherStrategy.get_term_for_url(s) == expected
