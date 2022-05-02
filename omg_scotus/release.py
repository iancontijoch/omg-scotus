from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod

from omg_scotus._enums import Disposition
from omg_scotus.helpers import get_disposition_type
from omg_scotus.helpers import get_justices_from_sent
from omg_scotus.helpers import remove_hyphenation
from omg_scotus.helpers import remove_justice_titles
from omg_scotus.helpers import remove_notice
from omg_scotus.helpers import require_non_none
from omg_scotus.justice import JusticeTag
from omg_scotus.opinion import OpinionType


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
    documents: list[Document]

    def __init__(self, date: str, text: str, url: str) -> None:
        self.date = date
        self.text = text
        self.url = url

    @abstractmethod
    def set_documents(self) -> None: pass


class Document(ABC):
    """Any type of document included in a release."""
    text: str

    def __init__(self, text: str) -> None:
        self.text = text
    pass


class OpinionDocument(Document, ABC):
    """Syllabi/Opinions/Opinions"""
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
        if joiners:
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
            r'(?s).*?(?=\.[^.!?]+filed)'
        )
        sent = require_non_none(
            re.search(pattern, self._attribution_sentence),
        ).group()
        self.set_authorship(sent)


class Opinion(OpinionDocument):
    """Opinion belonging to a case."""
    text: str
    author: JusticeTag
    joiners: list[JusticeTag] | None
    type: OpinionType
    _attribution_sentence: str

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self._attribution_sentence = self.get_attribution_sentence()
        self.recusals = None
        self.set_recusals()
        self.assign_authorship()
        self.type = self.get_type(self._attribution_sentence)

    def get_attribution_sentence(self) -> str:
        """Return sentence used to determine authorship and opinion type."""
        # matches first occurrence of Justice Name/Chief Justice/Curiam
        pattern = (
            r'(?ms)(?:CHIEF\s+)*JUSTICE\s+[A-Z]{3,}.+?[a-z]+\.|PER CURIAM'
        )
        # return require_non_none(re.search(pattern, self.text)).group()
        return '. '.join(re.findall(pattern, self.text))

    def assign_authorship(self) -> None:
        sent = remove_hyphenation(self._attribution_sentence)
        sent = remove_justice_titles(sent)
        self.set_authorship(sent)

    def __str__(self) -> str:
        """Print Opinion Summary."""
        retv = (
            f'\n{"-"*40}\nOPINION: {self.type}\n{"-"*40}'
            f'\nAuthor:  {self.author}'
        )
        if self.joiners:
            retv += f'\nJoined by:  {self.joiners}'
        return retv

    @staticmethod
    def get_type(text: str) -> OpinionType:
        """Return opinion type."""
        STATEMENT_PATTERN = r'writ of certiorari is denied\.\s+Statement'
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


class CaseOrder(Document):
    """"""
    pass


class RuleOrder(Document):
    """"""
    pass


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
        petitioner: str, respondent: str, lower_court: str,
        holding: str, disposition_text: str, is_per_curiam: bool,
    ) -> None:
        super().__init__(date, text, url)
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
        if self.syllabus:
            return (self.syllabus.author, self.syllabus.joiners)
        elif self.is_per_curiam:
            return (JusticeTag.PER_CURIAM, [JusticeTag.PER_CURIAM])
        else:
            raise NotImplementedError

    def set_recusals(self) -> list[JusticeTag] | None:
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


class OpinionRelatingToOrder(Release):
    """Opinions may be written by Justices to comment on the summary
    disposition of cases by orders, e.g., if a Justice wants to dissent from
    the denial of certiorari or concur in that denial.
    """
    case_number: str
    petitioner: str
    repondent: str
    lower_court: str
    opinions: list[Opinion]

    pass


class OrderRelease(Release):
    """The vast majority of cases filed in the Supreme Court are disposed of
    summarily by unsigned orders. Such an order will, for example, deny a
    petition for certiorari without comment. Regularly scheduled lists of
    orders are issued on each Monday that the Court sits, but "miscellaneous"
    orders may be issued in individual cases at any time. """
    orders: list[CaseOrder | RuleOrder]
