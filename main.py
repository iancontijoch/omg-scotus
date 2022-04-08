from datetime import datetime
from distutils.command.clean import clean
import bs4
import requests
import hashlib
from bs4 import BeautifulSoup
import dateparser
import pdfplumber
import re
from io import BytesIO
from typing import List, Optional, Tuple, Any, Union
from enum import Enum, auto


class OrderSection(Enum):
    CERTIORARI_SUMMARY_DISPOSITIONS = auto()
    ORDERS_IN_PENDING_CASES = auto()
    CERTIORARI_GRANTED = auto()
    CERTIORARI_DENIED = auto()
    HABEAS_CORPUS_DENIED = auto()
    MANDAMUS_DENIED = auto()
    REHEARINGS_DENIED = auto()


class Opinion():
    opinion_pg_ix: int
    op_pages: List[pdfplumber.pdf.Page]
    case_name: str
    petitioner: str
    respondent: str
    court_below: str
    author: str
    joiners: Optional[List[str]]
    text: str

    def __init__(self, opinion_pg_ix, pages) -> None:
        self.opinion_pg_ix = opinion_pg_ix

        self.op_page = pages[0]
        self.op_pages = pages

        self.petitioner, self.respondent = self.get_op_parties()
        self.case_name = self.get_case_name()
        self.court_below = self.get_op_court()
        self.author = self.get_opinion_author()
        self.court_below = self.get_op_court()
        self.text = self.get_opinion_text()

    def remove_opinion_header(self, p):
        """Return everything after header"""
        return '\n'.join(p.extract_text().split('\n')[3:])

    def get_opinion_author(self):
        """Returns author for opinion"""
        return self.op_page.extract_text().split('\n')[2].split()[2].replace(',', '')

    def get_op_parties(self) -> Tuple[str, str]:
        pattern = 'SUPREME COURT OF THE UNITED STATES \n(.*) v. (.*)ON PETITION'
        petitioner, respondent = re.compile(pattern, re.DOTALL).search(
            self.op_page.extract_text()).groups()
        petitioner = petitioner.replace('\n', '').replace('  ', ' ').strip()
        respondent = respondent.replace('\n', '').replace('  ', ' ').strip()

        return petitioner, respondent

    def get_op_court(self) -> str:
        pattern = '\nON.*TO THE (.*)No.'
        return re.compile(pattern, re.DOTALL).search(self.op_page.extract_text()).groups()[0].replace('\n', '').replace('  ', ' ').strip()

    def get_case_name(self):
        return ' v. '.join([self.petitioner, self.respondent])

    def get_opinion_text(self) -> str:
        text = ''.join([self.remove_opinion_header(p) for p in self.op_pages])
        return self.clean_opinion_text(text)

    def clean_opinion_text(self, text: str):
        """Clean up text"""
        #  remove newline whitespace
        text = re.sub(r'(\n* *\n)(\w+)', ' \\2', text)
        #  join hyphenated spillovers
        text = re.sub(r'(\w)(- )(\w)', '\\1\\3', text)
        #  remove extra spaces between punctuation.
        text = re.sub(r'([\.\,])  ', '\\1 ', text)
        #  remove newlines after header removal
        text = re.sub(r'( \n )(\w)', ' \2', text)
        #  remove hyphenated spillovers after header removal
        text = re.sub(r'(\w)-\n ', '\\1', text)
        #  remove newline when not followed by whitespace
        text = re.sub(r'  \n(\S)', ' \\1', text)

        return text


def latest_order(div: bs4.element.Tag):
    """Return latest order date and type."""
    spans = div.contents[1].find_all('span')

    date = spans[0].text.strip()
    date = dateparser.parse(date).strftime('%Y-%m-%d')
    order_type = spans[1].text.strip()
    order_url = f"https://www.supremecourt.gov/{spans[1].contents[0]['href']}"

    return (date, order_type, order_url)


def detect_opinions(pages: List[str]) -> int:
    for i, page in enumerate(pages):
        if page.extract_text().split('\n')[0][:10] == '  Cite as:':
            return i
    return

def is_opinion(lines: List[str]) -> bool:
    cond1 = lines[0][:10] == '  Cite as:' 
    if cond1: 
        try:
            cond2 = ''.join(lines)[0][-3:].strip() == '1'
        except IndexError:
            breakpoint()
        return cond1 and cond2
    return cond1

def is_order(lines: List[str]) -> bool:
    return lines[-1].isnumeric()

def add_begin_end_page_delimiter(pages: pdfplumber.PDF.pages) -> str:
    retv = []
    for page in pages:
        lines = page.extract_text().splitlines()
        if page.page_number == 1:
            retv.append('\nBEG_DOC\n')            
        retv.append('\nBEG_PAGE\n')
        retv.extend(lines)
        retv.append('\nEND_PAGE\n')
        if page.page_number == len(pages):
            retv.append('\nEND_DOC')
        
    return '\n'.join(retv)

