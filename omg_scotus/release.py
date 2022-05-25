from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod

import pdfplumber

from omg_scotus._enums import Disposition
from omg_scotus._enums import DocumentType
from omg_scotus._enums import OrderSectionType
from omg_scotus._enums import RulesType
from omg_scotus.helpers import get_disposition_type
from omg_scotus.helpers import get_justices_from_sent
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import remove_hyphenation
from omg_scotus.helpers import remove_justice_titles
from omg_scotus.helpers import remove_notice
from omg_scotus.helpers import require_non_none
from omg_scotus.justice import JusticeTag
from omg_scotus.opinion import OpinionType
from omg_scotus.order import Rule
from omg_scotus.section import OrderSection
from omg_scotus.section import Section


class Release(ABC):
    """There are 3 types of releases by the Court:
    1. Slip Opinions
    2. Opinions Related to Orders
    3. Orders

    Each release has one or more documents.
    """
    date: str
    text: str
    url: str
    document_type: DocumentType
    documents: list[Document]

    def __init__(
        self, date: str, text: str, url: str,
        document_type: DocumentType,
    ) -> None:
        self.date = date
        self.text = text
        self.url = url
        self.document_type = document_type

    @abstractmethod
    def set_documents(self) -> None: pass

    @abstractmethod
    def compose_tweet(self) -> str:
        pass


class Document(ABC):
    """Any type of document included in a release."""
    text: str

    def __init__(self, text: str) -> None:
        self.text = text

    @abstractmethod
    def compose_tweet(self) -> str:
        pass


class OpinionDocument(Document, ABC):
    """Syllabi/Opinions/ORTO"""
    text: str
    author: JusticeTag
    joiners: list[JusticeTag] | None
    recusals: list[JusticeTag] | None
    _attribution_sentence: str

    @abstractmethod
    def get_attribution_sentence(self) -> str:
        pass

    @abstractmethod
    def assign_authorship(self) -> None:
        pass

    def set_recusals(self) -> None:
        pattern = r'(?s)(?<=\.)[^.!?]+\s+took\s+no\s+part\s.+$'
        recusals_sent = re.search(pattern, self._attribution_sentence)
        if recusals_sent:
            self.recusals = get_justices_from_sent(recusals_sent.group())

    def set_authorship(self, sent: str) -> None:
        author, *joiners = get_justices_from_sent(sent)
        self.author = author

        if joiners == [None]:  # If it happened to match a retired justice
            self.joiners = None
        elif joiners:
            self.joiners = joiners
        elif bool(re.search('unanimous', sent)):
            self.joiners = [
                j for j in JusticeTag
                if j not in (
                    self.author,
                    JusticeTag.PER_CURIAM,
                )
            ]
        else:
            self.joiners = None


class Syllabus(OpinionDocument):
    """Syllabus for a Slip Opinion."""

    def __init__(self, text: str) -> None:
        super().__init__(text=text)
        self._attribution_sentence = self.get_attribution_sentence()
        self.recusals = None
        self.set_recusals()
        self.assign_authorship()

    def get_attribution_sentence(self) -> str:
        """Return syllabus Justice alignment string.

        Search for a line starting with 3+ capital letters, followed
        by 'delivered' or 'announced' and grab through end of string.

        e.g. 'KAGAN, J. delivered the opinion of... in which ... joined.'
        """
        pattern = r'(?ms)^\s*[A-Z]{3,}\,\s+[CJ\s\.\,]+.+'
        retv = require_non_none(
            re.search(
                pattern,
                remove_notice(self.text),
            ),
        ).group()
        retv = remove_hyphenation(retv)
        retv = remove_justice_titles(retv)
        return retv

    def assign_authorship(self) -> None:
        """Parse first sentence of attribution sentence and set authorship."""
        # first sentence before the word 'filed'
        pattern = (
            r'(?s).*?(?=\.[^.!?]+filed|unanimous)'
        )
        sent = require_non_none(
            re.search(pattern, self._attribution_sentence),
        ).group()
        self.set_authorship(sent)

    def compose_tweet(self) -> str:
        pass


