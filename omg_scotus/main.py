from __future__ import annotations

import argparse
from typing import Any

from omg_scotus.fetcher import Fetcher
from omg_scotus.fetcher import Stream
from omg_scotus.parser import Parser


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
    pr = Parser(fr.get_payload()[0])
    return pr.get_object()


def get_stream(args: Any) -> Stream:
    if args.orders:
        return Stream.ORDERS
    elif args.slip:
        return Stream.SLIP_OPINIONS
    elif args.relating:
        return Stream.OPINIONS_RELATING_TO_ORDERS
    else:
        raise NotImplementedError


def main() -> int:

    parser = argparse.ArgumentParser(description='Run omg-scotus!')

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-o', '--orders', nargs='?', const='nourl',
        help='fetch latest order(s)',
    )
    group.add_argument(
        '-s', '--slip', nargs='?', const='nourl',
        help='fetch latest slip opinion',
    )
    group.add_argument(
        '-r', '--relating', nargs='?', const='nourl',
        help='fetch latest opinion relating to orders.',
    )

    args = parser.parse_args()
    if args.orders:
        option = args.orders
    elif args.slip:
        option = args.slip
    elif args.relating:
        option = args.relating
    else:
        raise NotImplementedError

    if option:
        if option == 'nourl':
            debug_docs = []
            payloads = Fetcher(get_stream(args), date='5/16/22').get_payload()
            for payload in payloads:
                order = Parser(payload).get_object()
                debug_docs.append(order)
        else:
            debug_docs = [get_doc(option, get_stream(args))]

    # debug_orders = [
    #     # get_doc('050820zr_097c', Stream.ORDERS),  # stay
    #     # get_doc('040422zor_4f14', Stream.ORDERS),  # orderlist no op.
    #     # get_doc('041822zor_19m2', Stream.ORDERS),  # OL 1 op.
    #     # get_doc('022822zor_o759', Stream.ORDERS),  # OL 2+ op.
    #     # get_doc('041822zr_11o2', Stream.ORDERS),  # misc. order OL
    #     # get_doc('20pdf/19-1257_new_4g15', Stream.SLIP_OPINIONS),
    #     # get_doc('21pdf/20-303_6khn', Stream.SLIP_OPINIONS),
    #     # get_doc('21pdf/21a244_hgci', Stream.SLIP_OPINIONS),  # PC
    #     # get_doc('21pdf/20-480_b97c', Stream.SLIP_OPINIONS),  # reg opinion
    #     # get_doc('21pdf/143orig_1qm1', Stream.SLIP_OPINIONS),  # orig
    #     # get_doc('20pdf/22o65_dc8e', stream=Stream.SLIP_OPINIONS) #orig-mult
    #     # get_doc('21pdf/21-145_2b82',
    #     #         Stream.OPINIONS_RELATING_TO_ORDERS)  # 2 opinions
    #     # get_doc('frbk22_cb8e', stream=Stream.ORDERS),  # Rules of Appellate
    # ]

    for doc in debug_docs:
        if isinstance(doc, list):
            for subdoc in doc:
                print(subdoc)
        else:
            print(doc)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
