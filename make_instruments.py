"""
Generate the Chapter 2 instrument appendices from the administered proformas.

Sources (Novel Data/):
    Headteacher Interview.docx                        -> snippets/interview_guide.tex
    School Visit Proforma - Lesson Observations v2.docx  \
    School Visit Proforma - Outside of Lessons v2.docx   /-> snippets/visit_protocol.tex

Each proforma is a sequence of rated items in a fixed shape: a stem paragraph,
a pole paragraph carrying the 1--5 scale and its end labels, and a table giving
the anchor description for (some of) the scale points. The interview items add a
key-word/phrase checklist to the same table. This script reads that shape
directly out of the Word XML, so the appendix is the instrument rather than a
transcription of it.

Usage:
    python thesis/make_instruments.py            # write the snippets
    python thesis/make_instruments.py --check    # exit 1 if either is stale
"""

import argparse
import ast
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_prompts import tex_escape  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')

PROJECT  = Path(__file__).resolve().parent.parent
DATA     = PROJECT / 'Novel Data'
SNIPPETS = PROJECT / 'thesis' / 'snippets'

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# Stray values left in the blank proforma by a filled-in copy. Keys are matched
# after whitespace normalisation.
FIXUPS = {
    'Teachers feel respected by all students 4':
        'Teachers feel respected by all students',
}

POLES = re.compile(r'^(.*?)\s*1\s+2\s+3\s+4\s+5\s*(.*)$')
DOTFILL = re.compile(r'^[^…\.]{0,40}[…\.]{6,}$')
YESNO = re.compile(r'^(.*?)\s*Y\s*/\s*N\s*$')
QNUM = re.compile(r'^Q\d+\.')

# Blank space on the paper form, with nothing to reproduce.
DROP = {'Notes:'}


# ── Word extraction ──────────────────────────────────────────────────────────

def _text(node) -> str:
    return re.sub(r'\s+', ' ', ''.join(t.text or '' for t in node.iter(W + 't'))).strip()


def read_docx(path: Path) -> list:
    """Return the body as a list of ('p', text) and ('tbl', rows) items."""
    with zipfile.ZipFile(path) as z:
        body = ET.fromstring(z.read('word/document.xml')).find(W + 'body')
    out = []
    for el in body:
        tag = el.tag.replace(W, '')
        if tag == 'p':
            t = FIXUPS.get(_text(el), _text(el))
            t = re.sub(r'^\*\*(.*)\*\*$', r'\1', t)  # emphasis typed as markdown
            if t and t not in DROP and not DOTFILL.match(t):
                out.append(('p', t))
        elif tag == 'tbl':
            rows = []
            for tr in el.findall(W + 'tr'):
                rows.append([' '.join(_text(p) for p in tc.findall(W + 'p')).strip()
                             for tc in tr.findall(W + 'tc')])
            out.append(('tbl', rows))
    return out


# ── Item rendering ───────────────────────────────────────────────────────────

def scale_sentence(poles: str | None, rows: list) -> str:
    """'Rated 1 (minor) to 5 (serious).', plus a note if 0 is defined."""
    lo = hi = None
    if poles:
        m = POLES.match(poles)
        if m:
            lo, hi = m.group(1).strip(), m.group(2).strip()
    base = (f'Rated 1 ({tex_escape(lo.lower())}) to 5 ({tex_escape(hi.lower())}).'
            if lo and hi else 'Rated 1 to 5.')
    if any(r and r[0].strip() == '0' for r in rows):
        base += ' A score of 0 is recorded separately (see below).'
    return base


def render_item(stem: str, poles: str | None, rows: list) -> list:
    anchors = [(r[0].strip(), r[1].strip()) for r in rows
               if len(r) >= 2 and re.fullmatch(r'[0-5]', r[0].strip())]
    checklist = [r[0].strip() for r in rows
                 if len(r) >= 2 and r[1].strip().upper() in ('Y/N', '')
                 and r[0].strip() and not re.fullmatch(r'[0-5]', r[0].strip())
                 and r[0].strip().lower() != 'key word/phrase']
    notes = [r[1].strip() for r in rows
             if len(r) >= 2 and not r[0].strip() and r[1].strip()]

    out = [r'\paragraph{' + tex_escape(stem) + r'}']
    out.append(scale_sentence(poles, rows))
    out.append('')
    if anchors:
        out.append(r'\begin{description}')
        for k, v in anchors:
            out.append(r'\item[' + k + r'] ' + tex_escape(v))
        out += [r'\end{description}', '']
    for n in notes:
        out += [tex_escape(n) + '.' if not n.endswith('.') else tex_escape(n), '']
    # 19 Aug 2026 (Damian): the key-word checklists are omitted from the thesis
    # appendix -- they enter no score. Only the question and its anchors remain.
    return out


