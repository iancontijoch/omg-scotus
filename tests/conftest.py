from __future__ import annotations

from datetime import date

import pytest

from omg_scotus.justice import create_court
from omg_scotus.justice import Ideology
from omg_scotus.justice import Justice
from omg_scotus.justice import JusticeTag
from omg_scotus.justice import President
from omg_scotus.justice import Role
from omg_scotus.opinion import StayOpinion


@pytest.fixture
def justice_w_middle_name_title() -> Justice:
    retv = Justice(
        first_name='John',
        middle_name='Glover',
        last_name='Roberts',
        tag=JusticeTag.ROBERTS,
        suffix='Jr.',
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.CHIEF_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
        is_active=True,
    )
    return retv


@pytest.fixture
def justice_w_middle_name() -> Justice:
    retv = Justice(
        first_name='John',
        middle_name='Glover',
        last_name='Roberts',
        tag=JusticeTag.ROBERTS,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.CHIEF_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
        is_active=True,
    )
    return retv


@pytest.fixture
def justice_wo_middle_name_title() -> Justice:
    retv = Justice(
        first_name='Mickey',
        last_name='Mouse',
        suffix='Jr.',
        tag=JusticeTag.ALITO,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
        is_active=False,
    )
    return retv


@pytest.fixture
def justice_wo_middle_name() -> Justice:
    retv = Justice(
        first_name='Mickey',
        last_name='Mouse',
        tag=JusticeTag.ALITO,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
        is_active=False,
    )
    return retv


@pytest.fixture
def court():
    return create_court(current=True)
