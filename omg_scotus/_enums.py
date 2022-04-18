from __future__ import annotations

from enum import auto
from enum import Enum


class OrderListSectionType(Enum):

    CERTIORARI_SUMMARY_DISPOSITIONS = auto()
    ORDERS_IN_PENDING_CASES = auto()
    CERTIORARI_GRANTED = auto()
    CERTIORARI_DENIED = auto()
    HABEAS_CORPUS_DENIED = auto()
    MANDAMUS_DENIED = auto()
    REHEARINGS_DENIED = auto()

    @staticmethod
    def from_string(label: str) -> OrderListSectionType:
        if label in (
            'CERTIORARI -- SUMMARY DISPOSITIONS',
            'CERTIORARI -- SUMMARY DISPOSITION',
        ):
            return OrderListSectionType.CERTIORARI_SUMMARY_DISPOSITIONS
        elif label in ('ORDERS IN PENDING CASES', 'ORDER IN PENDING CASE'):
            return OrderListSectionType.ORDERS_IN_PENDING_CASES
        elif label == 'CERTIORARI GRANTED':
            return OrderListSectionType.CERTIORARI_GRANTED
        elif label == 'CERTIORARI DENIED':
            return OrderListSectionType.CERTIORARI_DENIED
        elif label == 'HABEAS CORPUS DENIED':
            return OrderListSectionType.HABEAS_CORPUS_DENIED
        elif label == 'MANDAMUS DENIED':
            return OrderListSectionType.MANDAMUS_DENIED
        elif label in ('REHEARINGS DENIED', 'REHEARING DENIED'):
            return OrderListSectionType.REHEARINGS_DENIED
        else:
            raise NotImplementedError


class RulesType(Enum):
    RULES_OF_APPELLATE_PROCEDURE = auto()
    RULES_OF_BANKRUPTCY_PROCEDURE = auto()
    RULES_OF_CIVIL_PROCEDURE = auto()
    RULES_OF_CRIMINAL_PROCEDURE = auto()


class OrderType(Enum):
    ORDER_LIST = auto()
    MISCELLANEOUS_ORDER = auto()
    STAY_ORDER = auto()
    RULES_ORDER = auto()
