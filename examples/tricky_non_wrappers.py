"""Example Python file containing tricky non-wrappers.

None of these should be detected by `codediet doctor`.
"""


# ---------------------------------------------------------------------------
# Stubs — stand-ins for external functions that would exist in a real codebase.
# ---------------------------------------------------------------------------
def helper(x, **kwargs):  # noqa: ANN001,ANN201
    return x


def compute(a, b):  # noqa: ANN001,ANN201
    return a


def parse_float_safe(x):
    """This looks like a wrapper but has a guard."""
    if x is None:
        return 0.0
    return float(x)


def process_and_log(x):
    """Pass-through call PLUS a logging side effect — not a wrapper."""
    print(f"Processing: {x}")
    return helper(x)


def transform_arg(x):
    """Forwards a transformed argument — not a clean passthrough."""
    return helper(x.strip())


def reordered(a, b):
    """Arguments forwarded in a different order."""
    return compute(b, a)


def with_extra_kwarg(x):
    """Adds a keyword argument not present in the original params."""
    return helper(x, verbose=True)


def assign_then_return(x):
    """Intermediate assignment breaks the single-statement rule."""
    result = float(x)
    return result
