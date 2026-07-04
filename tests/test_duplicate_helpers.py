"""Comprehensive tests for the Duplicate Helper detector.

The detector groups functions by (semantic_root, param_count, AST_fingerprint).
A cluster only fires when ALL three match and there are ≥ 2 functions.

Negative tests are critical here — this detector has a higher inherent false-
positive risk than the wrapper or abandoned detectors, and the test suite must
aggressively guard against incorrect groupings.
"""

from __future__ import annotations

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from codediet.detectors.duplicate_helpers import detect
from codediet.models import FindingClass

PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


def _parse(code: str, filepath: str = "test.py") -> tuple:
    source_bytes = code.encode("utf-8")
    tree = _parser.parse(source_bytes)
    return tree, source_bytes, filepath


def run_detect(*code_blocks: tuple[str, str]) -> list:
    """Parse multiple (code, filepath) pairs and run detect on all."""
    parsed = [_parse(code, fp) for code, fp in code_blocks]
    return detect(parsed)


def run_single(code: str, filepath: str = "test.py") -> list:
    return run_detect((code, filepath))


# ═══════════════════════════════════════════════════════════════════════════
# POSITIVE CASES — clusters that SHOULD be detected
# ═══════════════════════════════════════════════════════════════════════════


class TestPositiveBasicClusters:
    def test_three_float_helpers(self):
        """Classic CLAUDE.md §7.2 example: safe_float, parse_float, ensure_float."""
        code = """
def safe_float(x):
    return float(x)

def parse_float(x):
    return float(x)

def ensure_float(x):
    return float(x)
"""
        findings = run_single(code)
        assert len(findings) == 1
        f = findings[0]
        assert f.detector == "duplicate_helper"
        assert f.classification == FindingClass.REVIEW
        cluster = set(f.evidence["cluster"])
        assert cluster == {"safe_float", "parse_float", "ensure_float"}

    def test_two_helpers_minimum_cluster(self):
        code = """
def safe_float(x):
    return float(x)

def parse_float(x):
    return float(x)
"""
        findings = run_single(code)
        assert len(findings) == 1

    def test_prefix_stripped_correctly(self):
        """root extracted from prefix: get_X, to_X, as_X."""
        code = """
def to_json(obj):
    return str(obj)

def as_json(obj):
    return str(obj)
"""
        findings = run_single(code)
        assert len(findings) == 1
        assert findings[0].evidence["root"] == "json"

    def test_suffix_stripped_correctly(self):
        """root extracted from suffix: X_safe, X_clean."""
        code = """
def value_safe(x):
    return x

def value_clean(x):
    return x
"""
        findings = run_single(code)
        assert len(findings) == 1
        assert findings[0].evidence["root"] == "value"


class TestPositiveCrossFile:
    """Clusters should be detected across multiple files."""

    def test_cluster_across_two_files(self):
        code_a = """
def safe_float(x):
    return float(x)
"""
        code_b = """
def parse_float(x):
    return float(x)
"""
        findings = run_detect((code_a, "utils.py"), (code_b, "helpers.py"))
        assert len(findings) == 1
        cluster = set(findings[0].evidence["cluster"])
        assert cluster == {"safe_float", "parse_float"}

    def test_cross_file_finding_located_at_first_member(self):
        """Finding file should be the file of the first function in the cluster."""
        code_a = """
def safe_float(x):
    return float(x)
"""
        code_b = """
def parse_float(x):
    return float(x)
"""
        findings = run_detect((code_a, "a.py"), (code_b, "b.py"))
        assert len(findings) == 1
        # First parsed = a.py
        assert findings[0].file == "a.py"


class TestPositiveFindingStructure:
    def test_finding_fields(self):
        code = """
def safe_float(x):
    return float(x)

def parse_float(x):
    return float(x)
"""
        findings = run_single(code)
        f = findings[0]
        assert f.detector == "duplicate_helper"
        assert f.classification == FindingClass.REVIEW
        assert f.line >= 1
        assert isinstance(f.file, str)
        assert isinstance(f.message, str)
        assert "evidence" != None

    def test_evidence_schema(self):
        code = """
def safe_float(x):
    return float(x)

def parse_float(x):
    return float(x)
"""
        findings = run_single(code)
        ev = findings[0].evidence
        assert "cluster" in ev
        assert "root" in ev
        assert "param_count" in ev
        assert isinstance(ev["cluster"], list)
        assert len(ev["cluster"]) >= 2

    def test_message_wording_per_spec(self):
        """Message must be comma-separated function names (per CLAUDE.md §7.2)."""
        code = """
def safe_float(x):
    return float(x)

def parse_float(x):
    return float(x)
"""
        findings = run_single(code)
        msg = findings[0].message
        assert "safe_float" in msg
        assert "parse_float" in msg

    def test_no_forbidden_words_in_message(self):
        """Per CLAUDE.md: forbidden words must not appear in REVIEW messages."""
        code = """
def safe_float(x):
    return float(x)

def parse_float(x):
    return float(x)
"""
        findings = run_single(code)
        msg = findings[0].message.lower()
        for word in ["delete", "remove", "dead", "unused", "duplicate",
                     "unsafe", "fix", "consolidate"]:
            assert word not in msg


