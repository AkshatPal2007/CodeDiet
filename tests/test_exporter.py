"""Tests for the exporter module (v0.3).

Per CLAUDE.md v0.3 §5.2:
  - Facts and Review Recommendations are always in separate sections.
  - The file is always written, even when there are no findings.
  - A clean-run is a useful fact, not a reason to skip the file.
  - No score, no percentage, no health ranking in the output.
"""

from pathlib import Path


from codediet.exporter import export_findings
from codediet.models import Finding, FindingClass


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _fact(file="utils.py", line=18, fn="parse_float", target="float") -> Finding:
    return Finding(
        detector="wrapper",
        classification=FindingClass.FACT,
        file=file,
        line=line,
        message=f"{fn} -> {target}",
        evidence={"function": fn, "target": target},
    )


def _review(file="helpers.py", line=5) -> Finding:
    return Finding(
        detector="duplicate_helper",
        classification=FindingClass.REVIEW,
        file=file,
        line=line,
        message="safe_float, parse_float, ensure_float",
        evidence={"cluster": ["safe_float", "parse_float", "ensure_float"]},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Markdown export tests
# ─────────────────────────────────────────────────────────────────────────────


class TestMarkdownExport:
    def test_header_present(self, tmp_path: Path):
        out = tmp_path / "findings.md"
        export_findings([], out, "/myrepo", files_scanned=10)
        content = out.read_text()
        assert "# CodeDiet Findings" in content
        assert "/myrepo" in content

    def test_timestamp_present(self, tmp_path: Path):
        out = tmp_path / "findings.md"
        export_findings([], out, "/myrepo", files_scanned=10)
        content = out.read_text()
        assert "Generated:" in content

    def test_facts_section_present(self, tmp_path: Path):
        out = tmp_path / "findings.md"
        export_findings([_fact()], out, "/myrepo", files_scanned=5)
        content = out.read_text()
        assert "## Facts" in content
        assert "utils.py:18" in content
        assert "parse_float" in content

    def test_reviews_section_present(self, tmp_path: Path):
        out = tmp_path / "findings.md"
        export_findings([_review()], out, "/myrepo", files_scanned=5)
        content = out.read_text()
        assert "## Review Recommendations" in content
        assert "helpers.py:5" in content

    def test_both_sections_always_present(self, tmp_path: Path):
        """Both sections must appear even when one has no findings."""
        out = tmp_path / "findings.md"
        export_findings([_fact()], out, "/myrepo", files_scanned=5)
        content = out.read_text()
        assert "## Facts" in content
        assert "## Review Recommendations" in content
        # Review section should say "None" rather than being omitted
        assert "None in this run" in content

    def test_empty_findings_file_still_written(self, tmp_path: Path):
        """A clean run must still produce a file — it's useful information."""
        out = tmp_path / "findings.md"
        export_findings([], out, "/myrepo", files_scanned=42)
        assert out.exists()
        content = out.read_text()
        assert "## Facts" in content
        assert "## Review Recommendations" in content
        assert "None in this run" in content

    def test_summary_counts(self, tmp_path: Path):
        out = tmp_path / "findings.md"
        export_findings([_fact(), _fact(fn="parse_int", target="int"), _review()],
                        out, "/myrepo", files_scanned=7)
        content = out.read_text()
        assert "2 Facts" in content
        assert "1 Review Recommendations" in content
        assert "7 files scanned" in content

    def test_no_scores_or_health_ranking(self, tmp_path: Path):
        """CLAUDE.md: no score, no health percentage, no risk ranking — ever."""
        out = tmp_path / "findings.md"
        export_findings([_fact()], out, "/myrepo", files_scanned=10)
        content = out.read_text().lower()
        for word in ["score", "health", "risk", "%", "percent", "grade", "rank"]:
            assert word not in content, f"Banned word '{word}' found in export"

    def test_prompt_section_absent_without_flag(self, tmp_path: Path):
        out = tmp_path / "findings.md"
        export_findings([_fact()], out, "/myrepo", files_scanned=5, prompt_text=None)
        content = out.read_text()
        assert "LLM Hand-off Prompt" not in content

    def test_prompt_section_present_with_text(self, tmp_path: Path):
        out = tmp_path / "findings.md"
        export_findings(
            [_fact()], out, "/myrepo", files_scanned=5,
            prompt_text="This is the prompt."
        )
        content = out.read_text()
        assert "LLM Hand-off Prompt" in content
        assert "This is the prompt." in content


# ─────────────────────────────────────────────────────────────────────────────
# Plain-text export tests
# ─────────────────────────────────────────────────────────────────────────────


class TestPlainTextExport:
    def test_header_present(self, tmp_path: Path):
        out = tmp_path / "findings.txt"
        export_findings([], out, "/myrepo", files_scanned=10)
        content = out.read_text()
        assert "CodeDiet Findings" in content
        assert "/myrepo" in content

    def test_facts_section_present(self, tmp_path: Path):
        out = tmp_path / "findings.txt"
        export_findings([_fact()], out, "/myrepo", files_scanned=5)
        content = out.read_text()
        assert "FACTS" in content
        assert "utils.py:18" in content

    def test_reviews_section_present(self, tmp_path: Path):
        out = tmp_path / "findings.txt"
        export_findings([_review()], out, "/myrepo", files_scanned=5)
        content = out.read_text()
        assert "REVIEW RECOMMENDATIONS" in content

    def test_empty_findings_file_still_written(self, tmp_path: Path):
        out = tmp_path / "findings.txt"
        export_findings([], out, "/myrepo", files_scanned=10)
        assert out.exists()
        content = out.read_text()
        assert "None in this run" in content

    def test_summary_counts(self, tmp_path: Path):
        out = tmp_path / "findings.txt"
        export_findings([_fact(), _review()], out, "/myrepo", files_scanned=3)
        content = out.read_text()
        assert "1" in content  # fact count
        assert "Files scanned" in content

    def test_prompt_section_appended(self, tmp_path: Path):
        out = tmp_path / "findings.txt"
        export_findings(
            [], out, "/myrepo", files_scanned=5,
            prompt_text="PASTE THIS INTO YOUR TOOL"
        )
        content = out.read_text()
        assert "LLM HAND-OFF PROMPT" in content
        assert "PASTE THIS INTO YOUR TOOL" in content
