"""
Generate thesis/snippets/llm_prompts.tex from the live scoring scripts.

The appendix reproducing the LLM prompts (app:2A:prompts) is generated rather
than typed, so that a change to a rubric in analyse_ofsted_reports.py or
analyse_behaviour_policies_v3.py cannot silently diverge from what the thesis
claims was administered.

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
POLICY  = PROJECT / 'analyse_behaviour_policies_v3.py'

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
                    return ast.literal_eval(node.value)
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
             and n.value.startswith('You are scoring')]
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


# ── Document ─────────────────────────────────────────────────────────────────

def build() -> str:
    of_rub, of_ver = literal_from(OFSTED, 'ACTIVE_RUBRIC'), literal_from(OFSTED, 'PROMPT_VERSION')
    bp_rub, bp_ver = literal_from(POLICY, 'ACTIVE_RUBRIC'), literal_from(POLICY, 'PROMPT_VERSION')
    of_sys, bp_sys = system_instruction(OFSTED), system_instruction(POLICY)

    L = [r'% Auto-generated by thesis/make_prompts.py --- do not edit by hand.',
         r'% Source: analyse_ofsted_reports.py, analyse_behaviour_policies_v3.py',
         '']

    L += [
        r'Both scorers share a prompt architecture. A system instruction establishes',
        r'the task, the scoring procedure and the output contract; the substantive',
        r'content is delivered as a single JSON payload carrying the school',
        r'identifiers, the extracted document text, the full rubric, and a',
        r'specification of the required output fields. The model must return',
        r"schema-valid JSON --- through the provider's structured-output facility",
        r'where available, and through a forced tool call otherwise --- so that no',
        r'free-text parsing is involved. Sampling temperature is zero. Each request is',
        r'keyed by a SHA-256 hash of the model name, prompt version, schema version and',
        r'payload, so re-running a scorer over unchanged documents returns cached',
        r'scores rather than silently re-scoring them.',
        '',
        r'Both rubrics require the model to state, for every score, why the score is',
        r'not one point higher and not one point lower. Both apply the same borderline',
        r'rule: where evidence is genuinely ambiguous, the lower score is taken. The',
        r'asymmetric exception in both is that a score below the midpoint requires',
        r'positive evidence of a deficiency --- silence on behaviour, or on',
        r'relationships, is scored as unremarkable rather than as poor. This matters',
        r'for interpreting the warmth null in \cref{sec:p1_text_valid}: the rubrics are',
        r'constructed so that a document which simply does not discuss warmth cannot',
        r'produce a low warmth score, and the observed compression at the midpoint is',
        r'therefore the designed response to silence, not a scoring failure.',
        '',
        r'\subsection*{Ofsted reports}',
        '',
        r'Prompt version \texttt{' + tex_escape(of_ver) + r'}. System instruction:',
        '',
    ]
    L += quote_block(of_sys)
    L += [
        r'The payload supplies the URN and school name, inspection date and report',
        r"type, Ofsted's own behaviour and attitudes judgement (as context only, and",
        r'explicitly not as a cap on the score), the opening summary, the',
        r'improvement-areas section, and the substantive inspection narrative with',
        r'boilerplate, primary-phase and sixth-form passages removed. For an',
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
        r'Prompt version \texttt{' + tex_escape(bp_ver) + r'}. The system instruction',
        r'carries the scoring procedure itself, as an explicit decision tree rather than',
        r'as holistic guidance:',
        '',
    ]
    L += quote_block(bp_sys)
    L += [
        r'The payload supplies the URN, school name and the title of the selected',
        r'document; a set of keyword-matched passages, explicitly labelled as',
        r'preliminary signals to be checked against the full text rather than scored on',
        r'directly; a flag and term list recording whether specialist-support vocabulary',
        r'is present; and the extracted policy text. The required output is a score, a',
        r'confidence level and a reason for each of strictness and warmth, plus a',
        r'manual-review flag.',
        '',
    ]
    L += anchor_block('Strictness scale anchors', bp_rub['strictness'])
    L += anchor_block('Warmth scale anchors', bp_rub['warmth'])
    L += rules_block('Scoring rules', bp_rub['hard_rules'])

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
