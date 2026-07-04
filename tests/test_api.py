"""Tests for the programmatic API (v0.2)."""

from pathlib import Path
import pytest

import codediet
from codediet import Finding, scan
from codediet.models import FindingClass

# Resolve example paths relative to the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLES_DIR = _PROJECT_ROOT / "examples"
_OBVIOUS = _EXAMPLES_DIR / "obvious_wrappers.py"
_TRICKY = _EXAMPLES_DIR / "tricky_non_wrappers.py"


def test_api_exports():
    """Verify that scan and Finding are exported at package root."""
    assert hasattr(codediet, "scan")
    assert hasattr(codediet, "Finding")
    assert codediet.scan is scan
    assert codediet.Finding is Finding


def test_scan_on_directory():
    """Verify scan on a directory returns list of Finding from any detector."""
    findings = scan(_EXAMPLES_DIR)
    assert isinstance(findings, list)
    assert len(findings) > 0
    for finding in findings:
        assert isinstance(finding, Finding)
        assert isinstance(finding.detector, str)
        assert isinstance(finding.evidence, dict)

    # Specifically verify wrapper findings are still present and correct.
    wrapper_findings = [f for f in findings if f.detector == "wrapper"]
    assert len(wrapper_findings) > 0
    for f in wrapper_findings:
        assert f.classification == FindingClass.FACT
        assert "function" in f.evidence
        assert "target" in f.evidence


def test_scan_on_single_file_obvious():
    """Verify scan on a file with obvious wrappers returns findings."""
    findings = scan(_OBVIOUS)
    assert len(findings) > 0
    # Check that parse_float is detected as a wrapper around float
    parse_float_finding = next(
        (f for f in findings if f.evidence.get("function") == "parse_float"), None
    )
    assert parse_float_finding is not None
    assert parse_float_finding.evidence["target"] == "float"
    assert parse_float_finding.classification == FindingClass.FACT


def test_scan_on_single_file_non_wrappers():
    """Verify scan on tricky non-wrappers returns no findings."""
    findings = scan(_TRICKY)
    assert len(findings) == 0


def test_scan_nonexistent_path():
    """Verify scan raises FileNotFoundError for nonexistent paths."""
    with pytest.raises(FileNotFoundError):
        scan("nonexistent_path_xyz/")
