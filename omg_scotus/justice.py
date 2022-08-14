from __future__ import annotations

import re
from datetime import date
from enum import auto
from enum import Enum

from dateutil.relativedelta import relativedelta
# from omg_scotus._enums import JusticeTag


class Role(Enum):
    ASSOCIATE_JUSTICE = auto()
    CHIEF_JUSTICE = auto()


class Ideology(Enum):
    LIBERAL = auto()
    CONSERVATIVE = auto()


class President(Enum):
    REAGAN = auto()
    CLINTON = auto()
    BUSH = auto()
    OBAMA = auto()
    TRUMP = auto()
    BIDEN = auto()


class JusticeTag(Enum):
    ROBERTS = auto()
    THOMAS = auto()
    BREYER = auto()
    ALITO = auto()
    SOTOMAYOR = auto()
    KAGAN = auto()
    GORSUCH = auto()
    KAVANAUGH = auto()
    BARRETT = auto()
    GINSBURG = auto()
    KENNEDY = auto()
    SCALIA = auto()
    SOUTER = auto()
    PER_CURIAM = auto()

    @staticmethod
    def from_string(s: str) -> JusticeTag:
        """Return JusticeTag from string."""
        d = {
            'CHIEF JUSTICE': JusticeTag.ROBERTS,
            'JUSTICE THOMAS': JusticeTag.THOMAS,
            'JUSTICE BREYER': JusticeTag.BREYER,
            'JUSTICE ALITO': JusticeTag.ALITO,
            'JUSTICE SOTOMAYOR': JusticeTag.SOTOMAYOR,
            'JUSTICE KAGAN': JusticeTag.KAGAN,
            'JUSTICE GORSUCH': JusticeTag.GORSUCH,
            'JUSTICE KAVANAUGH': JusticeTag.KAVANAUGH,
            'JUSTICE BARRETT': JusticeTag.BARRETT,
            'JUSTICE GINSBURG': JusticeTag.GINSBURG,
            'JUSTICE KENNEDY': JusticeTag.KENNEDY,
            'JUSTICE SCALIA': JusticeTag.SCALIA,
            'JUSTICE SOUTER': JusticeTag.SOUTER,
            'PER CURIAM': JusticeTag.PER_CURIAM,
            'ROBERTS': JusticeTag.ROBERTS,
            'THOMAS': JusticeTag.THOMAS,
            'BREYER': JusticeTag.BREYER,
            'ALITO': JusticeTag.ALITO,
            'SOTOMAYOR': JusticeTag.SOTOMAYOR,
            'KAGAN': JusticeTag.KAGAN,
            'GORSUCH': JusticeTag.GORSUCH,
            'KAVANAUGH': JusticeTag.KAVANAUGH,
            'BARRETT': JusticeTag.BARRETT,
            'GINSBURG': JusticeTag.GINSBURG,
            'KENNEDY': JusticeTag.KENNEDY,
            'SCALIA': JusticeTag.SCALIA,
            'SOUTER': JusticeTag.SOUTER,
        }
        if s not in d:
            raise NotImplementedError(
                f'String {s} not recognized as a Justice.',
            )
        else:
            return d[s]


