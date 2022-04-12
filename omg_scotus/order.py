from __future__ import annotations

from enum import auto
from enum import Enum


class OrderType(Enum):
    ORDER_LIST = auto()
    MISCELLANEOUS_ORDER = auto()
    STAY_ORDER = auto()
    RULES_OF_APPELLATE_PROCEDURE = auto()
    RULES_OF_BANKRUPTCY_PROCEDURE = auto()
    RULES_OF_CIVIL_PROCEDURE = auto()
    RULES_OF_CRIMINAL_PROCEDURE = auto()

    @staticmethod
    def from_string(label: str) -> OrderType:
        """Return OrderType from string."""
        if label.upper() == 'MISCELLANEOUS ORDER':
            return OrderType.MISCELLANEOUS_ORDER
        elif label.upper() == 'ORDER LIST':
            return OrderType.ORDER_LIST
        elif label.upper() in ('STAY ORDERED', 'STAYS ORDERED'):
            return OrderType.STAY_ORDER
        elif label.upper() == 'RULES OF APPELLATE PROCEDURE':
            return OrderType.RULES_OF_APPELLATE_PROCEDURE
        elif label.upper() == 'RULES OF BANKRUPTCY PROCEDURE':
            return OrderType.RULES_OF_BANKRUPTCY_PROCEDURE
        elif label.upper() == 'RULES OF BANKRUPTCY PROCEDURE':
            return OrderType.RULES_OF_BANKRUPTCY_PROCEDURE
        elif label.upper() == 'RULES OF CRIMINAL PROCEDURE':
            return OrderType.RULES_OF_CRIMINAL_PROCEDURE
        else:
            raise NotImplementedError

    def __str__(self) -> str:
        """Return string representation of OrderType."""
        return self.name.replace('_', ' ')
