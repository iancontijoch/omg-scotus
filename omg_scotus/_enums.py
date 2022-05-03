from __future__ import annotations

from enum import auto
from enum import Enum


class OrderSectionType(Enum):

    CERTIORARI_SUMMARY_DISPOSITIONS = auto()
    ORDERS_IN_PENDING_CASES = auto()
    CERTIORARI_GRANTED = auto()
    CERTIORARI_DENIED = auto()
    HABEAS_CORPUS_DENIED = auto()
    MANDAMUS_DENIED = auto()
    REHEARINGS_DENIED = auto()

    @staticmethod
    def from_string(label: str) -> OrderSectionType:
        if label in (
            'CERTIORARI -- SUMMARY DISPOSITIONS',
            'CERTIORARI -- SUMMARY DISPOSITION',
        ):
            return OrderSectionType.CERTIORARI_SUMMARY_DISPOSITIONS
        elif label in ('ORDERS IN PENDING CASES', 'ORDER IN PENDING CASE'):
            return OrderSectionType.ORDERS_IN_PENDING_CASES
        elif label == 'CERTIORARI GRANTED':
            return OrderSectionType.CERTIORARI_GRANTED
        elif label == 'CERTIORARI DENIED':
            return OrderSectionType.CERTIORARI_DENIED
        elif label == 'HABEAS CORPUS DENIED':
            return OrderSectionType.HABEAS_CORPUS_DENIED
        elif label == 'MANDAMUS DENIED':
            return OrderSectionType.MANDAMUS_DENIED
        elif label in ('REHEARINGS DENIED', 'REHEARING DENIED'):
            return OrderSectionType.REHEARINGS_DENIED
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


class DocumentType(Enum):
    ORDER_LIST = auto()
    MISCELLANEOUS_ORDER = auto()
    STAY_ORDER = auto()
    RULES_ORDER = auto()
    SLIP_OPINION = auto()
    OPINION_RELATING_TO_ORDERS = auto()


class Disposition(Enum):
    AFFIRMED = auto()
    AFFIRMED_IN_PART = auto()
    DISMISSED = auto()
    DISMISSED_AS_IMPROVIDENTLY_GRANTED = auto()
    DISMISSED_FOR_WANT_OF_JURISDICTION = auto()
    REMANDED = auto()
    REMANDED_IN_PART = auto()
    REVERSED = auto()
    REVERSED_IN_PART = auto()
    VACATED = auto()
    VACATED_IN_PART = auto()
    GRANTED = auto()
