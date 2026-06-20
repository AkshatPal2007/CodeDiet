"""Output renderers for CodeDiet findings.

The reporter is the only module that knows how to format findings for display.
Detectors never produce formatted output themselves.
"""

from __future__ import annotations

import json
import sys

from codediet.models import Finding


def report_text(findings: list[Finding], files_scanned: int) -> None:
    """Render findings as human-readable plain text to stdout."""
    print(f"Files scanned: {files_scanned}")
    print()

    wrappers = [f for f in findings if f.kind == "wrapper"]

    print(f"Wrapper Functions Found: {len(wrappers)}")

    if not wrappers:
        return

    print()
    for finding in wrappers:
        print("WRAPPER")
        print(f"  {finding.file}:{finding.line}")
        print(f"  {finding.function} -> {finding.target}")
        print()


def report_json(findings: list[Finding]) -> None:
    """Render findings as JSON to stdout."""
    output: dict[str, list[dict]] = {"wrappers": []}

    for f in findings:
        if f.kind == "wrapper":
            output["wrappers"].append(
                {
                    "file": f.file,
                    "line": f.line,
                    "function": f.function,
                    "target": f.target,
                }
            )

    json.dump(output, sys.stdout, indent=2)
    print()  # trailing newline
