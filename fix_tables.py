#!/usr/bin/env python3
"""Post-process estout-generated LaTeX tables.

Stata's `esttab` writes tables that are almost, but not quite, usable in the
thesis. Two things go wrong every time a table is regenerated:

  1. No `\\label{}` is emitted, so every `\\cref{tab:...}` renders as `??`.
  2. Underscores inside math mode are escaped (`$W\\_{12}$`), so subscripts
     render as literal underscores.

Rather than hand-patching the output after every Stata run, run this script.
It is idempotent: running it twice changes nothing.

    python thesis/fix_tables.py            # fix thesis/tables/*.tex in place
    python thesis/fix_tables.py --check    # report problems, change nothing

Label convention: `tab_foo.tex` gets `\\label{tab:foo}`. Files needing a
different label are listed in LABEL_OVERRIDES.

The script also *reports* (but never silently rewrites) a third class of
defect, which took down the whole build once: a table written by a script
using a non-raw Python string, so that `\\a` became a BEL byte and `\\\\`
collapsed to a single backslash. See `audit()`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TABLES_DIR = Path(__file__).resolve().parent / "tables"

# Files whose label does not follow the tab_foo.tex -> tab:foo convention.
LABEL_OVERRIDES = {
    "tab_representativeness": "tab:2A:representativeness",
}

LABEL_RE = re.compile(r"\\label\{[^}]*\}")
CAPTION_RE = re.compile(r"\\caption\{")
MATH_RE = re.compile(r"\$([^$]*?)\$")

# Files this script must never rewrite: tab_p1_grid.tex is owned by
# make_grid_numbers.py and formatted by hand there.
DO_NOT_TOUCH = {"tab_p1_grid"}

# The thesis float convention (1 Sep 2026): the title sits above the body
# and the notes below it, which is what economics journals do. Inside every
# table float the order is caption + label, then the tabular, then any notes
# block. move_caption_above() enforces it and is idempotent, so producers
# call it on their output and this script sweeps every table as a backstop
# for producers that live outside thesis/. Until this date the caption sat
# below the body; move_caption_below() is kept because producers still call
# it, and it now simply delegates.
# The float opener: egin{table}, its placement option and any
# \centering. The caption is placed immediately after this.
TABLE_OPEN_RE = re.compile(
    r"\\begin\{table\*?\}(?:\[[^\]]*\])?"
    r"(?:\s*\\centering)?")
TABULAR_OPEN_RE = re.compile(r"\\begin\{(?:tabularx?|longtable|threeparttable)\*?\}")
TABULAR_END_RE = re.compile(r"\\end\{(?:tabularx?|longtable|threeparttable)\*?\}")


def read(path: Path) -> tuple[str, str]:
    """Read without newline translation, and report the file's own newline.

    esttab writes LF even on Windows. Python's text mode would rewrite the whole
    file as CRLF on save, turning a one-line label insertion into a diff that
    touches every line of every table.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
    return text, "\r\n" if "\r\n" in text else "\n"


