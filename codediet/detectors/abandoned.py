"""Abandoned Implementation Detector.

Detects functions whose names suggest they are versioned or iterative
replacements of an earlier function in the same file. Examples:

    def search(query): ...
    def search_v2(query): ...    ← flagged
    def search_final(query): ... ← flagged

Detection requirements (ALL must hold for a finding to fire):

  1. The function name ends with a recognised abandonment suffix
     (e.g. ``_v2``, ``_new``, ``_final``, ``_old``, ``_deprecated``).
  2. A function whose name equals the stripped base name ALSO exists
     somewhere in the same file. Without the original, a versioned name
     may simply be a project naming convention rather than leftover bloat.
  3. The function is defined at module level or directly inside a class body.
     Deeply nested helpers are excluded to avoid noise.

When in doubt, do NOT flag. False negatives are explicitly preferred over
false positives.

Classification: REVIEW — never FACT. Human inspection must confirm whether
the older version is genuinely superseded.

Per CLAUDE.md §7.3: output wording is "Potentially Superseded
Implementation" — never "delete the old one," never "this is dead code."
"""

from __future__ import annotations

import re

from tree_sitter import Node

from codediet.models import Finding, FindingClass

# ---------------------------------------------------------------------------
# Suffix pattern — matches at the END of a function name only.
# Prefixes (new_foo, old_foo) are excluded: they are ambiguous in practice
# (e.g. ``new_user`` is a constructor idiom, not an abandoned replacement).
# ---------------------------------------------------------------------------
_SUFFIX_RE = re.compile(
    r"_v\d+$"           # _v2, _v3, _v10  …
    r"|_new$"
    r"|_final$"
    r"|_old$"
    r"|_temp$"
    r"|_tmp$"
    r"|_backup$"
    r"|_bak$"
    r"|_deprecated$"
    r"|_legacy$"
    r"|_orig$"
    r"|_original$"
    r"|_latest$"
    r"|_revised$"
    r"|_updated$"
    r"|_refactored$",
    re.IGNORECASE,
)

# Minimum length of the base name after suffix removal.
# Prevents spurious bases like "f" from a function named "f_v2".
_MIN_BASE_LEN: int = 2


def detect(tree: object, source: bytes, filepath: str) -> list[Finding]:
    """Walk the parse tree and return abandoned-implementation findings.

    Args:
        tree:      A tree-sitter parse Tree for a single Python file.
        source:    Raw source bytes (used to extract node text).
        filepath:  Display path included in each Finding.

    Returns:
        A list of Finding objects, one per detected versioned function.
        Returns an empty list if none are found.
    """
    items = _collect_functions(tree.root_node, source)
    all_names: set[str] = {name for name, _ in items}

    findings: list[Finding] = []
    for func_name, func_node in items:
        base = _strip_suffix(func_name)
        if base is None:
            continue
        if base not in all_names:
            # The presumed "original" does not exist in this file — skip.
            continue
        findings.append(
            Finding(
                detector="abandoned_implementation",
                classification=FindingClass.REVIEW,
                file=filepath,
                line=func_node.start_point[0] + 1,  # tree-sitter rows are 0-indexed
                message=f"{func_name} — Potentially Superseded Implementation",
                evidence={"function": func_name, "base": base},
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _collect_functions(
    node: Node, source: bytes, _inside_function: bool = False
) -> list[tuple[str, Node]]:
    """Recursively collect function definitions at module or class-body level.

    Skips functions that are nested inside another function body to avoid
    flagging ordinary inner helpers (closures, factory patterns, etc.).
    """
    results: list[tuple[str, Node]] = []

    if node.type == "function_definition":
        if not _inside_function:
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                results.append((_text(name_node, source), node))
        # Recurse into the function body, but mark ourselves as inside one.
        for child in node.children:
            results.extend(
                _collect_functions(child, source, _inside_function=True)
            )
        return results

    for child in node.children:
        results.extend(
            _collect_functions(child, source, _inside_function=_inside_function)
        )
    return results


def _strip_suffix(name: str) -> str | None:
    """Return the base name after stripping a recognised abandonment suffix.

    Returns None if:
     - no suffix matches,
     - the resulting base is too short (< _MIN_BASE_LEN characters),
     - or the base ends with an underscore (double-underscore edge cases).
    """
    match = _SUFFIX_RE.search(name)
    if match is None:
        return None
    suffix = match.group(0)
    base = name[: -len(suffix)]
    if len(base) < _MIN_BASE_LEN:
        return None
    if base.endswith("_"):
        # Avoids spurious bases like "search_" from "search__v2".
        return None
    return base


def _text(node: Node, source: bytes) -> str:
    """Extract the UTF-8 text of a tree-sitter node from the source bytes."""
    return source[node.start_byte : node.end_byte].decode("utf-8")
