from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod

import pdfplumber
import spacy
from spacy.language import Language

from omg_scotus._enums import Disposition
from omg_scotus._enums import DocumentType
from omg_scotus._enums import OrderSectionType
from omg_scotus._enums import RulesType
from omg_scotus.helpers import add_padding_to_periods
from omg_scotus.helpers import get_disposition_type
from omg_scotus.helpers import get_justices_from_sent
from omg_scotus.helpers import remove_between_parentheses
from omg_scotus.helpers import remove_extra_whitespace
from omg_scotus.helpers import remove_hyphenation
from omg_scotus.helpers import remove_justice_titles
from omg_scotus.helpers import remove_notice
from omg_scotus.helpers import remove_trailing_spaces_within_parentheses
from omg_scotus.helpers import require_non_none
from omg_scotus.justice import create_court
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
    nlp: Language

    def __init__(
        self, date: str, text: str, url: str,
        document_type: DocumentType, nlp: Language,
    ) -> None:
        self.date = date
        self.text = remove_trailing_spaces_within_parentheses(text)
        self.url = url
        self.document_type = document_type
        self.nlp = nlp

    @abstractmethod
    def set_documents(self) -> None: pass

    @abstractmethod
    def compose_tweet(self) -> str:
        pass


class Document(ABC):
    """Any type of document included in a release."""
    text: str
    nlp: Language
    document_type: DocumentType

    def __init__(
        self,
        text: str,
        nlp: Language,
        document_type: DocumentType,
    ) -> None:
        self.text = text
        self.nlp = nlp
        self.document_type = document_type

    @abstractmethod
    def compose_tweet(self) -> str:
        pass