def write(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def expected_label(stem: str) -> str:
    if stem in LABEL_OVERRIDES:
        return LABEL_OVERRIDES[stem]
    return "tab:" + stem[len("tab_"):] if stem.startswith("tab_") else "tab:" + stem


def find_caption_end(text: str, start: int) -> int:
    """Return the index just past the closing brace of \\caption{...}."""
    i = text.index("{", start)
    depth = 0
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced braces in \\caption")


def add_label(text: str, label: str, nl: str = "\n") -> tuple[str, bool]:
    if LABEL_RE.search(text):
        return text, False
    m = CAPTION_RE.search(text)
    if not m:
        return text, False
    end = find_caption_end(text, m.start())
    return text[:end] + nl + "\\label{" + label + "}" + text[end:], True


def move_caption_below(text: str, nl: str = "\n") -> tuple[str, bool]:
    """Deprecated alias for move_caption_above.

    The convention was inverted on 1 Sep 2026: the title now sits
    above the body and the notes below it. This alias is kept so that
    any producer still calling the old name complies with the current
    convention rather than silently reverting the sweep.
    """
    return move_caption_above(text, nl)


def move_caption_above(text: str, nl: str = "\n") -> tuple[str, bool]:
    """Move \\caption{...} (+ adjacent \\label) to the top of the float.

    Economics convention: the title goes above the table and the notes
    below it. The caption is placed immediately after \\begin{table}
    and its \\centering, which is robust to whatever wraps the body
    (\\resizebox, \\small, a \\def). Any notes block is left where it
    is, after the body, which puts it below. Files with no caption or
    no float are left alone. Idempotent.
    """
    m = CAPTION_RE.search(text)
    om = TABLE_OPEN_RE.search(text)
    if not m or not om:
        return text, False

    cap_start = m.start()
    # The canonical position is immediately after the float opener, not
    # merely somewhere above the body. Producers that emit \def\sym and
    # \small first left the caption below them, and since the preamble
    # sets no caption font, a preceding \small shrank the title: ten
    # committed tables carried a smaller title than the rest. Normalising
    # to the top of the float fixes both the ordering and the font.
    if not text[om.end():cap_start].strip():
        return text, False  # already at the top of the float

    cap_end = find_caption_end(text, cap_start)
    lm = re.match(r"\s*\\label\{[^}]*\}", text[cap_end:])
    block_end = cap_end + lm.end() if lm else cap_end
    block = text[cap_start:block_end]

    rm_start = cap_start
    line_start = text.rfind(nl, 0, cap_start) + 1
    if text[line_start:cap_start].strip() == "":
        rm_start = line_start
    rm_end = block_end
    nl_after = text.find(nl, block_end)
    if nl_after != -1 and text[block_end:nl_after].strip() == "":
        rm_end = nl_after + 1

    remainder = text[:rm_start] + text[rm_end:]
    om2 = TABLE_OPEN_RE.search(remainder)
    if not om2:
        return text, False
    ins = om2.end()
    if ins < len(remainder) and remainder[ins] == nl:
        ins += 1
    return remainder[:ins] + block + nl + remainder[ins:], True


def caption_to_title(text: str, title: str,
                     keep_first: bool = False) -> str:
    """Shorten a table's caption to a title, moving the detail into Notes.

    Journal convention (adopted 29 Aug 2026): the caption is a short title;
    everything explanatory lives in the notes minipage. This helper rewrites
    the caption to `title` and prepends the old caption's remaining text to
    the notes, creating a notes minipage when the table has none. By default
    the old caption's first sentence is dropped (it is normally the title in
    longer form); pass keep_first=True when it carries real content.
    Idempotent once applied, since a title-length caption is left alone by
    the callers' own length checks -- callers should apply it exactly once
    to a freshly composed table.
    """
    m = CAPTION_RE.search(text)
    if not m:
        return text
    end = find_caption_end(text, m.start())
    old = " ".join(text[m.end():end - 1].split())
    moved = old
    if not keep_first:
        sm = re.match(r".+?[.!?](?:\s+|$)(.*)$", old, re.S)
        moved = sm.group(1).strip() if sm else ""
    text = text[:m.start()] + "\\caption{" + title + "}" + text[end:]
    if not moved:
        return text
    nm = re.search(r"(\\textit\{Notes[:.]?\}:?\s*)", text)
    if nm:
        return (text[:nm.end()] + moved + " " + text[nm.end():])
    block = ("\\begin{minipage}{\\linewidth}\n\\smallskip\n"
             "\\footnotesize\\textit{Notes:} " + moved
             + "\n\\end{minipage}\n")
    i = text.rfind("\\end{table}")
    assert i != -1, "no end{table}"
    return text[:i] + block + text[i:]


def unescape_math(text: str) -> tuple[str, bool]:
    changed = False

    def repl(m: re.Match) -> str:
        nonlocal changed
        inner = m.group(1)
        if "\\_" in inner:
            changed = True
            return "$" + inner.replace("\\_", "_") + "$"
        return m.group(0)

    return MATH_RE.sub(repl, text), changed


def audit(text: str) -> list[str]:
    """Report corruption this script must not try to repair automatically.

    tab_outcome_stats.tex was once written by a script using a non-raw Python
    string. Every `\\a` became a BEL byte (0x07) -- `\\addlinespace` printed as
    `ddlinespace`, `\\approx` as `pprox` -- and every `\\\\` row terminator
    collapsed to a single backslash, so no row ever ended. BEL is an invalid
    character to TeX and the mangled alignment is fatal, so the thesis produced
    no PDF at all. The damage is not mechanically reversible (the eaten letter
    is gone), so this only reports: the fix is to regenerate from source.

    Note that a BEL byte is *not* caught by a non-ASCII scan -- 0x07 < 128.

    Tab and CR are excluded: this file is read with newline="" so that line
    endings survive round-tripping, which leaves a CR on every line of a CRLF
    file.
    """
    problems = []
    for i, line in enumerate(text.split("\n"), 1):
        bad = sorted({hex(ord(c)) for c in line
                      if ord(c) < 32 and c not in "\t\r"})
        if bad:
            problems.append(f"line {i}: control characters {bad} "
                            f"(a non-raw Python string ate an escape)")
        stripped = line.rstrip()
        if stripped.endswith("\\") and not stripped.endswith("\\\\"):
            problems.append(f"line {i}: row ends in a single backslash: "
                            f"...{stripped[-40:]!r}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report problems without modifying files")
    args = ap.parse_args()

    if not TABLES_DIR.is_dir():
        print("no tables directory at %s" % TABLES_DIR, file=sys.stderr)
        return 2

    problems = 0
    corrupt = 0
    for path in sorted(TABLES_DIR.glob("*.tex")):
        original, nl = read(path)

        # Corruption is reported first and blocks nothing else: a file in this
        # state needs regenerating from source, not patching.
        broken = audit(original)
        if broken:
            corrupt += 1
            print("CORRUPT   %s -- regenerate from source, do not hand-patch"
                  % path.name)
            for b in broken[:6]:
                print("            " + b)
            if len(broken) > 6:
                print("            ... and %d more" % (len(broken) - 6))
            continue

        if path.stem in DO_NOT_TOUCH:
            continue

        text, labelled = add_label(original, expected_label(path.stem), nl)
        text, unescaped = unescape_math(text)
        text, moved = move_caption_above(text, nl)

        notes = []
        if labelled:
            notes.append("added \\label{%s}" % expected_label(path.stem))
        if unescaped:
            notes.append("unescaped math subscripts")
        if moved:
            notes.append("moved caption to the top of the float")
        if not notes:
            continue

        problems += 1
        verb = "would fix" if args.check else "fixed"
        print("%s %-34s %s" % (verb, path.name, "; ".join(notes)))
        if not args.check:
            write(path, text)

    if problems == 0 and corrupt == 0:
        print("all %d tables clean" % len(list(TABLES_DIR.glob("*.tex"))))
    return 1 if (corrupt or (args.check and problems)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
