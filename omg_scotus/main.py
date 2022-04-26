from __future__ import annotations

from typing import Any

from omg_scotus.fetcher import Fetcher
from omg_scotus.fetcher import Stream
from omg_scotus.parser import Parser


# def get_doc(id: str) -> Any:
#     url = (
#         f'https://www.supremecourt.gov/'
#         f'orders/courtorders/{id}.pdf'
#     )
#     fr = Fetcher.from_url(url)
#     pr = Parser(fr.get_payload())
#     return pr.get_object()

def get_doc(id: str, stream: Stream) -> Any:
    if stream is Stream.ORDERS:
        url = (
            f'https://www.supremecourt.gov/'
            f'orders/courtorders/{id}.pdf'
        )
    elif stream in (Stream.SLIP_OPINIONS, Stream.OPINIONS_RELATING_TO_ORDERS):
        url = (
            f'https://www.supremecourt.gov/'
            f'opinions/{id}.pdf'
        )
    else:
        raise NotImplementedError
    fr = Fetcher.from_url(url, stream)
    pr = Parser(fr.get_payload())
    return pr.get_object()


def main() -> int:

    debug_orders = [
        # get_doc('050820zr_097c', Stream.ORDERS),  # stay
        # get_doc('040422zor_4f14', Stream.ORDERS),  # orderlist no op.
        # get_doc('041822zor_19m2', Stream.ORDERS),  # OL 1 op.
        # get_doc('022822zor_o759', Stream.ORDERS),  # OL 2+ op.
        # get_doc('041822zr_11o2', Stream.ORDERS),  # misc. order OL
        # get_doc('20pdf/19-1257_new_4g15', Stream.SLIP_OPINIONS),
        # get_doc('21pdf/20-303_6khn', Stream.SLIP_OPINIONS),
        # get_doc('21pdf/21a244_hgci', Stream.SLIP_OPINIONS),  # PC
        # get_doc('21pdf/20-480_b97c', Stream.SLIP_OPINIONS),  # reg opinion
        # get_doc('21pdf/143orig_1qm1', Stream.SLIP_OPINIONS),  # orig

    ]

    order = Parser(
        Fetcher(Stream.OPINIONS_RELATING_TO_ORDERS).get_payload(),
    ).get_object()
    debug_orders = [order]

    for doc in debug_orders:
        for order in doc:
            print(order)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
