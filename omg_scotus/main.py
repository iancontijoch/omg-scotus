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

    stay_order = get_order('050820zr_097c')
    orderlist_no_opinion = get_order('040422zor_4f14')
    orderlist_w_one_opinion = get_order('041822zor_19m2')
    orderlist_w_mult_opinions = get_order('022822zor_o759')

    debug_orders = (
        stay_order,
        orderlist_no_opinion,
        orderlist_w_one_opinion,
        orderlist_w_mult_opinions,
    )

    for order in debug_orders:
        print(order)
        if hasattr(order, 'opinions'):
            if order.opinions:
                for opinion in order.opinions:
                    print(opinion)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
