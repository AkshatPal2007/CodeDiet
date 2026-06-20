"""Output renderers for CodeDiet findings.

The reporter is the only module that knows how to format findings for display.
Detectors never produce formatted output themselves.

Per CLAUDE.md v0.2 §4 and §8, terminal and JSON output must visually separate
FACTS (mechanically verifiable) from REVIEW RECOMMENDATIONS (heuristic signals)
so users can immediately tell which findings are certainties and which are
\"go look at this\" signals.
"""

from __future__ import annotations

import json
import sys

from codediet.models import Finding, FindingClass


def report_text(findings: list[Finding], files_scanned: int) -> None:
    """Render findings as human-readable plain text to stdout.

    Findings are split into two clearly labelled sections:
      - FACTS: deterministic, mechanically defensible.
      - REVIEW RECOMMENDATIONS: heuristic signals worth a manual look.
    """
    print(f"Files scanned: {files_scanned}")
    print()

    facts = [f for f in findings if f.classification == FindingClass.FACT]
    reviews = [f for f in findings if f.classification == FindingClass.REVIEW]

    # ── FACTS section ────────────────────────────────────────────────────────
    print(f"FACTS — Mechanically Verifiable ({len(facts)} found)")
    if facts:
        print()
        for finding in facts:
            label = finding.detector.upper().replace("_", " ")
            print(f"  [{label}]")
            print(f"    {finding.file}:{finding.line}")
            print(f"    {finding.message}")
            print()
    else:
        print("  (none)\n")

    # ── REVIEW RECOMMENDATIONS section ───────────────────────────────────────
    print(f"REVIEW RECOMMENDATIONS — Heuristic Signals ({len(reviews)} found)")
    if reviews:
        print()
        for finding in reviews:
            label = finding.detector.upper().replace("_", " ")
            print(f"  [{label}]")
            print(f"    {finding.file}:{finding.line}")
            print(f"    {finding.message}")
            print()
    else:
        print("  (none)\n")


def report_json(findings: list[Finding]) -> None:
    """Render findings as JSON to stdout.

    Top-level keys are 'facts' and 'review_recommendations', matching the
    Fact/Review classification model from CLAUDE.md v0.2 §4.
    """
    output: dict[str, list[dict]] = {
        "facts": [],
        "review_recommendations": [],
    }

    for f in findings:
        entry = {
            "detector": f.detector,
            "file": f.file,
            "line": f.line,
            "message": f.message,
            "evidence": f.evidence,
        }
        if f.classification == FindingClass.FACT:
            output["facts"].append(entry)
        else:
            output["review_recommendations"].append(entry)

    json.dump(output, sys.stdout, indent=2)
    print()  # trailing newline
