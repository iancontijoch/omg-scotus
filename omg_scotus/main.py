from __future__ import annotations

from omg_scotus.fetcher import Fetcher
from omg_scotus.parser import Parser


def main() -> int:
    fr = Fetcher.from_url(
        url=(
            'https://www.supremecourt.gov/'
            + 'orders/courtorders/022822zor_o759.pdf'
        ),
    )

    pr = Parser(fr.get_payload())
    ol = pr.get_object()

    print(ol)
    if ol.opinions:
        for opinion in ol.opinions:
            print(opinion.case_name)
            print(opinion.author)
            print(opinion.joiners)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
