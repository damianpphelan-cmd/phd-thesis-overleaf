"""
Generate thesis/snippets/llm_prompts.tex from the live scoring scripts.

The appendix reproducing the LLM prompts (app:2A:prompts) is generated rather
than typed, so that a change to a rubric in a scoring script cannot silently
diverge from what the thesis claims was administered.

19 Aug 2026 (Damian's ruling): the appendix carries EXACTLY the instruments in
Chapter 2's Table 2.3 and nothing else -- inspection report (prose), behaviour
policy v4 (prose decision procedure, one call), website warmth v18 and strictness v15 (decomposed), website
religious character (classifier), interview strictness v13 and warmth v15
(decomposed, methodological comparisons). Interview teaching and faith
prominence are not in the chapter and are not reproduced. Prompt-version
strings are not printed.

Rubrics and system instructions are read with the ast module rather than by
importing the modules, so nothing in those scripts executes.

Output targets pdflatex with utf8/T1 only: no enumitem, no unicode characters,
no packages beyond what preamble.tex already loads.

Usage:
    python thesis/make_prompts.py            # write the snippet
    python thesis/make_prompts.py --check    # exit 1 if the snippet is stale
"""

import argparse
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

PROJECT = Path(__file__).resolve().parent.parent
OUT     = PROJECT / 'thesis' / 'snippets' / 'llm_prompts.tex'

OFSTED  = PROJECT / 'analyse_ofsted_reports.py'
POLICY  = PROJECT / 'analyse_behaviour_policies_v4.py'   # instrument of record in both chapters
WEB_WARMTH = PROJECT / 'score_website_warmth_v18.py'
WEB_STRICT = PROJECT / 'score_website_strictness_v13.py'  # v15 = v13's flags + a fifth band in code
WEB_IDENT  = PROJECT / 'analyse_website_scores.py'        # religious-character classifier
IV_STRICT  = PROJECT / 'score_interview_strictness.py'
IV_WARMTH  = PROJECT / 'score_interview_warmth_v15.py'

# Reported so the conversion of straight-quoted phrases can be eyeballed.
_CONVERTED: list[str] = []


def _tree(path: Path):
    return ast.parse(path.read_text(encoding='utf-8'))


def literal_from(path: Path, name: str):
    """Value of a module-level assignment to `name`, without importing."""
    for node in _tree(path).body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id == name:
                    v = node.value
                    # `"""...""".strip()` idiom (the website identity rubrics)
                    if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                            and v.func.attr == 'strip' and not v.args
                            and isinstance(v.func.value, ast.Constant)):
                        return v.func.value.value.strip()
                    return ast.literal_eval(v)
    raise KeyError(f'{name} not found in {path.name}')


def system_instruction(path: Path) -> str:
    """The scorer's system instruction, located by its opening words.

    Both scripts pass it as an implicitly-concatenated string literal (to
    `instructions=` for the OpenAI path), which the parser folds into one
    constant. The Anthropic fallback in analyse_ofsted_reports.py carries a
    shorter variant; the longest match is the one actually administered for the
    scores in use.
    """
    found = [n.value for n in ast.walk(_tree(path))
             if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and (n.value.startswith('You are scoring')
                  or n.value.startswith('You are reading a school behaviour policy'))]
    if not found:
        raise KeyError(f'system instruction not found in {path.name}')
    return max(found, key=len)


# ── LaTeX escaping ───────────────────────────────────────────────────────────

UNICODE = {
    '→': r'$\rightarrow$', '←': r'$\leftarrow$',
    '—': '---', '–': '--', '…': r'\ldots{}',
    '‘': '`', '’': "'", '“': '``', '”': "''",
    '≠': r'$\neq$', '£': r'\pounds{}', '°': r'$^{\circ}$', '•': r'\textbullet{}',
    ' ': '~', '×': r'$\times$', '≥': r'$\geq$', '≤': r'$\leq$',
    '·': r'$\cdot$',
}


