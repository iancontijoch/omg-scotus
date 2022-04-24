from __future__ import annotations

from typing import Any

from omg_scotus.fetcher import Fetcher
from omg_scotus.parser import Parser


def get_order(id: str) -> Any:
    url = (
        f'https://www.supremecourt.gov/'
        f'orders/courtorders/{id}.pdf'
    )
    fr = Fetcher.from_url(url)
    pr = Parser(fr.get_payload())
    return pr.get_object()


def get_opinion(id: str) -> Any:
    url = (
        f'https://www.supremecourt.gov/'
        f'opinions/{id}.pdf'
    )
    fr = Fetcher.from_url(url)
    pr = Parser(fr.get_payload())
    return pr.get_object()


def main() -> int:

    debug_orders = [
        # get_order('050820zr_097c'),  # stay
        # get_order('040422zor_4f14'),  # orderlist no op.
        # get_order('041822zor_19m2'),  # OL 1 op.
        # get_order('022822zor_o759'),  # OL 2+ op.
        # get_order('041822zr_11o2'),  # misc. order (type orderlist)
        # get_opinion('20pdf/19-1257_new_4g15'),
        # get_opinion('21pdf/20-303_6khn'),
        # get_opinion('21pdf/21a244_hgci'),  # PC
        get_opinion('21pdf/20-480_b97c'),
        # get_opinion('21pdf/143orig_1qm1'),  # orig

    ]

    # order = Parser(Fetcher(Stream.OPINIONS).get_payload()).get_object()
    # debug_orders = [order]

    for doc in debug_orders:
        for order in doc:
            print(order)
        # if hasattr(order, )
        # print(order.get_cases())

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
