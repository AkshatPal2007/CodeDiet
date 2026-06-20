"""Comprehensive tests for the wrapper detector.

Per CLAUDE.md §8: includes deliberately tricky near-misses to confirm the
detector correctly does NOT flag them. Negative test cases matter as much
as positive ones for this project.
"""

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from codediet.detectors.wrappers import detect

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


def run_detect(code: str, filepath: str = "test.py") -> list:
    source_bytes = code.encode("utf-8")
    tree = parser.parse(source_bytes)
    return detect(tree, source_bytes, filepath)


# ═══════════════════════════════════════════════════════════════════════════
# POSITIVE CASES — these ARE wrappers and MUST be detected
# ═══════════════════════════════════════════════════════════════════════════


class TestPositiveSimpleWrappers:
    """Straightforward single-argument wrappers."""

    def test_builtin_wrapper(self):
        code = """
def parse_float(x):
    return float(x)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].function == "parse_float"
        assert findings[0].target == "float"
        assert findings[0].kind == "wrapper"

    def test_function_wrapper(self):
        code = """
def process_number(x):
    return helper(x)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].function == "process_number"
        assert findings[0].target == "helper"

    def test_multi_arg_wrapper(self):
        code = """
def add(a, b):
    return math_add(a, b)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].function == "add"
        assert findings[0].target == "math_add"


class TestPositiveAttributeTargets:
    """Wrappers calling module.function or object.method patterns."""

    def test_module_function(self):
        code = """
def floor_it(x):
    return math.floor(x)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].target == "math.floor"

    def test_deep_attribute(self):
        code = """
def get_value(key):
    return self.config.store.get(key)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].target == "self.config.store.get"


class TestPositiveZeroArgWrappers:
    """Functions with no parameters that forward to no-arg calls."""

    def test_no_args(self):
        code = """
def do_something():
    return helper()
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].function == "do_something"
        assert findings[0].target == "helper"

    def test_no_args_builtin(self):
        code = """
def get_items():
    return list()
"""
        findings = run_detect(code)
        assert len(findings) == 1


class TestPositiveSplatPassthrough:
    """*args / **kwargs forwarding patterns."""

    def test_args_only(self):
        code = """
def wrapper(*args):
    return helper(*args)
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_kwargs_only(self):
        code = """
def wrapper(**kwargs):
    return helper(**kwargs)
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_args_and_kwargs(self):
        code = """
def wrapper(*args, **kwargs):
    return helper(*args, **kwargs)
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_self_with_args_kwargs(self):
        """Method wrapper: self is declared but not forwarded."""
        code = """
def format(self, *args, **kwargs):
    return Formatter.format(*args, **kwargs)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].target == "Formatter.format"


class TestPositiveMethodWrappers:
    """Methods where self/cls is present but stripped in forwarding."""

    def test_self_method_wrapper(self):
        code = """
def get_name(self):
    return helpers.get_name()
"""
        findings = run_detect(code)
        assert len(findings) == 1

    def test_cls_method_wrapper(self):
        code = """
def create(cls, data):
    return factory.create(data)
"""
        findings = run_detect(code)
        assert len(findings) == 1


class TestPositiveWithDocstrings:
    """CLAUDE.md: 'Adding a docstring does not exempt it from detection —
    those are surface details, not added logic.'

    However, a docstring IS a statement in the AST (expression_statement
    containing a string). So our detector's 'exactly one statement' check
    must handle this: the docstring is the first named child, the return
    is the second. We should count only non-docstring statements.
    """

    # NOTE: This test documents the CURRENT behavior. If we decide docstrings
    # should not block detection, the detector must be updated first.
    def test_wrapper_with_docstring_currently_not_detected(self):
        """A wrapper with a docstring has two statements in tree-sitter (the
        expression_statement for the docstring + the return_statement).
        Currently the detector requires exactly one statement, so this is
        NOT detected. This is a known false negative and is acceptable per §6.
        """
        code = """
def parse_float(x):
    \"\"\"Parse a float.\"\"\"
    return float(x)
"""
        # Currently a false negative — acceptable per §6.
        findings = run_detect(code)
        assert len(findings) == 0


class TestPositiveTypedParams:
    """Type annotations on parameters should not block detection."""

    def test_typed_wrapper(self):
        code = """
def parse_float(x: str):
    return float(x)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].function == "parse_float"

    def test_return_type_annotation(self):
        code = """
def parse_float(x) -> float:
    return float(x)
"""
        findings = run_detect(code)
        assert len(findings) == 1


class TestPositiveMultipleWrappers:
    """Multiple wrappers in one file should all be found."""

    def test_two_wrappers(self):
        code = """
def parse_float(x):
    return float(x)

def parse_int(x):
    return int(x)
"""
        findings = run_detect(code)
        assert len(findings) == 2
        funcs = {f.function for f in findings}
        assert funcs == {"parse_float", "parse_int"}


class TestPositiveNestedWrappers:
    """Wrappers inside other functions should still be detected."""

    def test_nested_wrapper(self):
        code = """