def add_document_delimiters(pages: pdfplumber.PDF.pages) -> str:
    """Add BEG/END page, BEG/END orders, BEG/END opinions 
    delimiters for easy regex."""

    retv = []

    for i, page in enumerate(pages):
        lines = page.extract_text().splitlines()
        if page.page_number == 1 and is_order(lines):
            retv.append('BEG_ORDERS')
            retv.extend(lines)
        elif all((page.page_number < len(pages) -2, 
                 is_order(lines), 
                 is_opinion(pages[i+1].extract_text().splitlines()))):
            retv.extend(lines)
            retv.append('END_ORDERS')
            retv.append('BEG_OPINION')
        elif all(
            (page.page_number < len(pages) - 1,
            is_opinion(lines),
            is_opinion(pages[i+1].extract_text().splitlines()))
        ):   
            retv.append('END_OPINION')
            retv.append('BEG_OPINION')
            retv.extend(lines)
        elif page.page_number == len(pages) and is_order(lines):  # last page
            retv.extend(lines)
            retv.append('END_ORDERS')
        elif page.page_number == len(pages) and is_opinion(lines):
            retv.extend(lines)
            retv.append('END_OPINION')
    
    return '\n'.join(retv)        
        

def read_pdf(url: str) -> pdfplumber.PDF.pages:
    # url = "https://www.supremecourt.gov/orders/courtorders/032822zor_f2bh.pdf"
    rq = requests.get(url)
    with pdfplumber.open(BytesIO(rq.content)) as pdf:
        return pdf.pages


def get_case_num_and_name(txt: str) -> str:
    """Return case numbers/names XXX-XXXX   BOB v. ALICE or IN RE BOB for a given text."""

    #  123-4567 or 12A34  BOB v. ALICE or IN RE BOB
    pattern = r'(\d\d(?:-|\w)\d+)\s+([\w\,\.,\(,\),\', ]+V. [\w\,\.,\' ]+\n)|(\d\d(?:-|\w)\d+)\s+(IN RE [\w\,\.,\(,\), ]+) \n'
    matches = re.findall(pattern, txt)
    return matches


def print_section_cases(section_name: str, cases: Union[list, str]) -> None:
    """Prints the output for found cases"""
    num_cases = 0
    if isinstance(cases, list):
        num_cases = len(cases)
        cases = '\n'.join(['  '.join(m).strip() for m in cases])
    print(f"\n{section_name}: {num_cases} case{(num_cases > 1)*'s'}\n{'-'*72}\n{cases}\n{'-'*72}\n")


def get_section_cases(pages: pdfplumber.PDF.pages, section: OrderSection) -> None:
    """Return cases for each section of the Order List"""

    # stringify enum by replacing _ with space
    current_section = section.name.replace('_', ' ')
    txt = add_begin_end_page_delimiter(pages)
    # pattern to get the text in each section (w/ header ______ GRANTED/DENIED)
    try:
        if section is OrderSection.CERTIORARI_SUMMARY_DISPOSITIONS:
            # name separately because of the hyphens
            current_section = 'CERTIORARI -- SUMMARY DISPOSITIONS'
            # next section doesn't begin with ____ GRANTED/DENIED
            suffix = r'ORDERS +IN +PENDING +CASES'
        else:
            suffix = r'\w+ (DENIED|GRANTED)'
        # allow for multiple spaces between words (due to PDF import noise)
        pattern = fr'{current_section.replace(" ", " +")}(.*?){suffix}'
    except ValueError:  # this won't be the case anymore. Remove.
        #  TODO Detect whether section is the last section and modify regex to bookend it.
        # this only applies when there's an opinion. Need to fix.
        pattern = r'REHEARINGS DENIED(.*)END_PAGE:'
    try:
        section_txt = re.compile(pattern, re.DOTALL).search(txt).groups()[0]
        section_cases = get_case_num_and_name(section_txt)
    except AttributeError:  # section doesn't appear in Order List
        section_cases = "No Orders"
    finally:
        print_section_cases(current_section, section_cases)


def create_order_summary(pages: pdfplumber.PDF.pages, date: datetime.date, order_type: str) -> None:
    print("\n\n--------ORDER LIST SUMMARY--------")
    print(date)
    print(order_type)
    for section in OrderSection:
        get_section_cases(pages, section)
        

def get_opinions_from_orders(pages_str: str) -> str:
    """Return text for all opinions included in the order list."""
    retv = []
    pattern = r' +Cite as: +\d\d\d U. S. ____ \(\d\d\d\d\) +1'
    matches = re.finditer(pattern, pages_str)
    spans = [m.span() for m in matches]
    if len(spans) == 0:
        return None  # no opinions
    elif len(spans) == 1:  # match from end of match span to end of doc
        retv.append(pages_str[spans[0][0]:])
    else:  # match from end of span to beginning of next and then to end of doc
        for i, s in enumerate(spans):
            if i < len(spans) - 1:
                retv.append(pages_str[s[0]:spans[i+1][0]])
            else:
                retv.append(pages_str[s[0]:])  
    return retv


def main() -> int:
    url_orders = 'https://www.supremecourt.gov/orders/ordersofthecourt/21'

    page = requests.get(url_orders)
    soup = BeautifulSoup(page.text, 'html.parser')

    # div with current orders
    div_orders = soup.find_all('div', class_='column2')[
        0]  # there is one for "More" orders
    # to check for changes to order section
    hash = hashlib.sha256(div_orders.text.encode('utf-8')).hexdigest()

    # most recent order
    date, order_type, order_url = latest_order(div_orders)
    pgs = read_pdf(order_url)
    pgs = read_pdf(
        'https://www.supremecourt.gov/orders/courtorders/101821zor_4f14.pdf')  # buggy 
    create_order_summary(pgs, date, order_type)
    
    # add_document_delimiters(pgs)
    # pgs_txt = add_begin_end_page_delimiter(pgs)
    pgs_txt = '\n'.join([p.extract_text() for p in pgs])
    opinions = get_opinions_from_orders(pgs_txt)
    print(opinions)
    
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
