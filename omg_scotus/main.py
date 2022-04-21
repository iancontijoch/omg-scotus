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


def main() -> int:

    debug_orders = [
        get_order('050820zr_097c'),  # stay
        get_order('040422zor_4f14'),  # orderlist no op.
        get_order('041822zor_19m2'),  # OL 1 op.
        get_order('022822zor_o759'),  # OL 2+ op.
        get_order('041822zr_11o2'),  # misc. order (type orderlist)
    ]

    order = debug_orders[0]

    for order in debug_orders:
        print(order)
        if hasattr(order, 'opinions'):
            if order.opinions:
                for opinion in order.opinions:
                    print(opinion)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
