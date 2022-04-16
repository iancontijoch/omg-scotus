from __future__ import annotations

from enum import auto
from enum import Enum


class CaseType(Enum):
    ORIGINAL = auto()
    CERTIORARI = auto()


class Case:
    number: str
    name: str
    type: CaseType
    parties: tuple[str, str]

    def __init__(self, number: str, name: str):
        self.number = number
        self.name = name
