"""Comprehensive tests for the Abandoned Implementation detector.

Per CLAUDE.md §10: negative test cases (near-misses that must NOT fire)
are as important as positive cases. Every test class that verifies detection
has a corresponding class that verifies non-detection of similar-looking code.
"""

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from codediet.detectors.abandoned import detect
from codediet.models import FindingClass

PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


def run_detect(code: str, filepath: str = "test.py") -> list:
    source_bytes = code.encode("utf-8")
    tree = _parser.parse(source_bytes)
    return detect(tree, source_bytes, filepath)


# ═══════════════════════════════════════════════════════════════════════════
# POSITIVE CASES — these SHOULD be flagged
# ═══════════════════════════════════════════════════════════════════════════


class TestPositiveVersionSuffix:
    """Classic _v2, _v3 versioning suffixes."""

    def test_v2_suffix_with_original(self):
        code = """
def search(query):
    return []

def search_v2(query):
    return [q for q in [] if query in q]
"""
        findings = run_detect(code)
        assert len(findings) == 1
        f = findings[0]
        assert f.detector == "abandoned_implementation"
        assert f.classification == FindingClass.REVIEW
        assert f.evidence["function"] == "search_v2"
        assert f.evidence["base"] == "search"

    def test_v3_suffix_with_original(self):
        code = """
def process(data):
    return data

def process_v3(data):
    return sorted(data)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].evidence["function"] == "process_v3"

    def test_large_version_number(self):
        """_v10 should be recognised the same as _v2."""
        code = """
def render(template):
    return template

def render_v10(template):
    return template.strip()
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].evidence["function"] == "render_v10"


class TestPositiveWordSuffixes:
    """Semantic suffixes: _new, _final, _old, _temp, etc."""

    def test_new_suffix(self):
        code = """
def parse_config(path):
    pass

def parse_config_new(path):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].evidence["function"] == "parse_config_new"

    def test_final_suffix(self):
        code = """
def validate(x):
    return True

def validate_final(x):
    return bool(x)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].evidence["function"] == "validate_final"

    def test_old_suffix(self):
        code = """
def format_date(dt):
    return str(dt)

def format_date_old(dt):
    return dt.isoformat()
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].evidence["function"] == "format_date_old"

    def test_deprecated_suffix(self):
        code = """
def send(msg):
    pass

def send_deprecated(msg):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].evidence["function"] == "send_deprecated"

    def test_legacy_suffix(self):
        code = """
def authenticate(user):
    pass

def authenticate_legacy(user):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_backup_suffix(self):
        code = """
def save(data):
    pass

def save_backup(data):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_orig_suffix(self):
        code = """
def compute(n):
    return n * 2

def compute_orig(n):
    return n + n
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_temp_suffix(self):
        code = """
def build(items):
    return items

def build_temp(items):
    return list(items)
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_refactored_suffix(self):
        code = """
def load(path):
    pass

def load_refactored(path):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_revised_suffix(self):
        code = """
def export(data):
    pass

def export_revised(data):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1


class TestPositiveMultipleVersions:
    """Multiple versioned functions referencing the same base."""

    def test_two_versioned_variants(self):
        """Both _v2 and _new are flagged when original exists."""
        code = """
def search(q):
    pass

def search_v2(q):
    pass

def search_new(q):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 2
        names = {f.evidence["function"] for f in findings}
        assert names == {"search_v2", "search_new"}

    def test_three_versioned_variants(self):
        code = """
def process(data):
    pass

def process_v2(data):
    pass

def process_v3(data):
    pass

def process_final(data):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 3


class TestPositiveClassMethods:
    """Versioned methods inside a class body should be detected."""

    def test_class_method_versioned(self):
        code = """
class Searcher:
    def search(self, query):
        return []

    def search_v2(self, query):
        return [q for q in [] if query in q]
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].evidence["function"] == "search_v2"


class TestPositiveLineNumbers:
    """Verify line numbers are 1-indexed and correct."""

    def test_line_number_accuracy(self):
        code = """def original(x):
    return x

def original_v2(x):
    return x + 1
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].line == 4  # 1-indexed

    def test_filepath_in_finding(self):
        code = """
def foo(x):
    pass

def foo_old(x):
    pass
"""
        findings = run_detect(code, filepath="mymodule/utils.py")
        assert len(findings) == 1
        assert findings[0].file == "mymodule/utils.py"


# ═══════════════════════════════════════════════════════════════════════════
# NEGATIVE CASES — these must NOT be flagged
# ═══════════════════════════════════════════════════════════════════════════


class TestNegativeNoOriginal:
    """No base function → no flag, even if suffix matches."""

    def test_versioned_without_original(self):
        """search_v2 exists but 'search' does not → should not fire."""
        code = """
def search_v2(query):
    return []
"""
        assert len(run_detect(code)) == 0

    def test_legacy_without_original(self):
        code = """
def handler_legacy(req):
    pass
"""
        assert len(run_detect(code)) == 0

    def test_old_without_original(self):
        code = """
def parse_config_old(path):
    pass
"""
        assert len(run_detect(code)) == 0

    def test_deprecated_without_original(self):
        code = """
def send_deprecated(msg):
    pass
"""
        assert len(run_detect(code)) == 0


