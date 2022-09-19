import pickle
from datetime import datetime

import spacy
from spacy.language import Language

from omg_scotus.fetcher import Fetcher
from omg_scotus.fetcher import Stream
from omg_scotus.helpers import get_term_year
from omg_scotus.justice import create_court
from omg_scotus.parser import Parser


def add_custom_rules_to_nlp(nlp: Language) -> None:
    # Add custom rules to nlp
    ruler = nlp.get_pipe('attribute_ruler')

    justices = (
        str.upper(justice.last_name)
        for justice in create_court(current=True)
    )

    patterns = [
        [{'TEXT': justice}] for justice in justices
    ]
    attrs = {'DEP': 'nsubj'}
    ruler.add(patterns=patterns, attrs=attrs)


def main() -> int:

    nlp = spacy.load('en_core_web_lg')
    add_custom_rules_to_nlp(nlp)
    retv = {}
    # scotus dockets start in 2003
    for term_year in range(
        11,
        int(get_term_year(datetime.today().date())) + 1,
    ):
        docs = []
        t_year = str(term_year).zfill(2)
        print(f'Preparing download for {term_year=}')
        payloads = Fetcher(
            Stream.SLIP_OPINIONS,
            term_year=t_year,
        ).get_payload()
        for i, payload in enumerate(payloads):
            doc = Parser(payload, nlp).get_object()
            print(f'Appended {i+1}/{len(payloads)} docs.')
            docs.append(doc)
        retv[t_year] = docs
        print(f'Term year {t_year} finished')

    with open('data/all_opinions.pkl', 'wb') as handle:
        pickle.dump(retv, handle, protocol=pickle.HIGHEST_PROTOCOL)

    print('All opinion data pickled successfully.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
