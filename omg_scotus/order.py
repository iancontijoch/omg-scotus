from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from enum import auto
from enum import Enum


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


class OrderCreator(ABC):

    date: str
    order_title: str

    @abstractmethod
    def factory_method(self) -> Order:
        pass

    def get_text(self) -> str:
        order = self.factory_method()
        result = f'Got text: {order.get_text()}.\n'
        result += f'Order type: {order.get_order_type()}'
        return result

    def set_date(self, date: str) -> OrderCreator:
        self.date = date
        return self

    def set_order_title(self, order_title: str) -> OrderCreator:
        self.order_title = order_title
        return self


class Order(ABC):
    date: str
    order_title: str

    def __init__(self, date: str, order_title: str) -> None:
        self.date = date
        self.order_title = order_title

    @abstractmethod
    def get_text(self) -> str:
        pass

    @abstractmethod
    def get_order_type(self) -> OrderType:
        pass
