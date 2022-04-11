from __future__ import annotations

from enum import auto
from enum import Enum


class OrderListSection(Enum):
    CERTIORARI_SUMMARY_DISPOSITIONS = auto()
    ORDERS_IN_PENDING_CASES = auto()
    CERTIORARI_GRANTED = auto()
    CERTIORARI_DENIED = auto()
    HABEAS_CORPUS_DENIED = auto()
    MANDAMUS_DENIED = auto()
    REHEARINGS_DENIED = auto()

    @staticmethod
    def from_string(label: str) -> OrderListSection:
        if label in (
            'CERTIORARI -- SUMMARY DISPOSITIONS',
            'CERTIORARI -- SUMMARY DISPOSITION',
        ):
            return OrderListSection.CERTIORARI_SUMMARY_DISPOSITIONS
        elif label in ('ORDERS IN PENDING CASES', 'ORDER IN PENDING CASE'):
            return OrderListSection.ORDERS_IN_PENDING_CASES
        elif label == 'CERTIORARI GRANTED':
            return OrderListSection.CERTIORARI_GRANTED
        elif label == 'CERTIORARI DENIED':
            return OrderListSection.CERTIORARI_DENIED
        elif label == 'HABEAS CORPUS DENIED':
            return OrderListSection.HABEAS_CORPUS_DENIED
        elif label == 'MANDAMUS DENIED':
            return OrderListSection.MANDAMUS_DENIED
        elif label in ('REHEARINGS DENIED', 'REHEARING DENIED'):
            return OrderListSection.REHEARINGS_DENIED
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        """Return string representation of OrderSection."""
        if self.name == 'CERTIORARI_SUMMARY_DISPOSITIONS':
            return 'CERTIORARI -- SUMMARY DISPOSITIONS'
        else:
            return self.name.replace('_', ' ').strip()
