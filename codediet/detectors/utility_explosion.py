"""Utility Explosion Detector.

Detects projects that have accumulated an unusually large number of
utility-named Python modules. This is a low-confidence, project-level
heuristic signal — not a claim that any specific file is unnecessary or
should be removed.

A finding fires when the total count of utility-named modules in the
scanned path meets or exceeds a configurable threshold (default: 3).

Per CLAUDE.md §7.6:
  - Output wording: "Review Utility Growth" — never "remove this file."
  - Reliability: Low (documented to users explicitly as lowest-confidence).
  - Output class: REVIEW — always, never FACT.

Unlike per-file detectors (wrappers, abandoned), this detector operates
on the full list of display paths produced by the scanner, not on a
single AST tree. It is called once per scan with the complete file list.
"""

from __future__ import annotations

import os

from codediet.models import Finding, FindingClass

# ---------------------------------------------------------------------------
# Utility-module basenames — common catch-all file names that signal
# a project is accumulating miscellaneous helper code without structure.
# ---------------------------------------------------------------------------
_UTILITY_BASENAMES: frozenset[str] = frozenset(
    {
        "utils.py",
        "util.py",
        "helpers.py",
        "helper.py",
        "common.py",
        "shared.py",
        "misc.py",
        "utilities.py",
        "tools.py",
        "funcs.py",
    }
)

# Minimum number of utility-named files before the detector fires.
# A single utils.py is unremarkable; three or more signals accumulation.
_DEFAULT_THRESHOLD: int = 3


def detect(
    display_paths: list[str],
    threshold: int = _DEFAULT_THRESHOLD,
) -> list[Finding]:
    """Detect utility-module proliferation across the scanned project.

    Args:
        display_paths: Relative display paths of all scanned Python files.
                       These are the same paths shown in terminal output.
        threshold:     Minimum number of utility-named modules required
                       before any findings are emitted. Default is 3.

    Returns:
        One Finding per matched utility-named file, if the total count
        meets or exceeds ``threshold``. Returns an empty list otherwise.
    """
    matched: list[str] = [
        dp for dp in display_paths if os.path.basename(dp) in _UTILITY_BASENAMES
    ]

    if len(matched) < threshold:
        return []

    count = len(matched)
    findings: list[Finding] = []
    for fp in matched:
        findings.append(
            Finding(
                detector="utility_explosion",
                classification=FindingClass.REVIEW,
                file=fp,
                line=1,
                message=(
                    f"Project has {count} utility-named module"
                    f"{'s' if count != 1 else ''}"
                    f" — Review Utility Growth"
                ),
                evidence={
                    "utility_files": matched,
                    "count": count,
                    "threshold": threshold,
                },
            )
        )
    return findings