def flush_loose(lines: list) -> list:
    """Render paragraphs that belong to no anchor table.

    Two blocks of the interview carry their response format inline rather than
    in a table: the yes/no systems checklist, and the Likert statements, where
    each statement is followed by its own copy of the agree/disagree scale.
    Both are collapsed into a single list.
    """
    out, i = [], 0
    while i < len(lines):
        if YESNO.match(lines[i]):
            out.append(r'\begin{itemize}')
            while i < len(lines) and YESNO.match(lines[i]):
                out.append(r'\item ' + tex_escape(YESNO.match(lines[i]).group(1).strip()))
                i += 1
            out += [r'\end{itemize}', '']
            continue
        pair = (i + 1 < len(lines) and POLES.match(lines[i + 1])
                and not POLES.match(lines[i]))
        if pair:
            m = POLES.match(lines[i + 1])
            out += [f'Each statement is rated 1 ({tex_escape(m.group(1).strip().lower())}) '
                    f'to 5 ({tex_escape(m.group(2).strip().lower())}).', '',
                    r'\begin{itemize}']
            while (i + 1 < len(lines) and POLES.match(lines[i + 1])
                   and not POLES.match(lines[i])):
                out.append(r'\item ' + tex_escape(lines[i]))
                i += 2
            out += [r'\end{itemize}', '']
            continue
        if QNUM.match(lines[i]):
            out += [r'\paragraph{' + tex_escape(lines[i]) + r'}',
                    'Recorded verbatim; not scored on the 1--5 scale.', '']
        else:
            out += [tex_escape(lines[i]), '']
        i += 1
    return out


def parse_items(body: list, headings: set) -> list:
    """Walk the body, emitting headings, loose paragraphs and rated items."""
    out, buf = [], []
    for kind, payload in body:
        if kind == 'p':
            if payload in headings:
                # The three forms punctuate "Section N" headings differently.
                head = re.sub(r'^(Section \d+)\s*[-–—]+\s*', r'\1 --- ',
                              payload.rstrip(':'))
                out += flush_loose(buf)
                out += [r'\subsubsection*{' + tex_escape(head) + r'}', '']
                buf = []
            else:
                buf.append(payload)
            continue
        # A table closes an item: the stem and pole lines are the last two
        # paragraphs before it, and anything earlier is loose prose.
        poles = buf[-1] if buf and POLES.match(buf[-1]) else None
        stem  = buf[-2] if poles and len(buf) >= 2 else (buf[-1] if buf else '')
        out += flush_loose(buf[:-2] if poles and len(buf) >= 2 else buf[:-1])
        out += render_item(stem, poles, payload)
        buf = []
    return out + flush_loose(buf)


def drop_form_header(body: list, keep_from: str) -> list:
    """Discard the blank form's identification fields."""
    for i, (kind, payload) in enumerate(body):
        if kind == 'p' and payload.startswith(keep_from):
            return body[i:]
    return body


# ── Documents ────────────────────────────────────────────────────────────────

def build_interview() -> str:
    body = drop_form_header(read_docx(DATA / 'Headteacher Interview.docx'),
                            'Open-ended questions')
    headings = {'Open-ended questions:', 'Yes-or-no questions', 'Statement ranking',
                'To be completed after the interview'}
    L = [r'% Auto-generated by thesis/make_instruments.py --- do not edit by hand.',
         r'% Source: Novel Data/Headteacher Interview.docx',
         '',
         r'The schedule below is the instrument as administered. Each open-ended',
         r'question was scored 1--5 against the anchor descriptions shown. Each',
         r'question was asked by one researcher and scored by both; \cref{tab:irr_interview}',
         r'reports agreement between them, and the analysis uses the final recorded score',
         r'for each question. A checklist of key words and phrases was also completed for',
         r'each question; it enters no score reported in the chapter and is omitted here.',
         r'Item-to-sub-score mapping is given in \cref{app:2A:guide}.',
         '']
    return '\n'.join(L + parse_items(body, headings)).rstrip() + '\n'


