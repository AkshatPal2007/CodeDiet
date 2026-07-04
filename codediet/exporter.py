"""Findings exporter for CodeDiet — writes a portable findings file.

Per CLAUDE.md v0.3 §5.2:
  - Writes findings grouped by classification (Fact / Review) with file:line
    references identical to terminal output.
  - Always writes the file even when findings are empty — a clean run is
    itself useful information (e.g. for a PR comment or changelog).
  - Facts and Review Recommendations are ALWAYS separate sections.
  - Supports Markdown (.md) and plain text (.txt) output.
  - Appends a generated prompt section when prompt_text is supplied.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from codediet.models import Finding, FindingClass


def export_findings(
    findings: list[Finding],
    output_path: str | Path,
    repo_path: str | Path,
    files_scanned: int,
    prompt_text: str | None = None,
) -> None:
    """Write findings to *output_path* in Markdown or plain-text format.

    Args:
        findings:      All findings from the scan (may be empty).
        output_path:   Destination file.  Extension determines format:
                       ``.md``  → Markdown, anything else → plain text.
        repo_path:     The scanned path, used in the file header.
        files_scanned: Number of Python files that were analysed.
        prompt_text:   If supplied, appended as a final section after the
                       summary.  Pass ``None`` when ``--prompt`` is absent.

    Returns:
        None — the file is written to disk; callers need not capture output.
    """
    output_path = Path(output_path)
    is_markdown = output_path.suffix.lower() == ".md"

    facts = [f for f in findings if f.classification == FindingClass.FACT]
    reviews = [f for f in findings if f.classification == FindingClass.REVIEW]

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    repo_label = str(repo_path)

    lines: list[str] = []

    if is_markdown:
        lines += _render_markdown(
            facts, reviews, repo_label, timestamp, files_scanned, prompt_text
        )
    else:
        lines += _render_text(
            facts, reviews, repo_label, timestamp, files_scanned, prompt_text
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Markdown renderer
# ─────────────────────────────────────────────────────────────────────────────


def _render_markdown(
    facts: list[Finding],
    reviews: list[Finding],
    repo_label: str,
    timestamp: str,
    files_scanned: int,
    prompt_text: str | None,
) -> list[str]:
    lines: list[str] = []

    lines.append(f"# CodeDiet Findings — {repo_label}")
    lines.append(f"Generated: {timestamp}")
    lines.append("Detector(s) run: wrapper")
    lines.append("")

    # ── Facts section ─────────────────────────────────────────────────────────
    lines.append("## Facts")
    lines.append("(deterministic — these are structurally true as written)")
    lines.append("")
    if facts:
        # Group by detector label for future multi-detector support
        for finding in facts:
            label = finding.detector.replace("_", " ").title()
            lines.append(f"### {label}")
            lines.append(f"- `{finding.file}:{finding.line}` — {finding.message}")
            lines.append("")
    else:
        lines.append("_None in this run._")
        lines.append("")

    # ── Review Recommendations section ────────────────────────────────────────
    lines.append("## Review Recommendations")
    lines.append("(heuristic signals — worth a look, not a claim about the outcome)")
    lines.append("")
    if reviews:
        for finding in reviews:
            label = finding.detector.replace("_", " ").title()
            lines.append(f"### {label}")
            lines.append(f"- `{finding.file}:{finding.line}` — {finding.message}")
            lines.append("")
    else:
        lines.append("_None in this run._")
        lines.append("")

    # ── Summary ───────────────────────────────────────────────────────────────
    lines.append("---")
    lines.append("## Summary")
    lines.append(f"- {len(facts)} Facts")
    lines.append(f"- {len(reviews)} Review Recommendations")
    lines.append(f"- {files_scanned} files scanned")

    # ── Optional LLM hand-off prompt ─────────────────────────────────────────
    if prompt_text is not None:
        lines.append("")
        lines.append("---")
        lines.append("## LLM Hand-off Prompt")
        lines.append(
            "_Copy the block below and paste it into your own coding assistant._"
        )
        lines.append("")
        lines.append("```text")
        lines.append(prompt_text)
        lines.append("```")

    return lines


# ─────────────────────────────────────────────────────────────────────────────
# Plain-text renderer
# ─────────────────────────────────────────────────────────────────────────────


def _render_text(
    facts: list[Finding],
    reviews: list[Finding],
    repo_label: str,
    timestamp: str,
    files_scanned: int,
    prompt_text: str | None,
) -> list[str]:
    lines: list[str] = []

    lines.append(f"CodeDiet Findings — {repo_label}")
    lines.append(f"Generated: {timestamp}")
    lines.append("Detector(s) run: wrapper")
    lines.append("")

    # ── Facts section ─────────────────────────────────────────────────────────
    lines.append("FACTS (deterministic — these are structurally true as written)")
    lines.append("-" * 70)
    if facts:
        for finding in facts:
            lines.append(f"  [{finding.detector.upper()}]")
            lines.append(f"    {finding.file}:{finding.line}")
            lines.append(f"    {finding.message}")
            lines.append("")
    else:
        lines.append("  None in this run.")
        lines.append("")

    # ── Review Recommendations section ────────────────────────────────────────
    lines.append(
        "REVIEW RECOMMENDATIONS (heuristic signals — worth a look, not a claim)"
    )
    lines.append("-" * 70)
    if reviews:
        for finding in reviews:
            lines.append(f"  [{finding.detector.upper()}]")
            lines.append(f"    {finding.file}:{finding.line}")
            lines.append(f"    {finding.message}")
            lines.append("")
    else:
        lines.append("  None in this run.")
        lines.append("")

    # ── Summary ───────────────────────────────────────────────────────────────
    lines.append("=" * 70)
    lines.append("SUMMARY")
    lines.append(f"  Facts:                    {len(facts)}")
    lines.append(f"  Review Recommendations:   {len(reviews)}")
    lines.append(f"  Files scanned:            {files_scanned}")

    # ── Optional LLM hand-off prompt ─────────────────────────────────────────
    if prompt_text is not None:
        lines.append("")
        lines.append("=" * 70)
        lines.append("LLM HAND-OFF PROMPT")
        lines.append("Copy everything below this line into your coding assistant.")
        lines.append("-" * 70)
        lines.append(prompt_text)

    return lines
