from __future__ import annotations

import argparse
from typing import Any
from typing import Sequence

import spacy
from spacy.language import Language

from omg_scotus.fetcher import Fetcher
from omg_scotus.fetcher import Stream
from omg_scotus.parser import Parser
from omg_scotus.tweet import TwitterPublisher


def get_doc(id: str, stream: Stream, nlp: Language) -> Any:
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
    pr = Parser(msg=fr.get_payload()[0], nlp=nlp)
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


def main(argv: Sequence[str] | None = None) -> int:

    nlp = spacy.load('en_core_web_sm')

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
    parser.add_argument(
        '-t', '--tweet', action='store_true',
    )

    # Parse args
    args = parser.parse_args(argv)
    if args.orders:
        option = args.orders
    elif args.slip:
        option = args.slip
    elif args.relating:
        option = args.relating
    else:
        raise NotImplementedError

    # Fetch and parse releases
    if option:
        if option == 'nourl':
            docs = []
            payloads = Fetcher(get_stream(args), date=None).get_payload()
            for payload in payloads:
                doc = Parser(payload, nlp).get_object()
                docs.append(doc)
        else:
            docs = [get_doc(option, get_stream(args), nlp)]

    tp = TwitterPublisher()

    # Print releases and tweet out summaries.
    for doc in docs:
        if isinstance(doc, list):
            for subdoc in doc:
                print(subdoc)
                if args.tweet:
                    tp.post_tweet(text=subdoc.compose_tweet())
        else:
            print(doc)
            if args.tweet:
                tp.post_tweet(text=doc.compose_tweet())

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