class TestNegativeStandaloneSuffixWords:
    """Functions whose name IS the suffix word — should not fire."""

    def test_function_named_new(self):
        """'new' alone has no suffix to strip."""
        code = """
def new():
    pass
"""
        assert len(run_detect(code)) == 0

    def test_function_named_old(self):
        code = """
def old():
    pass
"""
        assert len(run_detect(code)) == 0

    def test_function_named_temp(self):
        code = """
def temp():
    pass
"""
        assert len(run_detect(code)) == 0


class TestNegativeTooShortBase:
    """Functions whose base after suffix removal is too short."""

    def test_single_char_base(self):
        """'f_v2' strips to 'f', which is < MIN_BASE_LEN → not flagged."""
        code = """
def f(x):
    pass

def f_v2(x):
    pass
"""
        # Base 'f' has length 1 < 2, so should not fire
        assert len(run_detect(code)) == 0

    def test_two_char_base_is_accepted(self):
        """'go_v2' strips to 'go' (length 2) → should fire if 'go' exists."""
        code = """
def go():
    pass

def go_v2():
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1


class TestNegativeNestedFunctions:
    """Functions nested inside other functions should not be flagged."""

    def test_nested_not_detected(self):
        """Inner versioned helper inside a closure should not fire."""
        code = """
def outer():
    def inner(x):
        return x

    def inner_v2(x):
        return x + 1

    return inner_v2
"""
        # 'inner' is defined but nested — should not be collected
        assert len(run_detect(code)) == 0


class TestNegativeCommonLegitimatePatterns:
    """Real-world patterns that must NOT be flagged as abandoned."""

    def test_v1_in_api_versioning(self):
        """API version strings in routes/handlers have no 'v1' base."""
        code = """
def api_v1_handler(request):
    pass

def api_v2_handler(request):
    pass
"""
        # base of api_v1_handler would be 'api', base of api_v2_handler → 'api'
        # 'api' is not defined as a function → should not fire for either
        # Actually api_v1_handler strips _v1 → base = api_v1_handler[:-3]... 
        # Wait, _v1 IS matched by the regex. base = "api" ... "api" not in names.
        # So these should NOT fire.
        assert len(run_detect(code)) == 0

    def test_no_false_positive_on_ordinary_names(self):
        """Ordinary function names with no recognisable suffix."""
        code = """
def process_data(items):
    return items

def validate_input(data):
    return bool(data)

def send_response(resp):
    pass
"""
        assert len(run_detect(code)) == 0

    def test_suffix_in_middle_of_name(self):
        """'old' and 'new' as part of the middle of a name — not a suffix."""
        code = """
def get_old_records():
    pass

def get_new_records():
    pass
"""
        # Neither ends with _old or _new
        assert len(run_detect(code)) == 0

    def test_double_underscore_not_flagged(self):
        """Edge case: names with double underscores."""
        code = """
def setup():
    pass

def setup__v2():
    pass
"""
        # After stripping _v2 from setup__v2 → base is "setup_" which ends with _
        # → should NOT fire
        assert len(run_detect(code)) == 0

    def test_empty_file(self):
        assert len(run_detect("")) == 0

    def test_file_with_no_functions(self):
        code = """
x = 1
y = "hello"
CONSTANT = 42
"""
        assert len(run_detect(code)) == 0


class TestNegativeCaseSensitivity:
    """Suffix matching is case-insensitive per the regex flag."""

    def test_uppercase_suffix_flagged(self):
        """_V2 (uppercase) should also be recognised."""
        code = """
def render(t):
    pass

def render_V2(t):
    pass
"""
        findings = run_detect(code)
        # The regex uses IGNORECASE so this should fire
        assert len(findings) == 1

    def test_mixed_case_suffix(self):
        """_New and _OLD should be recognised."""
        code = """
def fetch(url):
    pass

def fetch_New(url):
    pass
"""
        findings = run_detect(code)
        assert len(findings) == 1


class TestFindingStructure:
    """Verify that Finding objects have correct structure."""

    def test_finding_fields(self):
        code = """
def process(data):
    return data

def process_v2(data):
    return sorted(data)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        f = findings[0]

        assert f.detector == "abandoned_implementation"
        assert f.classification == FindingClass.REVIEW
        assert isinstance(f.file, str)
        assert isinstance(f.line, int)
        assert f.line >= 1
        assert "Potentially Superseded Implementation" in f.message
        assert f.message.startswith("process_v2")
        assert "function" in f.evidence
        assert "base" in f.evidence
        assert f.evidence["function"] == "process_v2"
        assert f.evidence["base"] == "process"

    def test_message_wording_per_spec(self):
        """CLAUDE.md §7.3: message must use 'Potentially Superseded Implementation'."""
        code = """
def foo(x):
    pass

def foo_old(x):
    pass
"""
        findings = run_detect(code)
        assert "Potentially Superseded Implementation" in findings[0].message

    def test_wording_does_not_contain_forbidden_terms(self):
        """Per CLAUDE.md §6.4 and §7.3: forbidden action words must not appear."""
        code = """
def bar(x):
    pass

def bar_v2(x):
    pass
"""
        findings = run_detect(code)
        msg = findings[0].message.lower()
        for forbidden in ["delete", "remove", "dead", "unused", "duplicate", "unsafe"]:
            assert forbidden not in msg, f"Forbidden word '{forbidden}' in message: {msg}"
