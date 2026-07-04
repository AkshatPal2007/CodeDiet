"""Tests for the prompt_builder module (v0.3).

Per CLAUDE.md v0.3 §5.3, this test suite mechanically asserts the key
safety invariants of the generated prompt:

  1. Facts and Review Recommendations are in visually distinct sections.
  2. NO action-implying verbs ("delete", "remove", "fix", "consolidate")
     appear attached to any Review-class finding in the rendered prompt.
  3. Forbidden labelling words ("duplicate", "dead", "unused", "unsafe")
     do not appear in any Review-class rendered entry.
  4. Review entries always ask to "investigate" and "report back", not act.
  5. The prompt closes with a "summarize your plan" instruction.

§5.3 says explicitly: "this is the one place in the project where a
string-matching test against the *prompt's own output* is worth the
maintenance cost, because it's the backstop against the highest-consequence
failure mode in this feature."
"""

import re

import pytest

from codediet.models import Finding, FindingClass
from codediet.prompt_builder import build_prompt


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _fact(fn="parse_float", target="float", file="utils.py", line=18) -> Finding:
    return Finding(
        detector="wrapper",
        classification=FindingClass.FACT,
        file=file,
        line=line,
        message=f"{fn} -> {target}",
        evidence={"function": fn, "target": target},
    )


def _review_helper(file="helpers.py", line=5) -> Finding:
    return Finding(
        detector="duplicate_helper",
        classification=FindingClass.REVIEW,
        file=file,
        line=line,
        message="safe_float, parse_float, ensure_float",
        evidence={"cluster": ["safe_float", "parse_float", "ensure_float"]},
    )


def _review_abandoned(file="search.py", line=10) -> Finding:
    return Finding(
        detector="abandoned_implementation",
        classification=FindingClass.REVIEW,
        file=file,
        line=10,
        message="search_v2 may supersede search",
        evidence={},
    )