class Justice:
    first_name: str
    middle_name: str | None
    last_name: str
    suffix: str | None
    start_date: date
    birth_date: date
    tag: JusticeTag
    role: Role
    rank: int
    ideology: Ideology
    nominating_president: President
    _regex_pattern: str

    def __init__(
        self,
        first_name: str,
        last_name: str,
        start_date: date,
        birth_date: date,
        tag: JusticeTag,
        nominating_president: President,
        role: Role,
        ideology: Ideology,
        middle_name: str | None = None,
        suffix: str | None = None,
    ) -> None:

        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.suffix = suffix
        self.start_date = start_date
        self.birth_date = birth_date
        self.tag = tag
        self.nominating_president = nominating_president
        self.role = role
        self.ideology = ideology
        self.full_name = self._set_fullname()
        self.rank = self._get_rank()
        self.tenure = self._get_court_tenure()
        self.age = self._get_age()
        self._regex_pattern = self._get_regex_pattern()

    def _get_court_tenure(self) -> str:
        """Return length of tenure in years."""
        return f'{relativedelta(date.today(), self.start_date).years} years'

    def _get_age(self) -> int:
        """Return age."""
        return relativedelta(date.today(), self.birth_date).years

    def _set_fullname(self) -> str:
        """Return full name, including middle Initial and Honorifics."""
        s = f'{self.first_name} '
        if self.middle_name:
            s += f'{self.middle_name[0]}. '
        s += self.last_name
        if self.suffix:
            s += f', {self.suffix}'
        return s

    def _get_rank(self) -> int:
        pass

    def _get_regex_pattern(self) -> str:
        """Return regex pattern to identify Justice."""
        if self.role is Role.CHIEF_JUSTICE:
            return (
                fr'((Chief)? ?Justice|{self.first_name})[ \,\.\w]+'
                fr'{self.last_name}|CHIEF +JUSTICE'
            )
        else:
            return (
                fr'(((CHIEF)? ?JUSTICE|{self.first_name})[ \,\.\w]+)?'
                fr'({self.last_name}|{self.last_name.upper()})'
            )


def extract_justice(string: str) -> JusticeTag:
    """Search text for Justices names and return first tag."""
    court = create_court()
    d = {j._get_regex_pattern(): j.tag for j in court}
    for k, v in d.items():
        if bool(re.search(k, string, re.DOTALL | re.M | re.I)):
            return v
    raise NotImplementedError


def create_court() -> tuple[Justice, ...]:

    chief = Justice(
        first_name='John',
        middle_name='Glover',
        last_name='Roberts',
        suffix='Jr.',
        tag=JusticeTag.ROBERTS,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.CHIEF_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )

    thomas = Justice(
        first_name='Clarence',
        last_name='Thomas',
        tag=JusticeTag.THOMAS,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )

    breyer = Justice(
        first_name='Stephen',
        middle_name='Gerald',
        last_name='Breyer',
        tag=JusticeTag.BREYER,
        start_date=date(1994, 8, 3),
        birth_date=date(1938, 8, 15),
        nominating_president=President.CLINTON,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.LIBERAL,
    )

    alito = Justice(
        first_name='Samuel',
        middle_name='Anthony',
        last_name='Alito',
        suffix='Jr.',
        tag=JusticeTag.ALITO,
        start_date=date(2006, 1, 31),
        birth_date=date(1950, 4, 1),
        nominating_president=President.BUSH,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )

    sotomayor = Justice(
        first_name='Sonia',
        middle_name='Maria',
        last_name='Sotomayor',
        tag=JusticeTag.SOTOMAYOR,
        start_date=date(2009, 8, 8),
        birth_date=date(1954, 6, 25),
        nominating_president=President.OBAMA,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.LIBERAL,
    )

    kagan = Justice(
        first_name='Elena',
        last_name='Kagan',
        tag=JusticeTag.KAGAN,
        start_date=date(2010, 8, 7),
        birth_date=date(1960, 4, 28),
        nominating_president=President.OBAMA,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.LIBERAL,
    )

    gorsuch = Justice(
        first_name='Neil',
        middle_name='McGill',
        last_name='Gorsuch',
        tag=JusticeTag.GORSUCH,
        start_date=date(2017, 4, 10),
        birth_date=date(1967, 8, 29),
        nominating_president=President.TRUMP,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )

    kavanaugh = Justice(
        first_name='Brett',
        middle_name='Michael',
        last_name='Kavanaugh',
        tag=JusticeTag.KAVANAUGH,
        start_date=date(2018, 10, 6),
        birth_date=date(1965, 2, 12),
        nominating_president=President.TRUMP,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )

    barrett = Justice(
        first_name='Amy',
        middle_name='Coney',
        last_name='Barrett',
        tag=JusticeTag.BARRETT,
        start_date=date(2020, 10, 27),
        birth_date=date(1972, 1, 28),
        nominating_president=President.TRUMP,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )

    return (
        chief, thomas, breyer, alito, sotomayor,
        kagan, gorsuch, kavanaugh, barrett,
    )
