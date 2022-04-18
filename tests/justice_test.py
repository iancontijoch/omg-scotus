from __future__ import annotations

import pytest
from pytest_lazyfixture import lazy_fixture

from omg_scotus.justice import extract_justice
from omg_scotus.justice import JusticeTag


def test_justice_court_tenure(justice_w_middle_name_title):
    assert justice_w_middle_name_title.tenure == '16 years'


def test_justice_age(justice_w_middle_name_title):
    assert justice_w_middle_name_title.age == 67


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        (lazy_fixture('justice_w_middle_name_title'), 'John G. Roberts, Jr.'),
        (lazy_fixture('justice_wo_middle_name_title'), 'Mickey Mouse, Jr.'),
        (lazy_fixture('justice_w_middle_name'), 'John G. Roberts'),
        (lazy_fixture('justice_wo_middle_name'), 'Mickey Mouse'),
    ),
)
def test_justice_full_name(s, expected):
    assert s.full_name == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        ('John G. Roberts, Jr.', JusticeTag.CHIEF),
        ('CHIEF  JUSTICE', JusticeTag.CHIEF),
        ('chief justice', JusticeTag.CHIEF),
        ('Chief Justice John G. Roberts, Jr.', JusticeTag.CHIEF),
        ('Sonia Sotomayor', JusticeTag.SOTOMAYOR),
        ('Sonia M. Sotomayor', JusticeTag.SOTOMAYOR),
        ('Samuel Alito', JusticeTag.ALITO),
        ('JUSTICE ALITO', JusticeTag.ALITO),
        ('ALITO, JJ.', JusticeTag.ALITO),
        ('SOTOMAYOR', JusticeTag.SOTOMAYOR),
    ),
)
def test_get_justice_tag_from_string_found(s, expected):
    assert extract_justice(string=s) == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        ('Snia Stmayor', pytest.raises(NotImplementedError)),
        ('Mickey Mouse', pytest.raises(NotImplementedError)),
    ),
)
def test_get_justice_tag_from_string_not_found(s, expected):
    with expected:
        assert extract_justice(string=s) == expected
