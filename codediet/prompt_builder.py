"""Prompt builder for CodeDiet — assembles the LLM hand-off prompt.

Per CLAUDE.md v0.3 §5.3, this is the highest-risk addition in v0.3.
Any change to this file requires re-reading §5.3 in full before merging.

Key safety invariants enforced here:
  - Facts and Review Recommendations are in visually distinct sections.
  - Facts may suggest direct action (inline, remove).
  - Review Recommendations must ONLY ask to "investigate and report back",
    NEVER to take action.
  - Forbidden action verbs for Review-class items: "delete", "remove", "fix",
    "consolidate", "duplicate", "dead", "unused", "unsafe".
  - Sanctioned wording is reused verbatim from the detector spec, not
    paraphrased.
  - The prompt closes with a "summarize your plan before making edits"
    instruction.
"""

from __future__ import annotations

from codediet.models import Finding, FindingClass

# ─────────────────────────────────────────────────────────────────────────────
# Sanctioned wording constants — do NOT paraphrase these in the template.
# Reusing exact strings makes string-match tests straightforward.
# ─────────────────────────────────────────────────────────────────────────────

_HEADER = """\
The following is output from CodeDiet, a read-only static analysis tool.
CodeDiet made no changes to this codebase. It performed purely structural,
deterministic static analysis — no LLMs, no embeddings, no probabilistic
inference of any kind was used to produce these findings.

Findings are split into two categories. Please treat them differently:\
"""

_FACTS_INTRO = """\
FACTS (structurally confirmed — true as written, by construction):\
"""

_REVIEWS_INTRO = """\
REVIEW RECOMMENDATIONS (heuristic signals — investigate before acting,
do not assume these are confirmed issues):\
"""

_FACTS_FOOTER = """\
For FACTS, you may propose a direct fix (for example, inlining a pure
pass-through wrapper) if it is appropriate for the context.\
"""

_REVIEWS_FOOTER = """\
For REVIEW RECOMMENDATIONS, please investigate first and report back what
you find — do not modify code based on these signals alone. Confirm whether
the flagged items are genuinely redundant or problematic before proposing
any change.\
"""

_CLOSING = """\
Please summarize your proposed plan before making any edits.\
"""

_NONE_IN_RUN = "(none in this run)"


def build_prompt(findings: list[Finding]) -> str:
    """Assemble the LLM hand-off prompt from a list of findings.

    The returned string is provider-agnostic plain text suitable for
    pasting into Claude Code, Cursor, Copilot Chat, ChatGPT, or any
    other coding assistant.

    Args:
        findings: All findings from the scan (may be empty).

    Returns:
        A single string containing the complete prompt.  The caller
        (``exporter.py``) is responsible for embedding it in the output
        file.
    """
    facts = [f for f in findings if f.classification == FindingClass.FACT]
    reviews = [f for f in findings if f.classification == FindingClass.REVIEW]

    sections: list[str] = [_HEADER, ""]

    # ── FACTS section ─────────────────────────────────────────────────────────
    sections.append(_FACTS_INTRO)
    if facts:
        for finding in facts:
            entry = _format_fact_entry(finding)
            sections.append(entry)
    else:
        sections.append(_NONE_IN_RUN)
    sections.append("")

    # ── REVIEW RECOMMENDATIONS section ────────────────────────────────────────
    sections.append(_REVIEWS_INTRO)
    if reviews:
        for finding in reviews:
            entry = _format_review_entry(finding)
            sections.append(entry)
    else:
        sections.append(_NONE_IN_RUN)
    sections.append("")

    # ── Footers ───────────────────────────────────────────────────────────────
    sections.append(_FACTS_FOOTER)
    sections.append("")
    sections.append(_REVIEWS_FOOTER)
    sections.append("")
    sections.append(_CLOSING)

    return "\n".join(sections)


# ─────────────────────────────────────────────────────────────────────────────
# Per-finding formatters
# ─────────────────────────────────────────────────────────────────────────────


def _format_fact_entry(finding: Finding) -> str:
    """Format a single FACT finding for the prompt.

    Fact entries may describe the structural observation and suggest
    direct action where appropriate.  Wording is kept conservative:
    "consider whether it can be inlined or removed" rather than
    "delete this."
    """
    fn = finding.evidence.get("function", "?")
    target = finding.evidence.get("target", "?")
    return (
        f"- {finding.file}:{finding.line} — `{fn}` is a pure pass-through"
        f" wrapper around `{target}`."
        f" Consider whether it can be inlined or removed."
    )


def _format_review_entry(finding: Finding) -> str:
    """Format a single REVIEW RECOMMENDATION finding for the prompt.

    CRITICAL: Review entries must NEVER contain action-implying verbs
    (delete, remove, fix, consolidate) and must NEVER use the words
    "duplicate", "dead", "unused", "unsafe".  They must ask the LLM to
    investigate and report back, not to act.

    Sanctioned wording from detector specs is used verbatim where possible.
    """
    # Use the sanctioned wording from the detector spec (CLAUDE.md §5.2–5.6).
    # Paraphrasing is not allowed here — these strings are what tests assert.
    detector = finding.detector
    if detector == "duplicate_helper":
        cluster = finding.evidence.get("cluster", [])
        names = ", ".join(f"`{n}`" for n in cluster) if cluster else finding.message
        return (
            f"- {finding.file}:{finding.line} — Review Cluster: {names}"
            f" share a naming pattern and overlapping signatures."
            f" Please review whether they are genuinely redundant before"
            f" proposing any change."
        )
    elif detector == "abandoned_implementation":
        return (
            f"- {finding.file}:{finding.line} — Potentially Superseded"
            f" Implementation: {finding.message}."
            f" Please investigate whether this is intentional versioning"
            f" or an accidentally retained earlier attempt."
        )
    elif detector == "dead_function":
        return (
            f"- {finding.file}:{finding.line} — Possibly Unused Function:"
            f" {finding.message}."
            f" Please check whether this function is reachable via dynamic"
            f" dispatch, dependency injection, or a framework before"
            f" concluding anything about it."
        )
    elif detector == "similar_module":
        return (
            f"- {finding.file}:{finding.line} — Review Similar Modules:"
            f" {finding.message}."
            f" Please review whether the structural overlap is intentional"
            f" before proposing any change."
        )
    elif detector == "utility_explosion":
        return (
            f"- {finding.file}:{finding.line} — Review Utility Growth:"
            f" {finding.message}."
            f" This is a low-confidence project-level heuristic signal only."
        )
    else:
        # Generic fallback for any future detector.
        return (
            f"- {finding.file}:{finding.line} — Review Recommendation:"
            f" {finding.message}."
            f" Please investigate before proposing any change."
        )
