from __future__ import annotations

import re


def get_case_num_and_name(txt: str | None) -> list[str]:
    """Return case numbers/names XXX-XXXX
    e.g. BOB v. ALICE or IN RE BOB"""

    #  123-4567, 12A34, 123, ORIG., IN RE .... BOB V. ALICE
    if txt is None:
        return ['No cases.']
    pattern = r'(\d+.*?\d|\d+.*?ORIG.)\s+(.*?V.*?$|IN RE.*?$)'
    matches = re.findall(pattern=pattern, string=txt, flags=re.M)
    return matches


# def print_section_cases(section_name: str, cases: list[str]) -> None:
#     """Prints the output for found cases"""
#     if cases[0] == 'No cases.':
#         num_cases = 0
#         cases_text = cases[0]
#     else:
#         num_cases = len(cases)
#         cases_text = '\n'.join(['  '.join(m).strip() for m in cases])
#     print(
#         f'\n{section_name}: {num_cases} case'
#         f"{(num_cases > 1 or num_cases == 0)*'s'}"
#         f"\n{'-'*72}\n{cases_text}\n{'-'*72}\n",
#     )


# def get_section_cases(
#     section_matches: dict[OrderListSectionType, str | None],
# ) -> None:
#     """Return cases for each section of the Order List"""

#     for section in OrderListSectionType:
#         section_text = section_matches[section]
#         section_cases = get_case_num_and_name(section_text)
#         print_section_cases(str(section), section_cases)


# def create_order_summary(
#     section_matches: dict[OrderListSectionType, str | None],
#     date: str,
#     order_type: OrderType,
#     order_text: str | None,
# ) -> None:
#     print('\n\n--------ORDER LIST SUMMARY--------')
#     print(date)
#     print(order_type)
#     if order_type in (
#         OrderType.RULES_OF_APPELLATE_PROCEDURE,
#         OrderType.RULES_OF_BANKRUPTCY_PROCEDURE,
#         OrderType.RULES_OF_CIVIL_PROCEDURE,
#         OrderType.RULES_OF_CRIMINAL_PROCEDURE,
#     ):
#         print(order_text)
#     else:
#         get_section_cases(section_matches)


# def get_page_indices(pages: pdfplumber.PDF.pages) -> list[tuple[int, int]]:
#     """Return start and end indices for each page."""
#     retv = []
#     start = 0
#     full_txt = ''.join([p.extract_text() for p in pages])
#     for pg in pages:
#         pg_len = len(pg.extract_text())
#         end = start + pg_len
#         assert full_txt[start:end] == pg.extract_text()
#         retv.append((start, end))
#         start += pg_len
#     return retv


def main() -> int:
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