class Opinion(OpinionDocument):
    """Opinion belonging to a case."""
    type: OpinionType

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.recusals = None
        self._attribution_sentence = self.get_attribution_sentence()
        self.type = self.get_type(self._attribution_sentence)
        self.set_recusals()
        self.assign_authorship()

    def get_attribution_sentence(self) -> str:
        """Return sentence used to determine authorship and opinion type."""
        # matches first occurrence of Justice Name/Chief Justice/Curiam
        pattern = (
            r'(?ms)[^.!?\]\[]+(?:CHIEF\s+)*JUSTICE\s+[A-Z]{3,}.+?[a-z]+\.|'
            r'PER CURIAM'
        )
        return '. '.join(re.findall(pattern, self.text))

    def assign_authorship(self) -> None:
        sent = remove_hyphenation(self._attribution_sentence)
        sent = remove_justice_titles(sent)
        self.set_authorship(sent)

    def __str__(self) -> str:
        """Print Opinion Summary."""
        retv = f'\n{"-"*40}\nOPINION: {self.type.name}\n{"-"*40}'
        if self.type is OpinionType.STATEMENT:
            retv += f'\nAuthor:  {self.author.name}'
            return retv
        else:
            retv += f'\nAuthor:  {self.author.name}'
            if self.joiners:
                retv += (
                    f'\nJoined by:  '
                    f'{", ".join([s.name for s in self.joiners])}'
                )
        return retv

    @staticmethod
    def get_type(text: str) -> OpinionType:
        """Return opinion type."""
        STATEMENT_PATTERN = r'Statement\s+of\s+'
        DISSENT_PATTERN = r'(?:dissent)\w+\b'
        CONCURRENCE_PATTERN = r'(?:concurr)\w+\b'
        PLURALITY_PATTERN = r'delivered\s+an\s+opinion'
        MAJORITY_PATTERN = r'delivered\s+the\s+opinion'
        PER_CURIAM_PATTERN = r'PER CURIAM'

        d = {
            STATEMENT_PATTERN: OpinionType.STATEMENT,
            DISSENT_PATTERN: OpinionType.DISSENT,
            CONCURRENCE_PATTERN: OpinionType.CONCURRENCE,
            PLURALITY_PATTERN: OpinionType.PLURALITY,
            MAJORITY_PATTERN: OpinionType.MAJORITY,
            PER_CURIAM_PATTERN: OpinionType.PER_CURIAM,
        }

        text = remove_hyphenation(text)  # remove artifacts
        for k, v in d.items():
            if bool(re.search(k, text)):
                return v
        raise NotImplementedError

    def compose_tweet(self) -> str:
        pass


class OrderList(Document):
    title: str
    sections: list[Section]

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.title = self.get_title()
        self.sections = []
        self.set_sections()

    def get_title(self) -> str:
        """Return Order Title (first non space character through EOL."""
        pattern = r'\S.*\n'
        match = require_non_none(re.search(pattern, self.text))
        return remove_extra_whitespace(match.group())

    def set_sections(self) -> None:
        """Create and append OrderSections for OrderList."""
        # regex pattern looks text between section headers and between
        # last section header and EOF
        pattern = (
            r'(CERTIORARI +-- +SUMMARY +DISPOSITIONS*|ORDERS* +IN +PENDING '
            r'+CASES*|CERTIORARI +GRANTED|CERTIORARI +DENIED|HABEAS +CORPUS '
            r'+DENIED|MANDAMUS +DENIED|REHEARINGS* +DENIED)(.*?(?=CERTIORARI +'
            r'-- +SUMMARY +DISPOSITIONS*|ORDERS* +IN +PENDING +CASES*|CERTIORA'
            r'RI +GRANTED|CERTIORARI +DENIED|HABEAS +CORPUS +DENIED|MANDAMUS +'
            r'DENIED|REHEARINGS* +DENIED)|.*$)'
        )
        matches = re.finditer(
            pattern=pattern,
            string=self.text, flags=re.DOTALL,
        )

        for m in matches:
            section_title, section_content = remove_extra_whitespace(
                m.groups()[0],
            ), m.groups()[1]

            section = OrderSection(
                label=section_title,
                type=OrderSectionType.from_string(
                    section_title,
                ),
                text=section_content,
            )
            self.sections.append(section)

    def get_cases(self) -> list[str]:
        """Return all cases in an orderlist, regardless of section."""
        return [
            str(case.number) for section in self.sections
            for case in section.cases
        ]

    def compose_tweet(self) -> str:
        """Return tweetable summary."""
        return ''.join(s.compose_tweet() for s in self.sections)

    def __str__(self) -> str:
        """Return string representation of OrderList."""
        return '\n'.join([str(s) for s in self.sections])