def build_visit() -> str:
    L = [r'% Auto-generated by thesis/make_instruments.py --- do not edit by hand.',
         r'% Source: Novel Data/School Visit Proforma - *.docx',
         '',
         r'Two proformas were used on each visit. The lesson observation form was',
         r'completed once per lesson observed, and the outside-of-lessons form once per',
         r'school, covering transitions, break and lunch. Every item is rated 1--5 against',
         r'the anchor descriptions below, with anchors specified at 1, 3 and 5 and even',
         r'values used for intermediate judgements. Visits were made by teams of two or',
         r'three researchers, who completed the forms independently; item scores are',
         r'averaged across researchers and across lessons to give one value per school,',
         r'and \cref{tab:irr_classroom,tab:irr_outside} report agreement between observers.',
         '',
         r'\subsection*{Lesson observation}',
         '']
    lesson = drop_form_header(
        read_docx(DATA / 'School Visit Proforma - Lesson Observations v2.docx'),
        'Section 1')
    L += parse_items(lesson, {'Section 1 – Strictness and Warmth',
                              'Section 2 – Teaching practice'})
    L += ['', r'\subsection*{Outside-of-lessons observation}', '']
    outside = drop_form_header(
        read_docx(DATA / 'School Visit Proforma - Outside of Lessons v2.docx'),
        'Section 1')
    L += parse_items(outside, {'Section 1 - Comparison across lessons',
                               'Section 2 - Transitions',
                               'Section 3 – Break and lunch'})
    return '\n'.join(L).rstrip() + '\n'


# ── Sub-score composition, read out of the scorer ────────────────────────────
#
# The join between the scorer's internal column names and the proforma items
# reproduced in the two appendices above. Any column the scorer uses that is not
# listed here is a mapping this appendix would silently misstate, so it raises.

ITEM_NAMES = {
    # Lesson observation
    'Names_f': "Frequency with which teacher uses pupils' names",
    'Praise_f': 'Frequency of praise',
    'Interact_f': 'Quality of interactions between teachers and pupils',
    # Added to W1 by the visit-item extension (5 Aug 2026), which bought a
    # large inter-observer reliability gain at some cost to discriminant
    # validity; both items are lesson-observation ratings.
    'StudentPart_f': 'Frequency of student-initiated participation',
    'Motivation_f': 'Motivation level of students',
    'Concentration_f': 'Concentration level of students',
    'TeacherPart_f': 'Frequency of teacher-initiated participation',
    'Misbehav_inv': 'Level of misbehaviour tolerated before a first sanction (reversed)',
    'Disruption_inv': 'Frequency of low-level disruption (reversed)',
    'Response_f': 'Response of pupils to sanctions',
    'Respectful_f': 'Extent to which pupils address the teacher respectfully',
    'Questioning_f': 'Frequency of questioning/checking pupil progress',
    'Verbal_f': 'Quality of verbal feedback',
    'Discussion_f': 'Effectiveness of pupil discussion',
    'DiffObs_f': 'Quality of differentiation',
    'Explain_f': 'Clarity of teacher explanation',
    'Outcomes_f': 'Extent to which learning outcomes are achieved',
    'Methods_f': 'Effectiveness of teaching methods',
    'Structure_f': 'Clarity of lesson structure',
    'Resource_f': 'Effectiveness of resource use',
    # Outside-of-lessons observation
    'StudTrans_f': 'Quality of relationships between pupils during transition',
    'InteractBrk_f': 'Quality of non-behaviour related interactions between staff '
                     'and pupils at break',
    'RelBrk_f': 'Quality of relationships between pupils at break',
    'Sanction_f': 'Consistency of use of sanction system',
    'Reward_f': 'Consistency of use of reward system',
    'Corridors_f': 'Calmness of corridors',
    'Arrival_f': 'Arrival time to next lesson',
    'Canteen_f': 'Organisation of canteen/dining hall',
    'Recreat_f': 'Organisation of recreational space',
    # Interview
    'Q5_f': 'Q5 Reward and sanction system',
    'Q6_f': 'Q6 Characteristics of an outstanding teacher',
    'Q7_f': 'Q7 Extracurricular provision',
    'Q8_f': 'Q8 Marking and feedback',
    'Q11_f': 'Q11 Pupil wellbeing',
    'Q12_f': 'Q12 Assessing pupil progress',
    'S1_stmt': 'S1 Sanction systems applied consistently',
    'S2_stmt': 'S2 Reward systems applied consistently',
    'S3_stmt': 'S3 Teacher turnover is low',
    'S4_stmt': 'S4 Staff morale is good',
    'S5_stmt': 'S5 Pupil behaviour in class is generally good',
    'S6_stmt': 'S6 Pupil behaviour outside class is generally good',
    'S7_stmt': 'S7 Pupils feel safe at school',
    'S8_stmt': 'S8 Pupils feel their teachers care',
    'S9_stmt': 'S9 Teachers feel respected by pupils',
    # Yes/no systems
    'yn_centralised_det': 'Centralised detentions',
    'yn_exclusion_room': 'Internal exclusion room',
    'yn_demerits': 'Behaviour points/demerits',
    'yn_line_ups': 'Line-ups',
    'yn_silent_corr': 'Silent corridors',
    'yn_after_school': 'After-school revision',
    'yn_weekend_rev': 'Weekend revision',
    'yn_phone_ban': 'Ban on mobile phones',
    # Interview quality meta-ratings
    'confidence_f': 'Confidence of response',
    'willingness_f': 'Willingness to reveal information',
    'patience_f': 'Interviewee patience',
}

