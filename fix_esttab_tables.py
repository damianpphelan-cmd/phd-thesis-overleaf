r"""Restore the \label and \resizebox that esttab cannot emit.

Run this immediately after executing chapter3_analysis.ipynb. Every table the
notebook writes goes through Stata's esttab, which emits a \caption but no
\label and no width control. Both were previously added to each file by hand,
so every re-run of the notebook silently stripped them again -- and because
Chapter 3 \cref{}s all of these tables, a re-run broke the build in eleven
places at once. That happened on 5 August 2026 and is what this script exists
to stop happening a second time.

The label is derived from the filename: tab_<name>.tex -> \label{tab:<name>}.

Run:  python thesis/fix_esttab_tables.py [--check]

--check exits non-zero without writing, for use after a notebook re-run.
"""

import re
import sys
from pathlib import Path

TABLES = Path(__file__).resolve().parent / "tables"

# esttab escapes `_` to `\_` everywhere, including inside the math it was told
# to emit, so a coeflabel of "$W_{12}$" comes back as "$W\_{12}$". Unlike the
# `$`-expansion fault (fixed at source in the notebook, because Stata deletes
# the text before esttab sees it), this one is recoverable here.
MATH = re.compile(r"(?<!\\)\$(.+?)(?<!\\)\$")

# Every table chapter3_analysis.ipynb writes via esttab, and whether the
# chapter wants it scaled to \textwidth. tab_semh_mechanism is narrow enough
# to set at natural size; the rest overflow without it.
ESTTAB = {
    "tab_continuity_robustness": True,
    "tab_enacted_espoused":      True,
    "tab_main_results_s1":       True,
    "tab_main_results_s2":       True,
    "tab_main_results_s3":       True,
    "tab_management_discourse":  True,
    # tab_national_strictness is deliberately absent: it is NOT an esttab table.
    # make_national_strictness.py builds it from a7_estimates.csv and emits its
    # own label and resizebox. The notebook used to write a rival single-panel
    # version to the same path; that esttab call was removed on 5 Aug 2026.
    "tab_robustness_eng":        True,
    "tab_robustness_overall":    True,
    "tab_semh_mechanism":        False,
    "tab_teaching_philosophy":   True,
}


def unescape_math(text: str) -> str:
    """Turn `$W\\_{12}$` back into `$W_{12}$`, leaving prose `\\_` alone."""
    return MATH.sub(lambda m: "$" + m.group(1).replace(r"\_", "_") + "$", text)


def patch(text: str, stem: str, resize: bool) -> str:
    label = rf"\label{{tab:{stem.removeprefix('tab_')}}}"
    lines = unescape_math(text).splitlines()

    if not any(r"\label{" in ln for ln in lines):
        # esttab writes the caption on one line; the label belongs right after.
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith(r"\caption{"):
                lines.insert(i + 1, label)
                break
        else:
            raise SystemExit(f"{stem}: no \\caption to anchor the label to")

    if resize and not any(r"\resizebox" in ln for ln in lines):
        for i, ln in enumerate(lines):
            if ln.startswith(r"\begin{tabular}"):
                lines.insert(i, r"\resizebox{\textwidth}{!}{%")
                break
        else:
            raise SystemExit(f"{stem}: no \\begin{{tabular}} found")
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith(r"\end{tabular}"):
                lines[i] = r"\end{tabular}%"
                lines.insert(i + 1, "}")
                break

    return "\n".join(lines) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    stale = []

    for stem, resize in ESTTAB.items():
        path = TABLES / f"{stem}.tex"
        if not path.exists():
            print(f"  MISSING  {stem}.tex")
            stale.append(stem)
            continue
        before = path.read_text(encoding="utf-8")
        after = patch(before, stem, resize)
        if after == before:
            print(f"  ok       {stem}")
            continue
        stale.append(stem)
        if check:
            print(f"  STRIPPED {stem}  (label and/or resizebox missing)")
        else:
            path.write_text(after, encoding="utf-8")
            print(f"  restored {stem}")

    if check and stale:
        print(f"\n{len(stale)} table(s) need restoring: python thesis/fix_esttab_tables.py")
        return 1
    if not check:
        print(f"\n{len(stale)} restored, {len(ESTTAB) - len(stale)} already intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
