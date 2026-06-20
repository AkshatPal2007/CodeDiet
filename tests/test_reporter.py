"""Tests for the reporter module (v0.2)."""

import json
from io import StringIO
from unittest.mock import patch

from codediet.models import Finding, FindingClass
from codediet.reporter import report_json, report_text


def _make_facts():
    return [
        Finding(
            detector="wrapper",
            classification=FindingClass.FACT,
            file="utils.py",
            line=18,
            message="parse_float -> float",
            evidence={"function": "parse_float", "target": "float"},
        ),
        Finding(
            detector="wrapper",
            classification=FindingClass.FACT,
            file="helpers.py",
            line=44,
            message="process_number -> helper",
            evidence={"function": "process_number", "target": "helper"},
        ),
    ]


def _make_reviews():
    return [
        Finding(
            detector="duplicate_helper",
            classification=FindingClass.REVIEW,
            file="utils.py",
            line=5,
            message="safe_float, parse_float, ensure_float",
            evidence={"cluster": ["safe_float", "parse_float", "ensure_float"]},
        ),
    ]


class TestTextReport:
    def test_output_format_facts(self):
        """Facts section should appear with count and individual entries."""
        findings = _make_facts()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_text(findings, files_scanned=42)
            output = mock_stdout.getvalue()

        assert "Files scanned: 42" in output
        assert "FACTS" in output
        assert "2 found" in output
        assert "utils.py:18" in output
        assert "parse_float -> float" in output
        assert "helpers.py:44" in output
        assert "process_number -> helper" in output

    def test_output_format_reviews(self):
        """Review Recommendations section should appear with count."""
        findings = _make_reviews()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_text(findings, files_scanned=10)
            output = mock_stdout.getvalue()

        assert "REVIEW RECOMMENDATIONS" in output
        assert "1 found" in output
        assert "utils.py:5" in output

    def test_zero_findings(self):
        """Both sections should print with 0 found and (none) placeholders."""
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_text([], files_scanned=10)
            output = mock_stdout.getvalue()

        assert "Files scanned: 10" in output
        assert "FACTS" in output
        assert "0 found" in output
        assert "REVIEW RECOMMENDATIONS" in output
        assert "(none)" in output

    def test_no_scores_or_suggestions(self):
        """CLAUDE.md: No scores, percentages, rankings, risk values, or suggestions — ever."""
        findings = _make_facts()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_text(findings, files_scanned=42)
            output = mock_stdout.getvalue().lower()

        banned = ["score", "risk", "consider", "suggest", "delete",
                  "remove", "unnecessary", "percent", "%"]
        for word in banned:
            assert word not in output, f"Found banned word '{word}' in output"


class TestJsonReport:
    def test_output_structure_facts(self):
        """Facts should appear under 'facts' key with correct fields."""
        findings = _make_facts()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_json(findings)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert "facts" in data
        assert "review_recommendations" in data
        assert len(data["facts"]) == 2
        assert len(data["review_recommendations"]) == 0

        f = data["facts"][0]
        assert f["detector"] == "wrapper"
        assert f["file"] == "utils.py"
        assert f["line"] == 18
        assert f["message"] == "parse_float -> float"
        assert f["evidence"] == {"function": "parse_float", "target": "float"}

    def test_output_structure_reviews(self):
        """Review recommendations should appear under their own key."""
        findings = _make_reviews()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_json(findings)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert len(data["facts"]) == 0
        assert len(data["review_recommendations"]) == 1
        r = data["review_recommendations"][0]
        assert r["detector"] == "duplicate_helper"

    def test_zero_findings(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_json([])
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data == {"facts": [], "review_recommendations": []}

    def test_fields_present(self):
        """JSON entries should contain the standard v0.2 fields."""
        findings = _make_facts()
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            report_json(findings)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        allowed_keys = {"detector", "file", "line", "message", "evidence"}
        for entry in data["facts"]:
            assert set(entry.keys()) == allowed_keys