def tex_escape(s: str) -> str:
    s = s.replace('\\', r'\textbackslash{}')
    for ch in '&%$#_{}':
        s = s.replace(ch, '\\' + ch)
    s = s.replace('~', r'\textasciitilde{}').replace('^', r'\textasciicircum{}')
    for k, v in UNICODE.items():
        s = s.replace(k, v)
    s = s.replace('->', r'$\rightarrow$')
    s = re.sub(r'(?<!-)--(?!-)', '---', s)

    # Straight-quoted example phrases -> the document's ``...'' convention.
    # Guards against possessives: an apostrophe flanked by letters on the
    # relevant side is never a quote mark, and a run spanning a sentence
    # boundary or over 120 characters is assumed to be a mis-pairing.
    def q(m):
        inner = m.group(1)
        if len(inner) > 120 or '; ' in inner or '. ' in inner:
            return m.group(0)
        _CONVERTED.append(inner)
        return '``' + inner + "''"

    s = re.sub(r"(?<![A-Za-z])'([^']+)'(?![A-Za-z])", q, s)

    # Any residual non-ASCII would break inputenc/T1.
    bad = sorted({c for c in s if ord(c) > 127})
    if bad:
        raise ValueError('unmapped non-ASCII: ' + ' '.join(f'U+{ord(c):04X}' for c in bad))
    return s


def paragraphs(s: str) -> str:
    """Render a multi-line instruction, keeping its line structure as paragraphs."""
    parts = [p.strip() for p in s.split('\n') if p.strip()]
    return '\n\n'.join(tex_escape(p) for p in parts)


def anchor_block(title: str, scale: dict) -> list[str]:
    out = [r'\paragraph{' + title + r'}', r'\begin{description}']
    for k in sorted(scale, key=int):
        out.append(r'\item[Score ' + k + r'] ' + tex_escape(scale[k]))
    out += [r'\end{description}', '']
    return out


def rules_block(title: str, rules: list) -> list[str]:
    out = [r'\paragraph{' + title + r'}', r'\begin{enumerate}']
    for r_ in rules:
        out.append(r'\item ' + tex_escape(r_))
    out += [r'\end{enumerate}', '']
    return out


def quote_block(s: str) -> list[str]:
    return [r'\begin{quote}\small', paragraphs(s), r'\end{quote}', '']


def flag_section(title: str, path: Path, ladder: str | None) -> list[str]:
    """A decomposed instrument, condensed to its operative content.

    Emits the construct, the flag questions verbatim, and the banding rule:
    the hand-written `ladder` prose where supplied, otherwise the scorer's own
    band_labels. Exclusion clauses and hard rules are summarised by count and
    left to the script, per the concision note in the preamble above.
    """
    rub = literal_from(path, 'RUBRIC')
    out = [r'\subsection*{' + tex_escape(title) + r'}', '',
           r'Construct:',
           tex_escape(rub['construct']), '',
           r'\paragraph{The questions}', r'\begin{enumerate}\small']
    for name, q in rub['flags'].items():
        out.append(r'\item \textit{' + tex_escape(name.replace('_', ' '))
                   + r'.} ' + tex_escape(q))
    out += [r'\end{enumerate}', '']
    out += [r'\paragraph{The banding rule}']
    if ladder:
        out += [tex_escape(ladder), '']
    elif 'band_labels' in rub:
        out += [r'\begin{description}']
        for k in sorted(rub['band_labels'], key=str):
            out.append(r'\item[Band ' + tex_escape(str(k)) + r'] '
                       + tex_escape(rub['band_labels'][k]))
        out += [r'\end{description}', '']
    n_excl = len(rub.get('does_not_count', []) or [])
    n_hard = len(rub.get('hard_rules', []) or [])
    out += [tex_escape(
        f'The instrument additionally carries {n_excl or "its"} exclusion '
        f'clauses and {n_hard} hard rules, applied in code after the model answers.'),
        '']
    return out


# ── Document ─────────────────────────────────────────────────────────────────