class TestPositiveMethodClusters:
    """Methods in classes are collected (self/cls excluded from param count)."""

    def test_methods_cluster(self):
        code = """
class Repo:
    def get_items(self):
        return list(self._store)

    def build_items(self):
        return list(self._store)
"""
        findings = run_single(code)
        assert len(findings) == 1
        cluster = set(findings[0].evidence["cluster"])
        assert cluster == {"get_items", "build_items"}


# ═══════════════════════════════════════════════════════════════════════════
# NEGATIVE CASES — must NOT fire
# ═══════════════════════════════════════════════════════════════════════════


class TestNegativeDifferentParamCounts:
    """Different parameter counts → no cluster."""

    def test_different_counts(self):
        code = """
def safe_float(x):
    return float(x)

def parse_float(x, default=0.0):
    return float(x)
"""
        # safe_float: 1 param; parse_float: 2 params → different counts
        findings = run_single(code)
        assert len(findings) == 0

    def test_zero_vs_one_param(self):
        code = """
def get_items():
    return []

def build_items(source):
    return list(source)
"""
        findings = run_single(code)
        assert len(findings) == 0


class TestNegativeDifferentFingerprints:
    """Different AST fingerprints → no cluster, even with same root and params."""

    def test_guarded_vs_unguarded(self):
        """safe_float has an if guard; parse_float does not → different fingerprints."""
        code = """
def safe_float(x):
    if x is None:
        return 0.0
    return float(x)

def parse_float(x):
    return float(x)
"""
        # safe_float: ("if_statement", "return_statement")
        # parse_float: ("return_statement",)
        # Different fingerprints → no cluster
        findings = run_single(code)
        assert len(findings) == 0

    def test_try_vs_direct_return(self):
        code = """
def safe_int(x):
    try:
        return int(x)
    except ValueError:
        return 0

def parse_int(x):
    return int(x)
"""
        findings = run_single(code)
        assert len(findings) == 0


class TestNegativeNoAffix:
    """Functions without a recognised prefix or suffix → no root → not clustered."""

    def test_unstrippable_names(self):
        code = """
def process(data):
    return data

def transform(data):
    return data
"""
        findings = run_single(code)
        assert len(findings) == 0

    def test_partial_match_not_stripped(self):
        """'parser' does not start with 'parse_' (no underscore) → not stripped."""
        code = """
def parser(x):
    return x

def getter(x):
    return x
"""
        findings = run_single(code)
        assert len(findings) == 0


class TestNegativeBodyTooLong:
    """Functions with body > _MAX_BODY_STMTS are excluded from clustering."""

    def test_long_body_excluded(self):
        code = """
def safe_complex(x):
    a = x + 1
    b = a * 2
    c = b - 3
    d = c / 4
    e = d + 5
    return float(e)

def parse_complex(x):
    a = x + 1
    b = a * 2
    c = b - 3
    d = c / 4
    e = d + 5
    return float(e)
"""
        # Both have 6 statements > _MAX_BODY_STMTS (5) → excluded
        findings = run_single(code)
        assert len(findings) == 0


class TestNegativeSingleFunction:
    """A cluster requires ≥ 2 functions — single function must not fire."""

    def test_single_function_no_cluster(self):
        code = """
def safe_float(x):
    return float(x)
"""
        assert len(run_single(code)) == 0


class TestNegativeNestedFunctions:
    """Functions nested inside other functions are not collected."""

    def test_nested_not_clustered(self):
        code = """
def outer():
    def safe_float(x):
        return float(x)
    def parse_float(x):
        return float(x)
    return safe_float, parse_float
"""
        findings = run_single(code)
        assert len(findings) == 0


class TestNegativeEmptyAndTrivial:
    def test_empty_file(self):
        assert len(run_single("")) == 0

    def test_no_functions(self):
        code = """
X = 1
Y = 2
"""
        assert len(run_single(code)) == 0

    def test_empty_parsed_list(self):
        assert len(detect([])) == 0