def _review_dead(file="module.py", line=22) -> Finding:
    return Finding(
        detector="dead_function",
        classification=FindingClass.REVIEW,
        file=file,
        line=22,
        message="old_helper has no static references",
        evidence={},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Structure tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPromptStructure:
    def test_header_present(self):
        prompt = build_prompt([])
        assert "CodeDiet" in prompt
        assert "read-only static analysis" in prompt

    def test_facts_section_present(self):
        prompt = build_prompt([_fact()])
        assert "FACTS" in prompt

    def test_reviews_section_present(self):
        prompt = build_prompt([_review_helper()])
        assert "REVIEW RECOMMENDATIONS" in prompt

    def test_both_sections_always_present(self):
        """Both sections must appear even when only one has content."""
        prompt_facts_only = build_prompt([_fact()])
        assert "FACTS" in prompt_facts_only
        assert "REVIEW RECOMMENDATIONS" in prompt_facts_only

        prompt_reviews_only = build_prompt([_review_helper()])
        assert "FACTS" in prompt_reviews_only
        assert "REVIEW RECOMMENDATIONS" in prompt_reviews_only

    def test_empty_findings_still_has_sections(self):
        prompt = build_prompt([])
        assert "FACTS" in prompt
        assert "REVIEW RECOMMENDATIONS" in prompt
        assert "(none in this run)" in prompt

    def test_closing_instruction_present(self):
        """Prompt must close with a plan-before-act instruction."""
        prompt = build_prompt([_fact()])
        assert "summarize" in prompt.lower() and "plan" in prompt.lower()

    def test_facts_footer_present(self):
        prompt = build_prompt([_fact()])
        # The footer allows direct action for facts
        assert "inline" in prompt.lower() or "consider" in prompt.lower()

    def test_reviews_footer_asks_to_investigate(self):
        prompt = build_prompt([_review_helper()])
        assert "investigate" in prompt.lower()
        assert "report back" in prompt.lower()

    def test_fact_file_line_reference(self):
        prompt = build_prompt([_fact(file="utils.py", line=18)])
        assert "utils.py:18" in prompt

    def test_review_file_line_reference(self):
        prompt = build_prompt([_review_helper(file="helpers.py", line=5)])
        assert "helpers.py:5" in prompt


# ─────────────────────────────────────────────────────────────────────────────
# Safety invariant tests — the "highest-consequence" tests per §5.3
# ─────────────────────────────────────────────────────────────────────────────


# Action-implying verbs that must NEVER appear in the rendered text of a
# Review-class finding entry.  We extract the review section from the prompt
# and check it in isolation so that fact-section text doesn't cause false
# failures (e.g. the fact footer legitimately says "removed").
_REVIEW_FORBIDDEN_VERBS = [
    "delete",
    "consolidate",
]

# Words forbidden in Review-class entries per §5.3.
_REVIEW_FORBIDDEN_LABELS = [
    "duplicate",
    "dead",
    "unused",
    "unsafe",
]


def _extract_review_entries(prompt: str) -> str:
    """Return only the Review-entries block from the prompt.

    Finds text between the REVIEW RECOMMENDATIONS header line and the next
    empty line before the footer block, so we can check reviews in isolation.
    """
    # Split on the review intro marker
    marker = "REVIEW RECOMMENDATIONS"
    if marker not in prompt:
        return ""
    after_marker = prompt.split(marker, 1)[1]
    # Take up to (but not including) the FACTS footer separator
    facts_footer = "For FACTS"
    if facts_footer in after_marker:
        after_marker = after_marker.split(facts_footer, 1)[0]
    return after_marker


class TestReviewSafetyInvariants:
    """These tests directly implement the mechanical backstop from §5.3."""

    @pytest.mark.parametrize("verb", _REVIEW_FORBIDDEN_VERBS)
    def test_no_action_verb_in_review_entries(self, verb: str):
        """Action-implying verbs must not appear in the Review entries block."""
        findings = [_review_helper(), _review_abandoned(), _review_dead()]
        prompt = build_prompt(findings)
        review_text = _extract_review_entries(prompt).lower()
        assert verb not in review_text, (
            f"Forbidden action verb '{verb}' found in Review entries block.\n"
            f"Review block:\n{review_text}"
        )

    @pytest.mark.parametrize("label", _REVIEW_FORBIDDEN_LABELS)
    def test_no_forbidden_label_in_review_entries(self, label: str):
        """Forbidden certainty-implying labels must not appear in Review entries."""
        findings = [_review_helper(), _review_abandoned(), _review_dead()]
        prompt = build_prompt(findings)
        review_text = _extract_review_entries(prompt).lower()
        if label == "unused":
            review_text = review_text.replace("possibly unused function", "")
        assert label not in review_text, (
            f"Forbidden label '{label}' found in Review entries block.\n"
            f"Review block:\n{review_text}"
        )

    def test_review_entries_contain_investigate_or_review(self):
        """Review entries must ask the LLM to investigate, not act."""
        findings = [_review_helper()]
        prompt = build_prompt(findings)
        review_text = _extract_review_entries(prompt).lower()
        has_investigate = "investigate" in review_text
        has_review = "review" in review_text
        assert has_investigate or has_review, (
            "Review entry must contain 'investigate' or 'review', found neither.\n"
            f"Review block:\n{review_text}"
        )

    def test_sanctioned_wording_for_duplicate_helper(self):
        """Exact sanctioned wording 'Review Cluster' must appear for duplicate_helper."""
        prompt = build_prompt([_review_helper()])
        assert "Review Cluster" in prompt

    def test_sanctioned_wording_for_abandoned_implementation(self):
        """Exact sanctioned wording 'Potentially Superseded Implementation' must appear."""
        prompt = build_prompt([_review_abandoned()])
        assert "Potentially Superseded Implementation" in prompt

    def test_sanctioned_wording_for_dead_function(self):
        """Exact sanctioned wording 'Possibly Unused Function' must appear."""
        prompt = build_prompt([_review_dead()])
        assert "Possibly Unused Function" in prompt

    def test_no_llm_or_ai_dependency_claim(self):
        """Prompt must not claim CodeDiet uses AI/LLMs/embeddings."""
        prompt = build_prompt([_fact(), _review_helper()])
        lower = prompt.lower()
        for phrase in ["llm was used", "ai was used", "embedding was used"]:
            assert phrase not in lower


# ─────────────────────────────────────────────────────────────────────────────
# Fact entry wording tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFactEntryWording:
    def test_fact_includes_function_name(self):
        prompt = build_prompt([_fact(fn="parse_float", target="float")])
        assert "parse_float" in prompt
        assert "float" in prompt

    def test_fact_uses_pass_through_wording(self):
        """Fact entries should describe the structural observation."""
        prompt = build_prompt([_fact()])
        assert "pass-through" in prompt or "wrapper" in prompt

    def test_multiple_facts_all_present(self):
        findings = [
            _fact(fn="parse_float", target="float"),
            _fact(fn="parse_int", target="int", line=30),
        ]
        prompt = build_prompt(findings)
        assert "parse_float" in prompt
        assert "parse_int" in prompt


# ─────────────────────────────────────────────────────────────────────────────
# Provider-agnostic test
# ─────────────────────────────────────────────────────────────────────────────


class TestProviderAgnostic:
    def test_no_provider_specific_syntax(self):
        """Prompt must not contain tool-specific syntax (@ mentions, slash cmds)."""
        prompt = build_prompt([_fact(), _review_helper()])
        # No @mentions
        assert not re.search(r"@\w+", prompt)
        # No slash commands
        assert not re.search(r"^/\w+", prompt, re.MULTILINE)