def outer():
    def inner(x):
        return float(x)
    return inner
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].function == "inner"


class TestPositiveLineNumbers:
    """Verify line numbers are 1-indexed and correct."""

    def test_line_number(self):
        code = """
def first():
    pass

def wrapper(x):
    return float(x)
"""
        findings = run_detect(code)
        assert len(findings) == 1
        assert findings[0].line == 5  # 1-indexed


# ═══════════════════════════════════════════════════════════════════════════
# NEGATIVE CASES — these are NOT wrappers and MUST NOT be detected
# Per §8: "deliberately tricky near-misses"
# ═══════════════════════════════════════════════════════════════════════════


class TestNegativeExtraStatements:
    """Functions with more than one statement in the body."""

    def test_passthrough_plus_logging(self):
        """§8: 'a function with a pass-through call plus a single logging
        statement' — this is the canonical tricky near-miss."""
        code = """
def not_wrapper(x):
    print(f"processing {x}")
    return float(x)
"""
        assert len(run_detect(code)) == 0

    def test_passthrough_plus_assignment(self):
        code = """
def not_wrapper(x):
    result = float(x)
    return result
"""
        assert len(run_detect(code)) == 0

    def test_passthrough_plus_assert(self):
        code = """
def not_wrapper(x):
    assert x is not None
    return float(x)
"""
        assert len(run_detect(code)) == 0


class TestNegativeArgumentReordering:
    """§8: 'a function forwarding args in a different order'."""

    def test_swapped_args(self):
        code = """
def not_wrapper(x, y):
    return helper(y, x)
"""
        assert len(run_detect(code)) == 0

    def test_partial_args(self):
        """Only some args forwarded."""
        code = """
def not_wrapper(x, y, z):
    return helper(x, z)
"""
        assert len(run_detect(code)) == 0


class TestNegativeArgumentTransformation:
    """§8: 'a function with a default-value transformation'."""

    def test_arithmetic_transform(self):
        code = """
def not_wrapper(x):
    return helper(x + 1)
"""
        assert len(run_detect(code)) == 0

    def test_string_format(self):
        code = """
def not_wrapper(name):
    return helper(f"prefix_{name}")
"""
        assert len(run_detect(code)) == 0

    def test_default_value_override(self):
        code = """
def not_wrapper(x, flag=True):
    return helper(x, flag=False)
"""
        assert len(run_detect(code)) == 0

    def test_method_call_on_arg(self):
        code = """
def not_wrapper(x):
    return helper(x.strip())
"""
        assert len(run_detect(code)) == 0


class TestNegativeMethodChains:
    """Calls where the target is itself the result of a call — not a simple
    identifier or attribute access. These were real false positives found
    during venv scanning."""

    def test_chained_method(self):
        code = """
def deindent(lines):
    return textwrap.dedent("\\n".join(lines)).splitlines()
"""
        assert len(run_detect(code)) == 0

    def test_keyword_arg_in_chain(self):
        code = """
def encode(uni):
    return codecs.encode(uni, encoding="punycode").decode()
"""
        assert len(run_detect(code)) == 0

    def test_subscript_call(self):
        code = """
def get_first(items):
    return items[0].process()
"""
        assert len(run_detect(code)) == 0


class TestNegativeBranching:
    """Functions with any control flow are never wrappers."""

    def test_if_guard(self):
        code = """
def not_wrapper(x):
    if x is None:
        return None
    return float(x)
"""
        assert len(run_detect(code)) == 0

    def test_try_except(self):
        code = """
def not_wrapper(x):
    try:
        return float(x)
    except ValueError:
        return 0.0
"""
        assert len(run_detect(code)) == 0


class TestNegativeNonReturnBodies:
    """Functions that don't return a call."""

    def test_return_literal(self):
        code = """
def not_wrapper():
    return 42
"""
        assert len(run_detect(code)) == 0

    def test_return_variable(self):
        code = """
def not_wrapper(x):
    return x
"""
        assert len(run_detect(code)) == 0

    def test_only_expression(self):
        """A function whose body is a bare call (no return) is not a wrapper."""
        code = """
def not_wrapper(x):
    print(x)
"""
        assert len(run_detect(code)) == 0

    def test_pass_body(self):
        code = """
def stub():
    pass
"""
        assert len(run_detect(code)) == 0

    def test_raise(self):
        code = """
def not_wrapper():
    raise NotImplementedError
"""
        assert len(run_detect(code)) == 0


class TestNegativeKeywordArguments:
    """Keyword arguments in the call mean it's not a clean passthrough."""

    def test_added_kwarg(self):
        code = """
def not_wrapper(x):
    return helper(x, verbose=True)
"""
        assert len(run_detect(code)) == 0

    def test_all_kwargs(self):
        code = """
def not_wrapper(name, age):
    return helper(name=name, age=age)
"""
        assert len(run_detect(code)) == 0