SUBSCORES = [
    ('Warmth',   'W1', 'Teaching warmth', 'Lesson observation'),
    ('Warmth',   'W2', 'School warmth', 'Outside-of-lessons observation'),
    ('Warmth',   'W3', 'Espoused warmth', 'Interview statements'),
    ('Strictness', 'S1', 'In-lesson strictness', 'Lesson observation'),
    ('Strictness', 'S2', 'Out-of-lesson strictness', 'Outside-of-lessons observation'),
    ('Strictness', 'S3', 'Systems count (not a score component)', 'Interview'),
    ('Strictness', 'S4', 'Espoused strictness', 'Interview statements'),
    ('Teaching practice', 'T1', 'Teaching practice (observed)', 'Lesson observation'),
    ('Teaching practice', 'T2', 'Espoused staff climate (there is no espoused teaching score)', 'Interview statements'),
]

SCORER = PROJECT / 'warm_strict_scorer.py'


def _list_literal(node) -> list | None:
    if isinstance(node, ast.List) and all(isinstance(e, ast.Constant) for e in node.elts):
        return [e.value for e in node.elts]
    return None


def subscore_columns() -> dict:
    """Recover each sub-score's item list from warm_strict_scorer.py.

    Two idioms are in use: a named ``_w3_cols``-style list, and a list passed
    inline to ``nanmean_cols``. Both are read so the appendix cannot drift from
    the code that produced the scores.
    """
    tree = ast.parse(SCORER.read_text(encoding='utf-8'))
    named, assigned = {}, {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        tgt = node.targets[0]
        if isinstance(tgt, ast.Name):
            lit = _list_literal(node.value)
            if lit is not None:
                named[tgt.id] = lit
        elif (isinstance(tgt, ast.Subscript) and isinstance(tgt.slice, ast.Constant)):
            key = tgt.slice.value
            if (isinstance(node.value, ast.Call)
                    and getattr(node.value.func, 'id', '') == 'nanmean_cols'
                    and len(node.value.args) == 2):
                arg = node.value.args[1]
                # W1/S1/T1 select their item set through a conditional on the
                # LEGACY_ITEMS switch (the pre-5-Aug item sets are retained for
                # reproduction). The CURRENT set is the `orelse` branch, since
                # the condition reads `... if LEGACY_ITEMS else ...`. Added
                # 14 Aug 2026: before this the parser saw an IfExp, returned
                # nothing for W1, and the whole snippet silently failed to
                # regenerate, leaving the appendix showing the pre-rebuild
                # sub-score definitions.
                if isinstance(arg, ast.IfExp):
                    arg = arg.orelse
                lit = _list_literal(arg)
                if lit is not None:
                    assigned[key] = lit
                elif isinstance(node.value.args[1], ast.Name):
                    assigned[key] = named.get(node.value.args[1].id)

    # Items appended to a named list under `if not LEGACY_ITEMS:` are part of
    # the CURRENT set (Concentration -> S1, TeacherPart -> T1, 5 Aug 2026).
    # Added 19 Aug 2026: the parser read only the list literal, so the appendix
    # showed S1 with four items and T1 with nine while the scorer used five and
    # ten. `.append` under `if USE_KEY_PHRASES:` is the enriched mode and is
    # deliberately NOT read.
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Name)
                and test.operand.id == 'LEGACY_ITEMS'):
            continue
        for stmt in node.body:
            call = getattr(stmt, 'value', None)
            if (isinstance(stmt, ast.Expr) and isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == 'append'
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id in named
                    and len(call.args) == 1
                    and isinstance(call.args[0], ast.Constant)):
                named[call.func.value.id] = named[call.func.value.id] + [call.args[0].value]
    # re-resolve sub-scores that point at a named list, so the appends land
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Subscript)
                and isinstance(node.targets[0].slice, ast.Constant)
                and isinstance(node.value, ast.Call)
                and getattr(node.value.func, 'id', '') == 'nanmean_cols'
                and len(node.value.args) == 2
                and isinstance(node.value.args[1], ast.Name)
                and node.value.args[1].id in named):
            assigned[node.targets[0].slice.value] = named[node.value.args[1].id]

    out = dict(assigned)
    out['S3'] = named['yn_cols']  # summed and rescaled rather than averaged
    missing = [k for _, k, _, _ in SUBSCORES if not out.get(k)]
    if missing:
        raise SystemExit(f'sub-score definitions not found in scorer: {missing}')
    unknown = {c for cols in out.values() for c in cols
               if c not in ITEM_NAMES and not c.endswith('_kw')}
    if unknown:
        raise SystemExit(f'unmapped scorer columns (add to ITEM_NAMES): {sorted(unknown)}')
    return out


