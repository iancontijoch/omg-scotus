from __future__ import annotations

from typing import TypeVar

T = TypeVar('T')


def require_non_none(x: T | None) -> T:
    if x is None:
        raise AssertionError('Expected non None value.')
    else:
        return x