class RuleOrder(Document):
    rules: list[Rule]
    pdf: pdfplumber.pdf.PDF
    title: str
    type: RulesType
    url: str

    def __init__(
        self, text: str, pdf: pdfplumber.pdf.PDF, title: str,
        url: str,
    ) -> None:
        super().__init__(text)
        self.pdf = pdf
        self.title = title
        self.url = url
        self.rules = []
        self.get_type()
        self.get_rules()

    def get_type(self) -> RulesType:
        if bool(re.search('bankruptcy', self.title.lower())):
            return RulesType.RULES_OF_BANKRUPTCY_PROCEDURE
        elif bool(re.search('appellate', self.title.lower())):
            return RulesType.RULES_OF_APPELLATE_PROCEDURE
        elif bool(re.search('civil', self.title.lower())):
            return RulesType.RULES_OF_CIVIL_PROCEDURE
        elif bool(re.search('criminal', self.title.lower())):
            return RulesType.RULES_OF_CRIMINAL_PROCEDURE
        else:
            raise NotImplementedError

    def get_bolded_text(self) -> str:
        """Get bolded text to find Rule # and Titles."""
        return ''.join(
            [
                c['text'] for p in self.pdf.pages[3:]
                for c in p.chars
                if c['fontname'] == 'TimesNewRomanPS-BoldMT'
            ],
        )

    def get_rules(self) -> None:
        """Create Rule from rule, title in bolded text."""
        # find text between ^Rule
        pattern = r'Rule\s+([\d\.]+\.)(.+?)(?=Rule|$)'
        for m in re.finditer(pattern, self.get_bolded_text()):
            number, title = m.groups()
            title = remove_extra_whitespace(title)
            title = re.sub(r'\s\*', '', title)  # elim asterisks
            rule = Rule(number=number, title=title)
            self.rules.append(rule)
        self.set_rule_content()

    def set_rule_content(self) -> None:
        """Set text of rule."""
        pattern = r'(?ms)^Rule\s+[\d\.]+\.(.+?)(?=^Rule|\Z)'
        for i, m in enumerate(re.finditer(pattern, self.text)):
            self.rules[i].contents = m.group()

    def __str__(self) -> str:
        retv = '\n'
        retv += f'{"~"*72}\n'
        retv += (
            f'{self.title.upper()}:  {len(self.rules)} rules '
            f'affected\n'
        )
        retv += f'{"~"*72}\n'
        retv += ''.join([str(r) for r in self.rules])
        return retv

    def compose_tweet(self) -> str:
        s = (
            f'NEW RULES:\n\n'
            f'{self.type}\n'
            f'{len(self.rules)} rule'
            f'{(len(self.rules) > 1 or len(self.rules) == 0)*"s"}'
            f'added.\n\n'
            f'{self.url}'
        )
        return s


