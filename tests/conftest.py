from __future__ import annotations

from datetime import date

import pytest

from omg_scotus.justice import create_court
from omg_scotus.justice import Ideology
from omg_scotus.justice import Justice
from omg_scotus.justice import JusticeTag
from omg_scotus.justice import President
from omg_scotus.justice import Role
from omg_scotus.opinion import StayOpinion
from omg_scotus.order_list import OrderList


@pytest.fixture
def justice_w_middle_name_title() -> Justice:
    retv = Justice(
        first_name='John',
        middle_name='Glover',
        last_name='Roberts',
        tag=JusticeTag.CHIEF,
        suffix='Jr.',
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.CHIEF_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )
    return retv


@pytest.fixture
def justice_w_middle_name() -> Justice:
    retv = Justice(
        first_name='John',
        middle_name='Glover',
        last_name='Roberts',
        tag=JusticeTag.CHIEF,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.CHIEF_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )
    return retv


@pytest.fixture
def justice_wo_middle_name_title() -> Justice:
    retv = Justice(
        first_name='Mickey',
        last_name='Mouse',
        suffix='Jr.',
        tag=JusticeTag.ALITO,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )
    return retv


@pytest.fixture
def justice_wo_middle_name() -> Justice:
    retv = Justice(
        first_name='Mickey',
        last_name='Mouse',
        tag=JusticeTag.ALITO,
        start_date=date(2005, 9, 25),
        birth_date=date(1955, 1, 27),
        nominating_president=President.BUSH,
        role=Role.ASSOCIATE_JUSTICE,
        ideology=Ideology.CONSERVATIVE,
    )
    return retv


@pytest.fixture
def court():
    return create_court()


