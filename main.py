from distutils.command.clean import clean
import bs4
import requests
import hashlib
from bs4 import BeautifulSoup
import dateparser
import pdfplumber
import re
from io import BytesIO
from typing import List, Optional, Tuple, Any


class Opinion():
    opinion_pg_ix = int
    op_pages: Any
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
        petitioner, respondent = re.compile(pattern, re.DOTALL).search(self.op_page.extract_text()).groups()
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
        text = re.sub(r'([\.\,])  ', '\\1 ' , text)
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


def detect_opinions(pages: List[str]):
    for i, page in enumerate(pages):
        if page.extract_text().split('\n')[0][:10] == '  Cite as:':
            return i
    return


def read_pdf(url):
    url = "https://www.supremecourt.gov/orders/courtorders/022222zor_bq7d.pdf"
    rq = requests.get(url)

    with pdfplumber.open(BytesIO(rq.content)) as pdf:
        opinion_pg = detect_opinions(pdf.pages)
        if opinion_pg:
            op = Opinion(opinion_pg_ix=opinion_pg, pages=pdf.pages[opinion_pg:])
            order_pgs = pdf.pages[:opinion_pg]
            txt = ''.join([p.extract_text() for p in order_pgs])
            
            pattern = r'CERTIORARI GRANTED(.*)CERTIORARI DENIED'
            try:
                granted_txt = re.compile(pattern, re.DOTALL).search(txt).groups()[0]
                pattern = r'(\d+-\d+)\s+([\w\s\,\.,\(,\), ]+V. [\w\,\. ]+\n)'  # identify XX-XXX CASE NAME
                cases = re.findall(pattern, granted_txt)
                cases_list = '\n'.join(['  '.join(c).strip() for c in cases])
                
                print(f"\n\nCases Granted:\n{'-'*72}")
                print(cases_list)
                print('-'*72)
                print('\n')
            except AttributeError:
                print("No cert grants.")
        else:
            order_pgs = pdf.pages
            print(''.join([p.extract_text() for p in order_pgs]))   
        return 0

def main() -> int:

    url_orders = 'https://www.supremecourt.gov/orders/ordersofthecourt/21'

    page = requests.get(url_orders)
    soup = BeautifulSoup(page.text, 'html.parser')

    # div with current orders
    div_orders = soup.find_all('div', class_='column2')[
        0]  # there is one for "More" orders
    hash = hashlib.sha256(div_orders.text.encode('utf-8')).hexdigest()

    # most recent order
    date, order_type, order_url = latest_order(div_orders)
    print(read_pdf(order_url))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