class SlipOpinion(Release):
    """
    “Slip” opinions are the first version of the Court's opinions posted on
    this website. A “slip” opinion consists of the majority or principal
    opinion, any concurring or dissenting opinions written by the Justices,
    and a prefatory syllabus prepared by the Reporter's Office that summarizes
    the decision.
    """
    case_number: str
    petitioner: str
    repondent: str
    case_name: str
    lower_court: str
    holding: str
    disposition_text: str
    dipositions: list[Disposition]
    is_per_curiam: bool
    syllabus: Syllabus | None
    opinions: list[Opinion]
    majority_author: JusticeTag
    majority_joiners: list[JusticeTag] | None
    recusals: list[JusticeTag] | None

    def __init__(
        self, date: str, text: str, case_number: str, url: str,
        document_type: DocumentType, petitioner: str,
        respondent: str, lower_court: str, holding: str,
        disposition_text: str, is_per_curiam: bool,
    ) -> None:
        super().__init__(
            date=date, text=text, url=url,
            document_type=document_type,
        )
        self.case_number = case_number
        self.petitioner = petitioner
        self.respondent = respondent
        self.lower_court = lower_court
        self.holding = holding
        self.disposition_text = disposition_text
        self.is_per_curiam = is_per_curiam
        self.syllabus = None
        self.case_name = self.get_case_name()
        self.opinions = []
        self.set_documents()
        self.majority_author, self.majority_joiners = self.set_authorship()
        self.recusals = self.set_recusals()
        self.dispositions = get_disposition_type(self.disposition_text)

    def get_case_name(self) -> str:
        """Return {petitioner} v. {respondent} case format."""
        return ' v. '.join([self.petitioner, self.respondent])

    def set_authorship(self) -> tuple[JusticeTag, list[JusticeTag] | None]:
        """Set author and joiners for Slip Opinion."""
        if self.syllabus:
            return (self.syllabus.author, self.syllabus.joiners)
        elif self.is_per_curiam:
            return (JusticeTag.PER_CURIAM, [JusticeTag.PER_CURIAM])
        else:
            raise NotImplementedError

    def set_recusals(self) -> list[JusticeTag] | None:
        """Set recused Justices for Slip Opinion."""
        if self.syllabus:
            return self.syllabus.recusals
        elif self.is_per_curiam:
            return self.opinions[0].recusals
        else:
            raise NotImplementedError

    def set_documents(self) -> None:
        """Get Opinions"""
        pattern = (
            r'(?ms)(SUPREME COURT OF THE UNITED STATES.*?(?=SUPREME COURT OF '
            r'THE UNITED STATES))|(SUPREME COURT OF THE UNITED STATES .*)'
        )
        # this pattern searches for text betwen SCOTUS headers, as well as EOF.
        # joining because last match thru EOF is captured in group 2.
        doc_texts = [
            ''.join(f) for f in
            re.findall(pattern=pattern, string=self.text)
        ]

        if not self.is_per_curiam:
            self.syllabus = Syllabus(text=doc_texts[0])
            for doc_text in doc_texts[1:]:
                self.opinions.append(Opinion(text=doc_text))
        else:
            for doc_text in doc_texts:
                self.opinions.append(Opinion(text=doc_text))

    def __str__(self) -> str:
        """Print Slip Opinion Summary."""
        retv = (
            f"\n\n{'SLIP OPINION SUMMARY':~^{72}}\n"
            f'Link  {self.url}\n{"-"*72}\n'
            f'Case:  {self.case_name :>{5}}\n'
            f'No.:   {self.case_number :>{5}}\n'
        )
        if self.lower_court:
            retv += f'From:  {self.lower_court}\n'
        retv += f'Dispositions:\t{self.dispositions}\n'
        retv += (
            f'\n{"*"*72}\nHeld:\n\n\t{self.holding}\n\n{"*"*72}\n'
            f'Author:  {self.majority_author}\n'
        )
        if self.majority_joiners:
            retv += f'Joined by:  {self.majority_joiners}\n'
        if self.recusals:
            retv += f'Recused:  {self.recusals}\n'
        retv += '\n'.join([str(o) for o in self.opinions])  # print orders
        retv += '\n\nEND'
        return retv

    def compose_tweet(self) -> str:
        s = (
            f'OPINION:\n'
            f'{self.case_name :>{5}}\n\n'
            f'Held: {self.holding}\n\n'
            f'Author: {self.majority_author.name}'
            f'\n{self.url}'
        )
        return s