def build_scoring_guide() -> str:
    cols = subscore_columns()
    L = [r'% Auto-generated by thesis/make_instruments.py --- do not edit by hand.',
         r'% Source: warm_strict_scorer.py',
         '',
         r'\begin{longtable}{@{}p{0.055\linewidth}p{0.235\linewidth}p{0.62\linewidth}@{}}',
         r'\caption{Composition of the gold-standard sub-scores. Item wording is given'
         r' in full in \cref{app:2A:interview_guide} and \cref{app:2A:visit_protocol}.}',
         r'\label{tab:p1_subscore_items}\\',
         r'\toprule',
         r'& Sub-score & Constituent items \\',
         r'\midrule',
         r'\endfirsthead',
         r'\toprule',
         r'& Sub-score & Constituent items \\',
         r'\midrule',
         r'\endhead',
         r'\bottomrule',
         r'\endfoot']
    group = None
    for construct, key, label, source in SUBSCORES:
        if construct != group:
            if group is not None:
                L.append(r'\addlinespace')
            L.append(r'\multicolumn{3}{@{}l}{\textbf{' + construct + r'}} \\')
            group = construct
        items = '; '.join(ITEM_NAMES[c] for c in cols[key] if not c.endswith('_kw'))
        # the scorer's T2 is reported as SC (staff climate) everywhere in the chapter
        shown = {'T2': 'SC'}.get(key, key)
        L.append(f'{shown} & {label} & ' + r'\textit{' + source + r'.} '
                 + tex_escape(items) + r' \\')
    L += [r'\end{longtable}', '']
    return '\n'.join(L)


TARGETS = {'interview_guide.tex': build_interview,
           'visit_protocol.tex': build_visit,
           'subscore_items.tex': build_scoring_guide}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    stale = False
    for name, fn in TARGETS.items():
        path = SNIPPETS / name
        new  = fn()
        old  = path.read_text(encoding='utf-8') if path.exists() else None
        if args.check:
            if old == new:
                print(f'  in sync: {name}')
            else:
                print(f'  STALE:   {name}')
                stale = True
        else:
            path.write_text(new, encoding='utf-8')
            print(f'Written: snippets/{name}  ({len(new.splitlines())} lines, '
                  f'{len(new):,} chars)')
    if args.check and stale:
        print('Run: python thesis/make_instruments.py')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
