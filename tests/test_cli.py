"""Tests for the CLI entrypoint (v0.3).

Adds coverage for --export and --prompt flags introduced in v0.3.
All v0.2 CLI tests are preserved unchanged below the v0.3 additions.
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from codediet.cli import app

runner = CliRunner()

# Resolve example paths relative to the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLES_DIR = str(_PROJECT_ROOT / "examples")
_OBVIOUS = str(_PROJECT_ROOT / "examples" / "obvious_wrappers.py")
_TRICKY = str(_PROJECT_ROOT / "examples" / "tricky_non_wrappers.py")


# ─────────────────────────────────────────────────────────────────────────────
# v0.2 tests — carried forward unchanged (with "doctor" subcommand added)
# ─────────────────────────────────────────────────────────────────────────────


def test_doctor_on_examples_text_output():
    """Run doctor on the examples directory and verify text output shape."""
    result = runner.invoke(app, ["doctor", _EXAMPLES_DIR])
    assert result.exit_code == 0, result.output
    assert "Files scanned:" in result.output
    assert "FACTS" in result.output
    assert "REVIEW RECOMMENDATIONS" in result.output


def test_doctor_on_examples_json_output():
    """Run doctor with --json and verify valid JSON structure."""
    result = runner.invoke(app, ["doctor", _EXAMPLES_DIR, "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "facts" in data
    assert "review_recommendations" in data
    assert isinstance(data["facts"], list)
    assert isinstance(data["review_recommendations"], list)
    # The obvious_wrappers.py example should produce findings in facts
    assert len(data["facts"]) > 0


def test_doctor_on_single_file():
    """Run doctor on a single Python file."""
    result = runner.invoke(app, ["doctor", _OBVIOUS])
    assert result.exit_code == 0, result.output
    assert "parse_float -> float" in result.output


def test_doctor_no_findings_on_non_wrappers():
    """The tricky_non_wrappers file should produce zero findings."""
    result = runner.invoke(app, ["doctor", _TRICKY, "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data["facts"]) == 0
    assert len(data["review_recommendations"]) == 0


def test_doctor_nonexistent_path():
    """Nonexistent path should produce an error exit."""
    result = runner.invoke(app, ["doctor", "nonexistent_path_xyz/"])
    assert result.exit_code != 0


# ─────────────────────────────────────────────────────────────────────────────
# v0.3 tests — --export and --prompt
# ─────────────────────────────────────────────────────────────────────────────


def test_export_creates_markdown_file(tmp_path: Path):
    """--export with .md extension should create a valid Markdown file."""
    out = tmp_path / "findings.md"
    result = runner.invoke(app, ["doctor", _OBVIOUS, "--export", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists(), "Export file was not created"
    content = out.read_text()
    assert "# CodeDiet Findings" in content
    assert "## Facts" in content
    assert "## Review Recommendations" in content


def test_export_creates_txt_file(tmp_path: Path):
    """--export with .txt extension should create a plain-text file."""
    out = tmp_path / "findings.txt"
    result = runner.invoke(app, ["doctor", _OBVIOUS, "--export", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    content = out.read_text()
    assert "CodeDiet Findings" in content
    assert "FACTS" in content


def test_export_written_even_with_no_findings(tmp_path: Path):
    """--export must write the file even when there are zero findings."""
    out = tmp_path / "findings.md"
    result = runner.invoke(app, ["doctor", _TRICKY, "--export", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists(), "Export file not written for zero-findings run"
    content = out.read_text()
    # Both sections still present
    assert "## Facts" in content
    assert "## Review Recommendations" in content


def test_export_with_prompt_appends_prompt_section(tmp_path: Path):
    """--export --prompt should add LLM hand-off section to the output file."""
    out = tmp_path / "findings.md"
    result = runner.invoke(app, ["doctor", _OBVIOUS, "--export", str(out), "--prompt"])
    assert result.exit_code == 0, result.output
    content = out.read_text()
    assert "LLM Hand-off Prompt" in content


def test_prompt_without_export_emits_warning():
    """--prompt alone (no --export) should emit a warning but still exit 0."""
    result = runner.invoke(app, ["doctor", _OBVIOUS, "--prompt"])
    assert result.exit_code == 0
    # Warning goes to stderr; Typer's CliRunner merges them unless mix_stderr=False.
    # We check the combined output for the warning text.
    assert "no effect" in result.output or "Warning" in result.output


def test_export_path_confirmed_in_output(tmp_path: Path):
    """CLI should echo the path of the written file."""
    out = tmp_path / "findings.md"
    result = runner.invoke(app, ["doctor", _OBVIOUS, "--export", str(out)])
    assert result.exit_code == 0, result.output
    assert str(out) in result.output
