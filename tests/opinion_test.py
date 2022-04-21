from __future__ import annotations

from omg_scotus.justice import JusticeTag
from omg_scotus.opinion import OpinionType


def test_get_parties(sample_order_opinion):
    expected = ('KRISTOPHER LOVE', 'TEXAS')
    assert sample_order_opinion.get_parties() == expected


def test_get_case_name(sample_order_opinion):
    expected = 'KRISTOPHER LOVE v. TEXAS'
    assert sample_order_opinion.get_case_name() == expected


def test_get_case_number(sample_order_opinion):
    expected = '21–5050'
    assert sample_order_opinion.get_case_number() == expected


def test_get_court(sample_order_opinion):
    expected = 'COURT OF CRIMINAL APPEALS OF TEXAS'
    assert sample_order_opinion.get_court() == expected


def test_get_author_author(sample_order_opinion):
    expected = JusticeTag.SOTOMAYOR
    sample_order_opinion.author = None
    sample_order_opinion.get_author()

    assert sample_order_opinion.author == expected


def test_get_author_author_joiners(sample_order_opinion):
    expected = [JusticeTag.BREYER, JusticeTag.KAGAN]
    sample_order_opinion.joiners = None
    sample_order_opinion.get_author()

    assert sample_order_opinion.joiners == expected


def test_get_type(sample_order_opinion):
    expected = OpinionType.DISSENT
    assert sample_order_opinion.get_type() == expected
