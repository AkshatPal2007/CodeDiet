"""Tests for the reporter module."""

import json
from io import StringIO
from unittest.mock import patch

from codediet.models import Finding
from codediet.reporter import report_json, report_text


def _make_findings():
    return [
        Finding(
            kind="wrapper",
            file="utils.py",
            line=18,
            function="parse_float",
            target="float",
        ),
        Finding(
            kind="wrapper",
            file="helpers.py",
            line=44,
            function="process_number",
            target="helper",
        ),
    ]


class TestTextReport:
    def test_output_format(self):
        findings = _make_findings()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_text(findings, files_scanned=42)
            output = mock_stdout.getvalue()

        assert "Files scanned: 42" in output
        assert "Wrapper Functions Found: 2" in output
        assert "WRAPPER" in output
        assert "utils.py:18" in output
        assert "parse_float -> float" in output
        assert "helpers.py:44" in output
        assert "process_number -> helper" in output

    def test_zero_findings(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_text([], files_scanned=10)
            output = mock_stdout.getvalue()

        assert "Files scanned: 10" in output
        assert "Wrapper Functions Found: 0" in output
        assert "WRAPPER" not in output

    def test_no_scores_or_suggestions(self):
        """CLAUDE.md: No scores, percentages, rankings, risk values,
        generated commentary, or suggestions in the output — ever."""
        findings = _make_findings()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_text(findings, files_scanned=42)
            output = mock_stdout.getvalue().lower()

        banned = ["score", "risk", "consider", "suggest", "recommend",
                  "delete", "remove", "unnecessary", "percent", "%"]
        for word in banned:
            assert word not in output, f"Found banned word '{word}' in output"


class TestJsonReport:
    def test_output_structure(self):
        findings = _make_findings()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_json(findings)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert "wrappers" in data
        assert len(data["wrappers"]) == 2
        assert data["wrappers"][0]["file"] == "utils.py"
        assert data["wrappers"][0]["line"] == 18
        assert data["wrappers"][0]["function"] == "parse_float"
        assert data["wrappers"][0]["target"] == "float"

    def test_zero_findings(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_json([])
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data == {"wrappers": []}

    def test_no_extra_fields(self):
        """JSON output should contain only the fields from the spec."""
        findings = _make_findings()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_json(findings)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        allowed_keys = {"file", "line", "function", "target"}
        for wrapper in data["wrappers"]:
            assert set(wrapper.keys()) == allowed_keys