def build() -> str:
    of_rub = literal_from(OFSTED, 'ACTIVE_RUBRIC')
    bp_rub = literal_from(POLICY, 'ACTIVE_RUBRIC')
    of_sys, bp_sys = system_instruction(OFSTED), system_instruction(POLICY)
    rc_rub = literal_from(WEB_IDENT, 'RELIGIOUS_CHARACTER_RUBRIC')
    # the rubric is hard-wrapped in the source; rejoin lines within a paragraph
    rc_rub = re.sub('(?<!\n)\n(?!\n)[ \t]*', ' ', rc_rub)

    L = [r'% Auto-generated by thesis/make_prompts.py --- do not edit by hand.',
         r'% Source: the live scoring scripts (see make_prompts.py)',
         '']

    L += [
        r'Every scorer shares a prompt architecture. A system instruction establishes',
        r'the task, the scoring procedure and the output contract; the substantive',
        r'content is delivered as a single JSON payload carrying the school',
        r'identifiers, the extracted document text, the full rubric, and a',
        r'specification of the required output fields. The model must return',
        r"schema-valid JSON --- through the provider's structured-output facility",
        r'where available, and through a forced tool call otherwise --- so that no',
        r'free-text parsing is involved. Sampling temperature is zero. Each request is',
        r'keyed by a hash of the model name, the rubric text, the schema and the',
        r'payload, so re-running a scorer over unchanged documents returns cached',
        r'scores rather than silently re-scoring them.',
        '',
        r'The inspection-report rubric requires the model to state, for every score,',
        r'why the score is not one point higher and not one point lower, and applies a',
        r'borderline rule: where evidence is genuinely ambiguous, the lower score is',
        r'taken. A score below the midpoint requires positive evidence of a',
        r'deficiency --- silence on behaviour, or on relationships, is scored as',
        r'unremarkable rather than as poor. The behaviour-policy instrument reaches',
        r'the same position by construction: a policy with no positive content scores',
        r'1 on warmth, and one that describes provision without relational guidance',
        r'scores 3, so a document that does not discuss warmth cannot score low. This',
        r'matters for interpreting the warmth null in \cref{tab:source_criterion}: the',
        r'observed compression at the midpoint is the designed response to silence,',
        r'not a scoring failure.',
        '',
        r'\subsection*{Inspection reports}',
        '',
        r'System instruction:',
        '',
    ]
    L += quote_block(of_sys)
    L += [
        r'The payload supplies the URN and school name, the inspection date, the',
        r'report type with any stated grade removed from its wording, and the',
        r'grade-stripped uniform report body: the substantive inspection narrative',
        r'with boilerplate, primary-phase and sixth-form-specific passages removed',
        r'and every stated grade deleted, so that the model cannot see the',
        r'inspection verdict in anything it is given. For an',
        r'all-through school a further note instructs the model to score only the',
        r'secondary provision described in the remaining text. The required output is a',
        r'score, a confidence level and a reason for each of strictness, warmth and',
        r'teaching, plus a manual-review flag.',
        '',
    ]
    L += anchor_block('Strictness scale anchors', of_rub['strictness'])
    L += anchor_block('Warmth scale anchors', of_rub['warmth'])
    L += rules_block('Scoring rules: strictness and warmth', of_rub['hard_rules'])
    L += anchor_block('Teaching scale anchors', of_rub['teaching'])
    L += rules_block('Scoring rules: teaching', of_rub['teaching_hard_rules'])

    L += [
        r'\subsection*{Behaviour policy documents}',
        '',
        r'The behaviour-policy instrument reads the whole policy once and scores',
        r'both constructs in that one call, but it does not ask the model for a',
        r'band. The model answers a fixed sequence of yes/no questions, two of which',
        r'must be evidenced by a verbatim quotation that is checked against the',
        r'policy text, and the band is computed from the answers by the decision',
        r'procedure below, which is applied in code. The opening of the system',
        r'instruction:',
        '',
    ]
    L += quote_block(bp_sys)
    L += [
        r'The instruction then reproduces, for each construct, what is being',
        r'measured, the decision procedure, the questions and the band summaries',
        r'given below, followed by the scoring rules. The payload supplies the URN,',
        r'school name and document title, and the extracted policy text.',
        '',
    ]
    for dim, label in (('strictness', 'Strictness'), ('warmth', 'Warmth')):
        rub = bp_rub[dim]
        L += [r'\paragraph{' + label + r': what is measured}', tex_escape(rub['construct']), '']
        L += [r'\paragraph{' + label + r': decision procedure}', r'\begin{enumerate}']
        L += [r'\item ' + tex_escape(s) for s in rub['procedure']]
        L += [r'\end{enumerate}', '']
        L += [r'\paragraph{' + label + r': the questions}', r'\begin{enumerate}\small']
        L += [r'\item ' + tex_escape(q['q']) for q in rub['questions']]
        L += [r'\end{enumerate}', '']
        L += anchor_block(label + ': band summaries', rub['bands'])
    L += rules_block('Scoring rules', bp_rub['hard_rules'])

    L += [
        r'\subsection*{The decomposed instruments}',
        '',
        r'The website and interview instruments do not ask the model for a band.',
        r'Each asks a fixed set of factual questions about one document; every',
        r'affirmative answer must be supported by a verbatim quotation, which is',
        r'checked against the document before it counts; and the band is assigned',
        r'by a fixed rule in ordinary code. For concision, the question texts and',
        r'banding rules are reproduced here in their operative form; each',
        r'instrument also carries exclusion clauses (what does not count) and',
        r'tie-break rules, which are stated in full in its scoring script in the',
        r'project repository.',
        '',
    ]

    L += flag_section(
        'Website warmth', WEB_WARMTH,
        'A site with no verified relational referent is band 1; one or more '
        'verified referents reach band 2; a claim that recurs or is '
        'intensified reaches band 3; a described arrangement (a route to a '
        'named person, a named relational practice, described availability) '
        'reaches band 4; a narrated instance, pupil voice, or a parent '
        'witnessed account reaches band 5. The highest finding wins, and a '
        'site that presents itself principally through results is capped.')

    L += flag_section(
        'Website strictness', WEB_STRICT,
        'A site that expresses no expectation of pupils is band 1; a virtue '
        'without a conduct is band 2; a named conduct is band 3; conduct '
        'demanded of pupils is band 4. Negative findings (demands attached '
        'only to virtues, purely academic expectations, conduct words only in '
        'navigation or a values list) cap the band unless the site has '
        'specified particulars. Band 5 is reached where the site both names a '
        'small particular of conduct (a uniform detail, a phone rule, a '
        'punctuality time) and states a consequence; both are facts the '
        'questions above already establish, and the rung is assigned in code.')

    L += [
        r'\subsection*{Website religious character}',
        '',
        r'A classifier reads the same crawl text and returns one category. Its',
        r'rubric is reproduced in full:',
        '',
    ]
    L += quote_block(rc_rub)

    L += flag_section('Interview strictness', IV_STRICT, None)
    L += flag_section('Interview warmth', IV_WARMTH, None)
    L += [
        r'The two interview-transcript instruments are methodological comparisons',
        r'only: the espoused scores of record come from the statement battery',
        r'(\cref{app:2A:interview_guide}), not from the transcripts.',
        '',
    ]

    return '\n'.join(L).rstrip() + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='exit 1 if the snippet differs from the scripts')
    ap.add_argument('--show-quotes', action='store_true',
                    help='list the straight-quoted runs converted to ``...\'\'')
    args = ap.parse_args()

    new = build()
    old = OUT.read_text(encoding='utf-8') if OUT.exists() else None

    if args.show_quotes:
        for c in sorted(set(_CONVERTED), key=len, reverse=True):
            print(f'  [{len(c):3d}] {c}')
        return 0

    if args.check:
        if old == new:
            print('llm_prompts.tex is in sync with the scoring scripts.')
            return 0
        print('STALE: llm_prompts.tex does not match the current rubrics.')
        print('Run: python thesis/make_prompts.py')
        return 1

    OUT.write_text(new, encoding='utf-8')
    print(f'Written: {OUT.relative_to(PROJECT)}  ({len(new.splitlines())} lines, '
          f'{len(new):,} chars)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