class OpinionDocument(Document, ABC):
    """Syllabi/Opinions/ORTO"""
    text: str
    document_type: DocumentType
    nlp: Language
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
    alignment_tuple: list[tuple[OpinionType, str, list[str]]]

    def __init__(
        self, text: str, nlp: Language,
        document_type: DocumentType,
    ) -> None:
        super().__init__(text=text, nlp=nlp, document_type=document_type)
        self._attribution_sentence = self.get_attribution_sentence()
        self.get_alignment_tuple()
        self.recusals = None
        self.set_recusals()
        self.assign_authorship()

    def get_attribution_sentence(self) -> str:
        """Return syllabus Justice alignment string.

        Search for a line starting with 3+ capital letters, followed
        by 'delivered' or 'announced' and grab through end of string.

        e.g. 'KAGAN, J. delivered the opinion of... in which ... joined.'
        """
        # pattern = r'(?ms)^\s*[A-Z]{4,}\,\s+[CJ\s\.\,]+.+'
        pattern = r'(?ms)\b[A-Z]{4,}\,\s(C\. |J)*J\..*'
        string = remove_extra_whitespace(
            remove_notice(
                remove_hyphenation(
                    remove_between_parentheses(self.text),
                ),
            ),
        )
        retv = require_non_none(
            re.search(
                pattern,
                string,
            ),
        ).group()
        retv = remove_hyphenation(retv)
        retv = remove_justice_titles(retv)
        retv = add_padding_to_periods(retv)
        return retv

    def get_alignment_tuple(
        self,
    ) -> list[tuple[OpinionType, JusticeTag | None, list[JusticeTag] | None]]:
        doc = self.nlp(self._attribution_sentence)
        return self.alignment_summary(doc)

    @staticmethod
    def alignment_summary(
        doc: spacy.tokens.Doc,
    ) -> list[tuple[OpinionType, JusticeTag | None, list[JusticeTag] | None]]:
        """Return tuples indicating majority author, majority joiners, and
        concurrences/dissents"""
        majority_author, majority_joiners, contributor, contributor_joiners = (
            None, None, None, None,
        )

        opinions = []
        op_type = None

        court = create_court(current=False)

        for sent in doc.sents:
            if 'filed' not in sent.text:  # majority opinion
                for token in sent:
                    if token.text == 'joined' and majority_joiners is None:
                        majority_joiners = [
                            JusticeTag.from_string(t.text)
                            for t in token.subtree
                            if t.is_upper and len(t) > 3 and t.dep_ != 'pobj'
                        ]
                    elif majority_author is None and token.text in (
                            'delivered', 'announced',
                    ):
                        majority_author = [
                            JusticeTag.from_string(t.text)
                            for t in token.children if t.dep_ == 'nsubj'
                        ][0]
                if (
                    'all other Members' in sent.text
                    or 'unanimous' in sent.text
                ):
                    majority_joiners = [
                        j.tag for j in court
                        if j.tag != majority_author
                    ]
                opinions.append((
                    OpinionType.MAJORITY, majority_author,
                    majority_joiners,
                ))
            else:
                contributor, contributor_joiners = None, None
                if 'concurring' in sent.text and 'dissenting' in sent.text:
                    op_type = OpinionType.CONCURRENCE_AND_DISSENT
                elif 'concurring' in sent.text:
                    op_type = OpinionType.CONCURRENCE
                elif 'dissenting' in sent.text:
                    op_type = OpinionType.DISSENT
                else:
                    raise NotImplementedError

                if 'opinions' in sent.text and 'joined' not in sent.text:
                    # ALITO and KAVANAUGH filed opinions concurring in the
                    # judgment in part and dissenting in part.
                    contributors = [t for t in sent if t.pos_ == 'PROPN']
                    for c in contributors:
                        opinions.append(
                            (op_type, JusticeTag.from_string(c.text), None),
                        )
                else:
                    for token in sent:
                        if token.text == 'filed':
                            contributor = [
                                JusticeTag.from_string(t.text)
                                for t in token.children if t.dep_ == 'nsubj'
                            ][0]
                        elif token.text == 'joined':
                            contributor_joiners = [
                                JusticeTag.from_string(t.text)
                                for t in token.subtree
                                if (
                                    t.is_upper and len(t) > 3
                                    and t.dep_ != 'pobj'
                                )
                            ]
                    opinions.append(
                        (op_type, contributor, contributor_joiners),
                    )

        return opinions

    def assign_authorship(self) -> None:
        """Parse first sentence of attribution sentence and set authorship."""
        # first sentence before the word 'filed'
        pattern = (
            r'(?s).*?(?=\.[^.!?]+filed|unanimous|case|Parts*'
            r'|judgment|except|all\s+but)'
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
    nlp: Language

    def __init__(
        self,
        text: str,
        nlp: Language,
        document_type: DocumentType,
    ) -> None:
        super().__init__(text, nlp, document_type)
        self.recusals = None
        self._attribution_sentence = self.get_attribution_sentence()
        self.type = self.get_type(self._attribution_sentence)
        self.set_recusals()
        self.assign_authorship()

    def get_attribution_sentence(self) -> str:
        """Return sentence used to determine authorship and opinion type."""
        # matches first sentence after "YYYY]", disregards J. title
        retv: str = ''
        pattern = (
            r'(?ms)(?<=[^\[]\d{4}\])[^.!?\]\[]+(?:J\.)*[^.!?\]\[]+\.'
        )

        # PER CURIAMS do not have square brackets -- oops, they can in body
        try:
            retv = re.findall(pattern, self.text)[0]
        except IndexError:
            try:
                retv = re.findall(
                    r'PER\s+CURIAM|DECREE|ORDER\s+AND\s+JUDGMENT', self.text,
                )[0]
            except IndexError:
                try:
                    # get first sentence after brackets
                    if (
                        self.document_type
                        is DocumentType.OPINION_RELATING_TO_ORDERS
                    ):
                        pattern = (
                            r'(?ms)(?<=\d{4})[^.!?\]\[]+\.'
                            r'([^.!?\]\[]+\.)'
                        )
                        retv = re.findall(pattern, self.text)[0]
                    elif self.document_type is DocumentType.SLIP_OPINION:
                        pattern = r'(?ms)(?<=\d{4})[^.!?\]\[\d]+\.'
                        retv = re.findall(pattern, self.text)[0]
                    else:
                        raise NotImplementedError
                except IndexError:
                    raise
        finally:
            return retv

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
        DECREE_PATTERN = r'(?i)DECREE|ORDER\s+AND\s+JUDGMENT'

        d = {
            STATEMENT_PATTERN: OpinionType.STATEMENT,
            DISSENT_PATTERN: OpinionType.DISSENT,
            CONCURRENCE_PATTERN: OpinionType.CONCURRENCE,
            PLURALITY_PATTERN: OpinionType.PLURALITY,
            MAJORITY_PATTERN: OpinionType.MAJORITY,
            PER_CURIAM_PATTERN: OpinionType.PER_CURIAM,
            DECREE_PATTERN: OpinionType.DECREE,
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

    def __init__(
        self, text: str,
        nlp: Language,
        document_type: DocumentType,
    ) -> None:
        super().__init__(text, nlp=nlp, document_type=document_type)
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
        url: str, document_type: DocumentType,
    ) -> None:
        super().__init__(text, nlp=self.nlp, document_type=document_type)
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
    title: str
    petitioner: str
    repondent: str
    case_name: str
    lower_court: str
    holding: str
    disposition_text: str
    dipositions: list[Disposition]
    is_per_curiam: bool
    is_decree: bool
    syllabus: Syllabus | None
    opinions: list[Opinion]
    majority_author: JusticeTag
    majority_joiners: list[JusticeTag] | None
    recusals: list[JusticeTag] | None
    nlp: Language
    score: str

    def __init__(
        self, date: str, text: str, case_number: str, title: str, url: str,
        document_type: DocumentType, petitioner: str,
        respondent: str, lower_court: str, holding: str,
        disposition_text: str, is_per_curiam: bool, is_decree: bool,
        nlp: Language,
    ) -> None:
        super().__init__(
            date=date, text=text, url=url,
            document_type=document_type,
            nlp=nlp,
        )
        self.case_number = case_number
        self.title = title
        self.petitioner = petitioner
        self.respondent = respondent
        self.lower_court = lower_court
        self.holding = holding
        self.disposition_text = disposition_text
        self.is_per_curiam = is_per_curiam
        self.is_decree = is_decree
        self.syllabus = None
        self.case_name = self.get_case_name()
        self.opinions = []
        self.set_documents()
        # self.majority_author, self.majority_joiners = self.set_authorship()
        self.alignment = self.get_alignment_summary()
        self.score = self.get_alignment_score()
        self.recusals = self.set_recusals()
        self.dispositions = get_disposition_type(self.disposition_text)

    def get_case_name(self) -> str:
        """Return {petitioner} v. {respondent}/In Re {respdt} for mandamus."""
        if self.respondent:
            return ' v. '.join([self.petitioner, self.respondent])
        else:
            return f'In Re {self.petitioner}'

    def get_alignment_summary(
        self,
    ) -> tuple[list[JusticeTag], list[JusticeTag | None], str, list[str]]:
        if self.syllabus:
            majority_opinion, *opinions = self.syllabus.get_alignment_tuple()
        elif self.is_decree:
            majority_opinion, opinions = [
                (
                    OpinionType.DECREE,
                    JusticeTag.PER_CURIAM,
                    None,
                ), [],
            ]
        else:
            majority_opinion, opinions = [
                (
                    OpinionType.PER_CURIAM,
                    JusticeTag.PER_CURIAM,
                    None,
                ), [],
            ]

        dissent, majority = [], [require_non_none(majority_opinion[1])]
        opinion_summaries = []
        if majority_opinion[2] is not None:
            majority.extend(majority_opinion[2])
        for opinion in opinions:
            opinion_summary = (
                f'{require_non_none(opinion[0]).name}'
                f'by {require_non_none(opinion[1]).name}, '
            )
            if opinion[0] is OpinionType.DISSENT:
                dissent.append(opinion[1])
                if opinion[2] is not None:
                    dissent.extend(opinion[2])
            # add concurrence author and joiners to majority list
            elif opinion[0] in (
                OpinionType.CONCURRENCE,
                OpinionType.CONCURRENCE_AND_DISSENT,
            ):
                majority.append(require_non_none(opinion[1]))
                if opinion[2] is not None:
                    majority.extend(opinion[2])
            if opinion[2] is not None:
                opinion_summary += (
                    f'joined by {", ".join([j.name for j in opinion[2]])}'
                )
            opinion_summaries.append(opinion_summary)

        if (
            majority_opinion[0] is OpinionType.PER_CURIAM
            or majority_opinion[0] is OpinionType.DECREE
        ):
            majority_count = 9
        else:
            majority_count = len(set(majority))
        dissent_count = len(set(dissent))
        score = f'{majority_count}-{dissent_count}'

        return majority, dissent, score, opinion_summaries

    def get_alignment_score(self) -> str:
        'Return score and author (e.g. 6-3 by JUSTICE)'
        summary = self.alignment
        return f'{summary[2]} by {summary[0][0].name}'

    def set_authorship(self) -> tuple[JusticeTag, list[JusticeTag] | None]:
        """Set author and joiners for Slip Opinion."""
        if self.syllabus:
            # alignment = self.syllabus.get_alignment_tuple()
            return (self.syllabus.author, self.syllabus.joiners)
        elif self.is_per_curiam or self.is_decree:
            return (JusticeTag.PER_CURIAM, [JusticeTag.PER_CURIAM])
        else:
            raise NotImplementedError

    def set_recusals(self) -> list[JusticeTag] | None:
        """Set recused Justices for Slip Opinion."""
        if self.syllabus:
            return self.syllabus.recusals
        elif self.is_per_curiam or self.is_decree:
            return self.opinions[0].recusals
        else:
            raise NotImplementedError

    def set_documents(self) -> None:
        """Get Opinions"""
        pattern = (
            r'(?ms)(SUPREME\s+COURT\s+OF\s+THE\s+UNITED\s+STATES.*?'
            r'(?=SUPREME\s+COURT\s+OF\s+THE\s+UNITED\s+STATES))|(SUPREME\s+'
            r'COURT\s+OF\s+THE\s+UNITED\s+STATES\s+.*)'
        )
        # pattern searches for text betwen SCOTUS headers, as well as EOF.
        # joining because last match thru EOF is captured in group 2.
        doc_texts = [
            ''.join(f) for f in
            re.findall(pattern=pattern, string=self.text)
        ]

        if not (self.is_per_curiam or self.is_decree):
            self.syllabus = Syllabus(
                text=doc_texts[0], nlp=self.nlp,
                document_type=self.document_type,
            )
            for doc_text in doc_texts[1:]:
                self.opinions.append(
                    Opinion(
                        text=doc_text,
                        nlp=self.nlp,
                        document_type=self.document_type,
                    ),
                )
        else:
            for doc_text in doc_texts:
                self.opinions.append(
                    Opinion(
                        text=doc_text,
                        nlp=self.nlp,
                        document_type=self.document_type,
                    ),
                )

    def __str__(self) -> str:
        """Print Slip Opinion Summary."""
        retv = (
            f"\n\n{'SLIP OPINION SUMMARY':~^{72}}\n"
            f'Link  {self.url}\n{"-"*72}\n'
            f'Case:  {self.title :>{5}}\n'
            f'No.:   {self.case_number :>{5}}\n'
        )
        if self.lower_court:
            retv += f'From:  {self.lower_court}\n'
        retv += f'Dispositions:\t{" and ".join(self.dispositions)}\n\n'
        retv += f'  {self.score}\n'
        retv += (
            f'\n{"*"*72}\nHeld:\n\n\t{self.holding}\n\n{"*"*72}\n\n'
        )
        if self.recusals:
            retv += f'Recused:  {self.recusals}\n'
        for opinion in self.alignment[-1]:
            retv += f'{opinion}\n'
        return retv

    def compose_tweet(self) -> str:
        s = (
            f'OPINION:\n'
            f'{self.title :>{5}}\n\n'
            f'Held: {self.holding}\n\n'
            f'({self.score})'
            f'\n{self.url}'
        )
        return s


class OpinionRelatingToOrder(Release):
    """Opinions may be written by Justices to comment on the summary
    disposition of cases by orders, e.g., if a Justice wants to dissent from
    the denial of certiorari or concur in that denial.
    """
    case_number: str
    title: str
    petitioner: str
    repondent: str
    case_name: str
    lower_court: str
    documents: list[Document]
    author: JusticeTag
    joiners: list[JusticeTag] | None
    nlp: Language

    def __init__(
        self, date: str, text: str, case_number: str, title: str, url: str,
        document_type: DocumentType, petitioner: str,
        respondent: str, lower_court: str, nlp: Language,
    ) -> None:
        super().__init__(date, text, url, document_type, nlp=nlp)
        self.case_number = case_number
        self.title = title
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
            self.documents.append(
                Opinion(
                    text=doc_text,
                    nlp=self.nlp,
                    document_type=self.document_type,
                ),
            )

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
            f'{self.title}\n'
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
        pdf: pdfplumber.pdf.PDF, document_type: DocumentType, nlp: Language,
    ) -> None:
        super().__init__(
            date=date, text=text, url=url, nlp=nlp,
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
            self.document = OrderList(
                self.text,
                nlp=self.nlp,
                document_type=self.document_type,
            )
        elif self.document_type is DocumentType.RULES_ORDER:
            self.document = RuleOrder(
                self.text,
                self.pdf, self.title, self.url, self.document_type,
            )

    def __str__(self) -> str:
        """Return string representation of OrderList."""
        s = f'\n{self.title}\n{self.date}\n\n'
        s += f"{'ORDER SUMMARY':~^{72}}"
        s += f'{self.document}'
        return s

    def compose_tweet(self) -> str:
        """Return tweetable summary."""
        s = f'{self.title} ({self.date})\n'
        s += f'{self.document.compose_tweet()}\n\n'
        s += f'{self.url}'
        return s