class OpinionRelatingToOrder(Release):
    """Opinions may be written by Justices to comment on the summary
    disposition of cases by orders, e.g., if a Justice wants to dissent from
    the denial of certiorari or concur in that denial.
    """
    case_number: str
    petitioner: str
    repondent: str
    case_name: str
    lower_court: str
    documents: list[Document]
    author: JusticeTag
    joiners: list[JusticeTag] | None

    def __init__(
        self, date: str, text: str, case_number: str, url: str,
        document_type: DocumentType, petitioner: str,
        respondent: str, lower_court: str,
    ) -> None:
        super().__init__(date, text, url, document_type)
        self.case_number = case_number
        self.petitioner = petitioner
        self.respondent = respondent
        self.case_name = self.set_case_name()
        self.lower_court = lower_court
        self.documents = []
        self.set_documents()
        self.author, self.joiners = self.set_authorship()

    def set_case_name(self) -> str:
        """Return {petitioner} v. {respondent} case format."""
        return ' v. '.join([self.petitioner, self.respondent])

    def set_documents(self) -> None:
        pattern = (
            r'(?ms)(SUPREME COURT OF THE UNITED STATES.*?(?=SUPREME COURT OF '
            r'THE UNITED STATES))|(SUPREME COURT OF THE UNITED STATES .*)'
        )
        # this pattern searches for text betwen SCOTUS headers, as well as EOF.
        # joining because last match thru EOF is captured in group 2.
        doc_texts = [
            ''.join(f) for f in
            re.findall(pattern=pattern, string=self.text)
        ]
        for doc_text in doc_texts:
            self.documents.append(Opinion(text=doc_text))

    def set_authorship(self) -> tuple[JusticeTag, list[JusticeTag] | None]:
        """Set author and joiners for Slip Opinion."""
        if self.documents:
            doc = self.documents[0]
            if isinstance(doc, Opinion):
                return (doc.author, doc.joiners)
            else:
                raise ValueError
        else:
            raise ValueError('ORTO missing document(s).')

    def __str__(self) -> str:
        """Return string representation of OrderList."""
        s = f'\n{self.case_number}\n{self.date}\n\n'
        s += f"{'OPINION RELATING TO ORDER SUMMARY':~^{72}}"
        s += f'\nLink  {self.url}'
        s += '\n'.join([str(o) for o in self.documents])  # print orders
        return s

    def compose_tweet(self) -> str:
        try:
            doc = self.documents[0]
        except IndexError:
            raise
        if not isinstance(doc, Opinion):
            raise ValueError
        s = (
            f'OPINION RELATING TO ORDER:\n\n'
            f'{self.case_name}\n'
            f'{doc.type.name}\n\n'
            f'Author: {self.author.name}\n'
            f'{self.url}'
        )
        return s


class OrderRelease(Release):
    """The vast majority of cases filed in the Supreme Court are disposed of
    summarily by unsigned orders. Such an order will, for example, deny a
    petition for certiorari without comment. Regularly scheduled lists of
    orders are issued on each Monday that the Court sits, but "miscellaneous"
    orders may be issued in individual cases at any time. """
    title: str
    document: Document

    def __init__(
        self, date: str, text: str, url: str, title: str,
        pdf: pdfplumber.pdf.PDF, document_type: DocumentType,
    ) -> None:
        super().__init__(
            date=date, text=text, url=url,
            document_type=document_type,
        )
        self.title = title
        self.pdf = pdf
        self.order = None
        self.set_documents()

    def set_documents(self) -> None:
        if self.document_type in (
            DocumentType.ORDER_LIST,
            DocumentType.MISCELLANEOUS_ORDER,
        ):
            self.document = OrderList(self.text)
        elif self.document_type is DocumentType.RULES_ORDER:
            self.document = RuleOrder(
                self.text,
                self.pdf, self.title, self.url,
            )

    def __str__(self) -> str:
        """Return string representation of OrderList."""
        s = f'\n{self.title}\n{self.date}\n\n'
        s += f"{'ORDER SUMMARY':~^{72}}"
        s += f'\nLink  {self.url}'
        s += f'{self.document}'
        return s

    def compose_tweet(self) -> str:
        """Return tweetable summary."""
        s = f'{self.title} ({self.date})\n'
        s += f'{self.document.compose_tweet()}\n\n'
        s += f'{self.url}'
        return s
