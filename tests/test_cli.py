"""Tests for the CLI entrypoint (v0.2)."""

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


def test_doctor_on_examples_text_output():
    """Run doctor on the examples directory and verify text output shape."""
    result = runner.invoke(app, [_EXAMPLES_DIR])
    assert result.exit_code == 0, result.output
    assert "Files scanned:" in result.output
    assert "FACTS" in result.output
    assert "REVIEW RECOMMENDATIONS" in result.output


def test_doctor_on_examples_json_output():
    """Run doctor with --json and verify valid JSON structure."""
    result = runner.invoke(app, [_EXAMPLES_DIR, "--json"])
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
    result = runner.invoke(app, [_OBVIOUS])
    assert result.exit_code == 0, result.output
    assert "parse_float -> float" in result.output


def test_doctor_no_findings_on_non_wrappers():
    """The tricky_non_wrappers file should produce zero findings."""
    result = runner.invoke(app, [_TRICKY, "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data["facts"]) == 0
    assert len(data["review_recommendations"]) == 0


def test_doctor_nonexistent_path():
    """Nonexistent path should produce an error exit."""
    result = runner.invoke(app, ["nonexistent_path_xyz/"])
    assert result.exit_code != 0