@pytest.fixture
def sample_orderlist():
    orders_text = """ \n(ORDER LIST: 596 U.S.)  \n \n \nMONDAY, APRIL  18, 2022 \n \n \nCERTIORARI -- SUMMARY DISPOSITIONS  \n20-37    )   BECERRA, SEC. OF H&HS, ET AL. V. GRESHAM, CHARLES, ET AL. \n         ) \n20-38    )   ARKANSAS V.  GRESHAM, CHARLES, ET AL. \n                 The motion to vacate the judgments is  granted.   The \n             judgment of  the United States Court of Appeals for the District \n             of  Columbia Circuit in  Nos. 19-5094  and 19-5096 is  vacated, and \n             the cases are remanded to that court with  instructions to direct \n             the District Court to  vacate its judgment and dismiss the case \n             as moot.   See United States v.  Munsingwear, Inc., 340 U. S.  36   \n (1950).  The judgment of the United States Court of  Appeals for  \n the District of Columbia Circuit in Nos. 19-5293 and 19-5295 is   \n vacated, and the cases are remanded to that  court with   \n instructions to direct the District Court to remand to the  \n Secretary of  Health and Human Services. \n21-700        SMITH, KEITH V. CHICAGO, IL, ET  AL. \n                 The petition for a writ of certiorari is granted.  The \n             judgment is  vacated, and the case is remanded to the United \n             States Court of Appeals for the Seventh Circuit for further \n             consideration in light of  Thompson v. Clark, 596  U. S. ___  \n (2022). \nORDERS IN PENDING  CASES  \n21M103        BROWN, BRYAN K. V. NEAL, WARDEN \n                 The motion to direct the  Clerk to file  a petition for a writ \n             of certiorari out of time is denied.  \n21-757       AMGEN  INC., ET AL.  V. SANOFI, ET  AL. \n21-1013      TURKEY V. USOYAN, LUSIK, ET AL. \n                 The Solicitor General is invited to  file briefs in these \n             cases expressing the views of  the United States. \n21-7098      LANDRETH, THOMAS G. V.  UNITED STATES, ET  AL. \n21-7395      ZOGRAFIDIS, KONSTANTINOS V. UNITED STATES \n                 The motions of petitioners for leave to proceed in forma \n             pauperis are denied.   Petitioners are allowed until May 9, 2022, \n             within which to pay the docketing fees required by Rule 38(a)  \n and to submit petitions in compliance  with  Rule  33.1  of  the  \n Rules of this  Court. \nCERTIORARI DENIED  \n20-1351      HURD, PHILLIP W., ET AL. V. LASKAR, JOY \n20-1788      NEW YORK, NY, ET AL. V. FROST, JARRETT \n21-626        BOYD & ASSOCIATES V. WHITE, BRYAN K., ET AL. \n21-640       FIVE STAR AUTOMATIC PROTECTION  V.  DEPT. OF  LABOR \n21-669        GUIDO, JOSE  B. V. GARLAND, ATT'Y GEN. \n21-796       MARCHAND  &  ROSSI, L.L.P. V. WHITE, BRYAN  K., ET AL. \n21-838    )   PENOBSCOT NATION V.  FREY, ATT'Y GEN. OF  ME, ET AL. \n         ) \n21-840    )  UNITED STATES V. FREY, ATT'Y GEN. OF ME, ET AL.  \n21-848        SPIRE MISSOURI INC., ET AL. V. ENVTL. DEFENSE FUND, ET AL. \n21-854        MANISCALCO, RACHEL, ET AL. V.  NYC DEPT. OF ED., ET AL. \n21-898        CONYERS, BLAKE, ET AL. V. CHICAGO, IL \n21-906       KLICKITAT COUNTY, WA, ET AL.  V. CONFEDERATED TRIBES AND  BANDS \n21-951        RIO GRANDE FOUND. V. SANTA FE, NM, ET AL. \n21-966        NEW YORK, ET AL. V.  YELLEN, SEC. OF TREASURY, ET AL. \n21-978        RIVERO, CARMELA V. FIDELITY INVESTMENTS, INC. \n21-1010      NIX, TRACY V. ADVANCED UROLOGY INSTITUTE  \n21-1071      MURRAY, STEPHEN  L.  V. TAYLOR, JANELLE I., ET AL. \n21-1077      REYES, YACAIRA V. WESTCHESTER CTY. HEALTH,  ET  AL. \n21-1080      GARRETT, JACKY S. V. LUMPKIN, DIR., TX DCJ \n21-1091      ESPEJO, EDWIN V. WASHINGTON \n21-1094      KABONGO, JACQUES J.  V. MICHIGAN \n21-1096      GUAN,  ALICE V. ELLINGSWORTH RESIDENTIAL ASSOC. \n21-1097      DAHIYA, VINOD K. V.  NEPTUNE SHIPMANAGEMENT, ET AL. \n21-1103      PELAEZ, RAUL A. V. GEICO \n21-1104      DAVIS, JOHN V. ANDREWS, TX, ET  AL. \n21-1110      BOYS, TRAVIS V. LOUISIANA \n21-1112      GORBEA, SONYA V. VERIZON NEW YORK, INC. \n21-1116      LIEBOVICH, MATTHEW, ET AL. V.  TOBIN, DIANE J., ET  AL. \n21-1119      FRANCIS, PAUL V. DESMOND, JOHN O.  \n21-1129      ZHENG-SMITH, WEN-TING V. NASSAU HEALTH CARE CORP., ET AL. \n21-1130      MUTUA, RAINEY M. V.  GARLAND, ATT'Y GEN. \n21-1137      PHILLIPS, BYRON W. V.  LIFE PROPERTY MANAGEMENT, ET AL. \n21-1148      SB BLDG. ASSOC. LTD. PARTNERSHIP V. ATKINSON, BUNCE, ET AL. \n21-1156      DAVID, RODRIC V. KAZAL, TONY, ET AL. \n21-1162      BAILEY-JOHNSON,  ERIKA V. UNITED STATES \n21-1166      GRAMAJO-REYES, ROLAND O. V. GARLAND, ATT'Y  GEN. \n21-1167      CHAPMAN, TERRY R. V. SSA, ET AL. \n21-1186      MANOR, MICHELLE, ET  VIR V. MAYORKAS, SEC.  OF HOMELAND \n21-1199      GAETJENS, SALLY  V.  LOVES PARK,  IL, ET AL. \n21-1213      BROADEN, MICHAEL V.  DEPT. OF TRANSPORTATION \n21-1226      WASHINGTON, MICHAEL V.  FL  DEPT. OF TRANSPORTATION \n21-1227      MRI ASSOCIATES OF TAMPA, INC. V.  STATE  FARM  \n21-6186      ROSE,  FARUQ V. UNITED STATES \n21-6348      RAMIRO-MEDINA, RAFAEL V. UNITED STATES  \n21-6551      AGUILERA FERNANDEZ, DENIS A. V.  GARLAND, ATT'Y GEN.  \n21-6630      RODRIGUEZ, DANIEL A. V. UNITED STATES \n21-6719      N. R. V. KANSAS \n21-6747      TAYLOR, VICTOR D. V.  JORDAN,  WARDEN \n21-6815      FLORES-PEREZ, NOE V. UNITED STATES \n21-6846      REYNOSO, JUAN J. V.  LUMPKIN, DIR., TX DCJ \n21-7015      JAMES, EDWARD T. V.  FLORIDA \n21-7046      HAILE, MAKEDA V. CONTEH, ABDUL \n21-7075      COOKE, IAN T. V. WILLIAMS, JOHN  R., ET AL. \n21-7091      COLEY, ZACHARY E. V. SHAW INDUSTRIES, INC. \n21-7096      REED, DANIEL L. V. LUMPKIN, DIR., TX DCJ \n21-7100      DUNKINS, ALKIOHN V.  PENNSYLVANIA \n21-7104      SIMMERMAKER, JEFFREY R. V. CEDAR CTY. SHERIFF, ET  AL. \n21-7108      RYAN,  KEVIN S. V. MINNESOTA \n21-7109      MILLS, JAMIE V. HAMM, COMM'R, AL DOC \n21-7111      WORTHY, DAVID R. V.  CORIZON MEDICAL GROUP, ET AL. \n21-7113      JAKO, GERALD W. V. WEST VIRGINIA \n21-7114      SMITH, ROBERT N. V.  FLORIDA \n21-7118      DAVOREN, JOSHUA B. V.  MASSACHUSETTS \n21-7121      WILSON, JOSEPH L. V. PHOENIX POLICE DEPT., ET AL. \n21-7122      WARNER, THOMAS V. ILLINOIS \n21-7126      BUTLER, QUINCY D. V.  LUMPKIN, DIR.,  TX  DCJ \n21-7127      NWANERI, NGOZIKA J.  V. QUINN EMANUEL URQUHART SULLIVAN \n21-7130      JOHNSON, JABARI J. V.  DeFRANCESCO, ET AL. \n21-7131      JONES, BOBBY R. V. MITCHELL, WARDEN, ET  AL. \n21-7138      ECHOLS, ROY F. V. CSX TRANSPORTATION, INC. \n21-7159      WILLIAMS, GARLAND E. V. UNITED STATES \n21-7166      OZSUSAMLAR, MUSTAFA V.  ADAMS, WARDEN  \n21-7167      M. D. V. MT  DEPT. OF PUB. HEALTH, ET AL. \n21-7172      ZINMAN, COREY J.  V. NOVA SOUTHEASTERN UNIV., ET AL. \n21-7179      WILEY, PRECIOUS  V.  DEPT. OF VA, ET AL. \n21-7185      TATE,  BRIAN A. V. HOGAN, GOV. OF  MD, ET AL. \n21-7194      CANALES, MAINOR V. TENNESSEE \n21-7197      SHAFFER, DENNIS L. V.  KANSAS \n21-7198      AHART, REMEL V. MASSACHUSETTS \n21-7200      JACQUES, JOHN L. V.  WISCONSIN \n21-7206      DUCKWORTH, CHUCK V.  ILLINOIS \n21-7207      BREWER, ROBERT V. NEW YORK \n21-7208      BAILEY, THERESA V. NY  LAW SCHOOL, ET AL. \n21-7213      McKINNEY, KWASI V. ARKANSAS \n21-7228      DINGLE, TIMOTHY D. V.  KENDALL, WARDEN \n21-7231      McGILLVARY, CALEB L.  V.  NEW JERSEY \n21-7240      CARR, ROBERT V. WISCONSIN \n21-7250      FORTUNA, MICHAEL R.  V. HUDGINS, WARDEN, ET AL. \n21-7261      IFESINACHI, EZEANI  G. V. CIRILLO, WARDEN \n21-7265      MANNS, VICTOR L. V.  FLORIDA \n21-7278      JAMES, CALVIN V. WILCHER, SHERIFF \n21-7280      CARROLL, SAMMIE V. MARYLAND \n21-7303      PINCHON, EDWARD V. BYRD, WARDEN \n21-7308      COLVIN, DEON D. V. HOWARD UNIVERSITY \n21-7310      KLINE, CHRIS W. V. JOHNS, ADM'R, DEPT. OF  H&HS \n21-7320      CARTER, DEVIN M. V.  IOWA \n21-7330       RAJAB, JAPHER Y. V.  UNITED STATES  \n21-7331      ROBINSON, DARREGUS  T. V. UNITED STATES \n21-7332      SISNERO-GIL, MARLON V. UNITED STATES \n21-7333       PENNY, ANDREW M. V.  UNITED STATES   \n21-7334      NUMANN, GREGORY T. V.  UNITED STATES \n21-7339      GORDON, ROBERT D. V.  UNITED STATES \n21-7340      HALL, JOSEPH L. V. UNITED STATES \n21-7341      FRUIT, JERRY V. UNITED STATES \n21-7342      GARCIA, ALEJANDRO S. V. UNITED STATES \n21-7343      HUESTON,  HARRY V. UNITED STATES \n21-7344      CALLIGAN, EDWIN V. UNITED STATES \n21-7345      ARING, DAVID W. V. UNITED STATES \n21-7346      BRULE, AVIAN V. UNITED STATES \n21-7347      PHILLIPS, ANTHONY V.  UNITED STATES \n21-7349      JOHNSON,  CHARLES V. KIJAKAZI, COMM'R, SOCIAL SEC. \n21-7351      CRUZ-POLANCO, MIGUEL A. V. UNITED STATES \n21-7352      INTZIN-GUZMAN, PEDRO V. UNITED STATES \n21-7353      CHAVARRIA, ALEJANDRO V. UNITED STATES \n21-7354      KEEL, JOSEPH P. V. FLORIDA \n21-7355       VANCE, JON C. V. UNITED STATES  \n21-7356      JOHNSON, STACEY T. V.  UNITED STATES \n21-7357      CASTRO-LOPEZ, JOEL V.  UNITED STATES \n21-7359      GATTIS, KALEB V. UNITED STATES \n21-7360      GREENBERG, MARC N. V.  UNITED STATES \n21-7362      KURTZ, KYLE V. GRAY,  WARDEN \n21-7367      SWINDLE, ADAM S. V.  MA'AT, S.  \n21-7369      PARKER, DANNIE S. V.  UNITED STATES \n21-7372      ABADI, AARON V. DEPT. OF TRANSPORTATION \n21-7373      CHAPMAN, STEVEN M. V.  FCC COLEMAN - USP II, WARDEN \n21-7374      NOGUERA, WILLIAM A.  V. DAVIS, WARDEN \n21-7375      RODRIGUEZ, RODOLFO V.  UNITED STATES \n21-7376      STAFFORD, KHAIL V. UNITED STATES  \n21-7382      HUERTA, ADOLFO V. UNITED STATES \n21-7385      ALCARAZ, JUAN M. V.  WILLIAMS, WARDEN, ET AL. \n21-7386      CODY, SANDCHASE V. UNITED STATES \n21-7387      WOOD,  HENRY E. V. UNITED STATES \n21-7390      HAILEY, CHOYA D. V.  UNITED STATES  \n21-7391      HENDERSON, ISAIAH R. V. UNITED STATES \n21-7393      SKAGGS, TRAVIS R. V.  UNITED STATES \n21-7403      BREEDEN,  JAMES C. V.  UNITED STATES \n21-7404      BARAHONA-PAZ, JOSE  A. V. UNITED STATES \n21-7405      GUITY-NUNEZ, JOSHUA V. UNITED STATES \n21-7409      STRIZICH, JORY R. V.  MONTANA \n21-7414      HAWES, GREGORY M. V.  PACHECO, WARDEN, ET  AL. \n21-7415      RAUSENBERG, MATTHEW V.  LANGFORD,  WARDEN \n21-7418      L'HEUREUX, JAMES R.  V. WEST VIRGINIA \n21-7423      KEYES, DELBERT V. MISSISSIPPI \n21-7427      SNOW, WILLIAM G. V.  ILLINOIS \n21-7429      MARTINEZ, DAMON R. V.  UNITED STATES \n21-7430      ESPINOZA, ROBERTO P. V. UNITED STATES \n                 The petitions for writs of certiorari are denied. \n21-788        APARTMENT ASSN. OF LA  CTY. V.  LOS ANGELES, CA, ET  AL. \n                 The motion of Foundation for Moral Law for leave to file a \n             brief as  amicus curiae is granted.  The petition for a writ of \n             certiorari is denied. \n21-870        MICHIGAN V.  TERRANCE, TRESHAUN L.  \n21-871        LOUISIANA V. BROWN, DAVID H. \n                 The motions of respondents for leave to proceed in forma  \n pauperis are granted.  The petitions for writs of certiorari are   \n denied.  \n21-1144      LEACH, TRACIE, ET AL. V. MENTOR WORLDWIDE,  LLC \n                 The petition for a writ of certiorari is denied.  Justice \n             Alito took no part in  the consideration or decision of this \n             petition. \n21-7123      WILSON, JOHN J. V. FLORIDA \n21-7168      LIVIZ, ILYA  V. SUPREME COURT OF  MA \n                 The motions of petitioners for leave to proceed in forma \n             pauperis are denied, and the petitions for writs of  certiorari \n             are dismissed.  See Rule 39.8.   As the petitioners have \n             repeatedly abused this Court's process, the Clerk is directed \n             not to accept any further petitions in noncriminal matters from  \n             petitioners unless the docketing fees required by  Rule 38(a) are \n             paid and the petitions are submitted in  compliance with Rule \n             33.1.  See Martin v.  District  of  Columbia  Court  of  Appeals, 506 \n             U. S. 1 (1992) (per  curiam). \n21-7366      ROGERS, RAYMOND L. V.  UNITED STATES \n                 The petition for a writ of certiorari is denied.  Justice \n             Gorsuch took no part in the consideration or decision of this  \n             petition. \n21-7389      ALEXANDER, JOHN P. V.  MISSISSIPPI \n                 The motion of petitioner for leave to  proceed in forma \n             pauperis is  denied, and the petition for a writ of certiorari is \n             dismissed.   See Rule 39.8.  As the petitioner has repeatedly \n             abused this  Court's process, the Clerk is  directed not to accept \n             any further petitions in noncriminal matters from petitioner \n             unless the docketing fee required by Rule  38(a) is paid and the \n             petition is  submitted in compliance with Rule 33.1.  See Martin  \n             v.  District  of  Columbia  Court  of  Appeals, 506 U. S.  1 (1992)  \n             (per  curiam).  \nHABEAS CORPUS DENIED  \n21-7410      IN RE EDUARDO PINEDA \n                 The petition for a writ of habeas corpus is denied. \nMANDAMUS DENIED  \n21-1115      IN RE WANDA BOWLING \n                 The petition for a writ of mandamus is denied. \nPROHIBITION DENIED  \n21-7364      IN RE DAVID LOPEZ \n                 The petition for a writ of prohibition is denied. \nREHEARINGS DENIED  \n21-8          PENNINGTON-THURMAN, WILMA M. V.  FED. HOME  LOAN MORTGAGE, ET  AL. \n21-787       RUSSOMANNO, GINA V. DUGAN, DAN, ET AL. \n21-815        PIERSON, RAYMOND H.  V. ROGOW, BRUCE S., ET AL. \n21-5557      MILLER, CHASMIND D. V.  GEICO, ET  AL. \n21-5938      JOHNSON, BRENDA M. V.  ELECTRONIC TRANSACTION \n21-6172      SULZNER, JUSTIN P. V.  USDC ND  IA \n21-6444      IN RE JAMES J. KNOCHEL \n21-6470      KOGIANES, MICHAEL G.  V.  JENSEN, EDWARD, ET  AL. \n21-6498      PARK, HYE-YOUNG V. UNIV. BD. OF  TRUSTEES, ET AL. \n21-6571      BENITEZ,  RUBEN O. V.  MISSISSIPPI \n21-6588      ANDERSON, AMY B. V.  WRIGHT, WARDEN, ET AL. \n21-6694      BRANTLEY, LAWRENCE  S. V. TX DEPT. OF  FAMILY  \n21-6709      WIJE,  SURAN V. UNITED STATES \n21-6840      BART, SANDRA L. V. UNITED STATES \n21-6910      CRUZADO-LAUREANO, JUAN M. V. MULDROW, W. STEPHEN \n21-7005      DeVORE, ADAM M. V. BLACK, WARDEN \n                 The petitions for rehearing are denied.  \n21-881        SHAO, LINDA V. McMANIS FAULKNER, LLP \n                 The petition for rehearing is denied.  The Chief Justice \n             took no part in the consideration or decision of this petition. \n21-934       WEINBACH, LANA V. BOEING CO., ET  AL. \n                 The petition for rehearing is denied.  Justice Alito took  no \n             part in the consideration or decision of this petition. \n21-6979      JOHNSTON, ANDREW J. V.  UNITED STATES \n                 The petition for rehearing is denied.  Justice Barrett took  \n             no part in the consideration or  decision of this petition. """
    opinions_text = """\nSUPREME COURT OF THE UNITED STATES \nKRISTOPHER LOVE  v. TEXAS \nON PETITION FOR WRIT OF CERTIORARI TO THE  \nCOURT OF CRIMINAL APPEALS OF TEXAS  \nNo. 21–5050.  Decided April 18, 2022  \n  The petition for a writ of certiorari is denied. \nJUSTICE SOTOMAYOR, with whom JUSTICE  BREYER and  \nJUSTICE  KAGAN join, dissenting from the denial of sum-\nmary vacatur. \n  Racial bias is “odious in all aspects,” but “especially per-\nnicious in the administration of justice.” Buck v. Davis, 580 \nU. S. ___, ___ (2017) (slip op., at 22) (internal quotation \nmarks omitted).  When racial bias infects a jury in a capital \ncase, it deprives a defendant of his right to an impartial tri-\nbunal in a life-or-death context, and it “‘poisons public con-\n \nfidence’ in the judicial process.”  Ibid.  The seating of a ra-\ncially biased juror, therefore, can never be harmless.  As \nwith other forms of disqualifying bias, if even one racially \nbiased juror is empaneled and the death penalty is imposed, \n“the State is disentitled to execute the sentence,” Morgan v. \nIllinois, 504 U. S. 719, 729 (1992).\n  In this case, petitioner Kristopher Love, a Black man, \nclaims that one of the jurors in his capital trial was racially \nbiased because the juror asserted during jury selection that \n“[n]on-white” races were statistically more violent than the \nwhite race.  29 Record 145.  The Texas Court of Criminal \nAppeals never considered Love’s claim on the merits.  In-\nstead, relying on an inapposite state-law rule, the court con-\ncluded that any error was harmless because Love had been \nprovided with two extra peremptory strikes earlier in the \njury selection proceeding, which he had used before the ju-\nror at issue was questioned.  That decision was plainly er-\nroneous.  An already-expended peremptory strike is no cure for the seating of an allegedly biased juror. The state court \nthus deprived Love of any meaningful review of his federal \nconstitutional claim.  I would summarily vacate the judg-\nment below and remand for proper consideration. \nI \n  In 2018, a jury convicted Love of capital murder in the\ncourse of a robbery that occurred in 2015.  Prior to trial,  \nprospective members of the jury filled out a questionnaire \nthat included the following questions:  \n  “68.  Do  you  sometimes  personally  harbor  bias \nagainst members of certain races or ethnic groups? \n  “69. Do you believe that some races and/or ethnic \ngroups tend to be more violent than others?”  Jury\nQuestionnaire, p. 12 (Juror 1136B).  \n  To the first question, No. 68, the prospective juror at is-\nsue answered, “No.”  Ibid.   But to the second question, No. \n69, he answered, “Yes.”  Ibid. He explained that “[s]tatistics \nshow more violent crimes are committed by certain races.  I \nbelieve in statistics.”  Ibid.  \n  During the voir dire  proceeding that followed, both Love \nand the State questioned the prospective juror about his re-\nsponse to question No.  69.  He  explained that he understood \n“[n]on-white” races to be the “more violent races.”  29 Rec-\nord 145. He claimed that he had seen statistics to this effect \nin “[n]ews reports and criminology classes” he had taken.   \nId., at 144.  He stated that his answer to question No. 69 \nwas based on these statistics, rather than his “personal feel-\nings towards one race or another,” id., at 107, and he indi-\ncated that he did not “think because of somebody’s race \nthey’re more likely to commit a crime than somebody of a\ndifferent race,” id., at 145.  He told defense counsel that he \nwould not feel differently about  Love “because he’s an Afri-\ncan American.”  Id., at 146.   Following the examination, Love’s counsel moved to ex-\nclude the prospective juror for cause based on “his stated \nbeliefs that . . . non-whites commit more violent crimes \nthan whites.”  Id., at 153.  Counsel argued that, under \nTexas law, the first issue the jury would have to decide at \nsentencing (referred to as Special Issue No. 1) was “whether \nthere is a probability that the defendant would commit\ncriminal acts of violence that would constitute a continuing \nthreat to society.” Tex. Code Crim. Proc. Ann., Art. 37.071,  \n§2(b)(1) (Vernon 2021).  Counsel explained that “leaving \nthis man on the jury would be an invitation to leaving some-\none on there that might make a decision on Special Issue \nNo. 1 that would ultimately lead to a sentence of death on  \nhis preconceived notions and beliefs that have to do with \nthe race of the defendant.”  29 Record 153–154. \n  The trial court denied defense counsel’s challenge for\ncause without explanation.  At that point, counsel had ex-\nhausted all of Love’s allotted peremptory challenges and \ntwo extra challenges the trial court had previously granted.  \nLove’s  counsel  requested  a  third  additional  peremptory \nchallenge in order to strike the prospective juror at issue.  \nThe trial court denied that request, again without explana-\ntion, and seated the juror on the jury. \n  At the conclusion of the trial, the jury convicted Love.  At  \nsentencing, the jury unanimously concluded that there was \na sufficient probability that Love would commit future vio-\nlent crimes and that there were not sufficient mitigating \ncircumstances to warrant a sentence of life.  Accordingly,  \nthe trial court sentenced Love to death. \n  On appeal, Love argued that he was “denied the constitu-\ntional right to an impartial jury” because the trial court \nseated a “racially biased juror.”  Brief for Appellant in No. \nAP–77,085 (Tex. Crim. App.), pp. 101–102.  Rather than ad-\ndress this federal constitutional claim on the merits, the  \nCourt of Criminal Appeals of Texas held that, “even if we  \nassume that the trial court erred in denying Appellant’s  challenges [to the juror at issue and another prospective ju-\nror] for cause,” Love could not show any harm under Texas \nlaw. 2021 WL 1396409, *24 (Apr. 14, 2021). The court rea-\nsoned that the trial judge had previously granted Love two \nextra peremptory challenges, which he had already used by \nthe time the prospective juror at issue was called up.  Nev-\nertheless, in the state appellate court’s view, each extra per-\nemptory challenge operated to cure any harm from the er-\nroneous denial of any challenge for cause.  See ibid. (citing \nChambers  v. State, 866 S. W. 2d 9, 23 (Tex. Crim. App. \n1993) (en banc)).  The court concluded that Love could not \nmake out any claim for relief stemming from the juror’s al-\nleged bias.   See 2021 WL 1396409, *24. \n  Love now petitions this Court for a writ of certiorari. \nII  \n  “[T]he Sixth and Fourteenth Amendments guarantee a\ndefendant on trial for his life the right to an impartial jury.”   \nRoss v. Oklahoma, 487 U. S. 81, 85 (1988).  Biases capable\nof destroying a jury’s impartiality can take many forms.  \nSee Morgan, 504 U. S., at 729 (juror who would automati-\ncally vote for the death penalty in every case); Parker v. \nGladden, 385 U. S. 363, 365–366 (1966) (per curiam) (prej-\nudicial comments by the bailiff ); Irvin v. Dowd, 366 U. S. \n \n717, 725–727 (1961) (public opinions and press coverage\nabout the case); Morford  v. United States, 339 U. S. 258, 259 \n(1950) (per curiam) (potential influence of an executive or-\nder requiring loyalty to United States).  Whatever the na-\nture of the bias, if a trial court seats a juror who harbors a \ndisqualifying prejudice, the resulting judgment must be re-\nversed.  See United States v. Martinez-Salazar, 528 U. S.  \n304, 316 (2000); Morgan, 504 U. S., at 729; see also Rose v. \nClark, 478 U. S. 570, 578 (1986) (“Harmless-error analysis \nthus presupposes a trial . . . before an impartial judge and \njury”). \n  This Court has recognized that claims of racial bias must be treated “with added precaution” in light of the special \ndanger such bias poses.  Pena-Rodriguez v. Colorado, 580  \nU. S. ___, ___ (2017) (slip op., at 17).  For instance, when a \njuror makes a clear statement indicating that racial stereo-\ntypes or animus influenced a conviction, the Sixth Amend-\nment requires the trial court to make an exception to the \ngeneral rule shielding juror deliberations from scrutiny in \norder “to consider the evidence of the juror’s statement and \nany resulting denial of the jury trial guarantee.”  Ibid.  In  \naddition, in some circumstances, courts must permit de-\nfendants to ask questions about prospective jurors’ racial \nbiases during voir dire. See Turner  v. Murray, 476 U. S. 28,  \n36–37 (1986); Ham v. South Carolina, 409 U. S. 524, 527  \n(1973).  The principle underlying these cases is simple: \n“[R]acial bias in the justice system must be addressed—in-\ncluding, in some instances, after the verdict has been en-\ntered.”  Pena-Rodriguez, 580 U. S., at ___ (slip op., at 17).  \nThat is because racial bias is too grave and systemic a \nthreat to the fair administration of justice to be tolerated or \nignored.\n  In this case, no court has meaningfully reviewed Love’s \nallegations of racial bias in violation of the Sixth and Four-\nteenth Amendments.  Instead, the Court of Criminal Ap-\npeals “assume[d]” that the juror at issue was biased, but \nconcluded that allowing him to sit on the jury was harmless.  \n2021 WL 1396409, *24. That is an inherently contradictory\ndetermination.  If the juror were indeed biased, then be-\ncause he sat on the jury, Love’s conviction and sentence \n“would have to be overturned.”  Ross, 487 U. S., at 85. \n  The Court of Criminal Appeals reached its erroneous con-\nclusion by relying upon a state-law rule that has no appli-\ncation to Love’s claim.  Texas courts have developed a rule \naimed at evaluating the harm when a party is forced to use\na peremptory challenge on a juror who should have been \nexcluded for cause, thereby “‘wrongfully depriv[ing]’” the  \n   \nparty of an allotted challenge.  Hernandez  v.  State, 563 S. W. 2d 947, 948 (Tex. Crim. App. 1978) (en banc).  In such \ncases, a trial court can cure any harm from its erroneous \nruling by granting an  additional peremptory strike.  See \nChambers, 866 S. W. 2d, at 22–23.  This rule has no bearing \non Love’s federal constitutional claim that a racially biased \njuror actually sat on his jury and helped convict him and \nsentence him to death. As to that type of claim, a previously \nused peremptory strike does not eliminate the need to in-\nquire into the juror’s bias.\n  The State acknowledges that the Court of Criminal Ap-\npeals “never reached the federal issues Love raises,” Brief \nin Opposition 13, but the State contends that the court’s \nharmless-error analysis constitutes an independent and ad-\nequate  ground  for  the  judgment  below,  precluding  this \nCourt’s jurisdiction.  See Foster v. Chatman, 578 U. S. 488, \n497 (2016). As already shown, however, the state harmless-\nerror rule was not “an ‘adequate’  basis for the court’s deci-\nsion” on Love’s federal claim.  Ibid.  Indeed, in this situa-\ntion, the rule is entirely beside the point.  The State’s juris-\ndictional argument therefore fails. \n  The State also predicts that, on the merits, Love’s claim \nwould be rejected if it were reviewed, especially given the \ndeference owed to the trial court’s assessment of prospec-\ntive jurors.  A reviewing court should give the trial judge \nappropriate deference, see Uttecht v. Brown, 551 U. S. 1, 7 \n(2007), but it may not turn a blind eye to claims of bias en-\ntirely. The merits of Love’s claim should be reviewed by the \nCourt of Criminal Appeals in the first instance.  As this \nCourt has often said, “‘[w]e are a court of review, not of first \n \nview.’”  Manuel v. Joliet, 580 U. S. ___, ___ (2017) (slip op., \n \nat 14); see Sandstrom v.  Montana, 442 U. S. 510, 527 (1979) \n(“As none of these issues was considered by the Supreme \nCourt of Montana, we decline to reach them as an initial \nmatter here”). *  *  * \n  Over time, we have endeavored to cleanse our jury sys-\ntem of racial bias.  One of the most important mechanisms \nfor doing so, questioning during voir dire, was properly em-\nployed here to identify a potential claim of bias. Safeguards \nlike this, however, are futile if courts do not even consider \nclaims of racial bias that litigants bring forward.  The task  \nof reviewing the record to determine whether a juror was \nfair and impartial is challenging, but it must be under-\ntaken, especially when a person’s life is on the line.  I would \nensure that Love’s claim is heard by the Court of Criminal \nAppeals, rather than leave these questions unanswered.  I \nrespectfully dissent. """

    return OrderList(orders_text, opinions_text)


@pytest.fixture
def sample_order_opinion(sample_orderlist):
    return sample_orderlist.opinions[0]


@pytest.fixture
def sample_stay_opinion():
    text = """Supreme Court of the United States \n \nNo.  19A1035 \n \n \nDEPARTMENT OF JUSTICE, \n           \n                Applicant   \nv. \n \n \nHOUSE COMMITTEE ON THE JUDICIARY  \n \n \n \nO R D E R \n \n \n \n  UPON CONSIDERATION of the application of counsel for the \napplicant, \n  IT IS ORDERED that the mandate of the United States Court of \nAppeals for the District of Columbia Circuit, case No. 19-5288, is hereby \nstayed pending receipt of a response, due on or before Monday, May 18, 2020, \nby 3 p.m. ET, and further order of the undersigned or of the Court. \n \n            /s/  John G. Roberts, Jr.                                \n            Chief Justice of the United States \n \n \nDated this 8th \nday of May, 2020.  """

    return StayOpinion(text=text)
