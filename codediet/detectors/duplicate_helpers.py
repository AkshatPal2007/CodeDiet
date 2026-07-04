"""Duplicate Helper Detector.

Detects clusters of functions that share the same semantic root name,
the same parameter count, and structurally similar AST fingerprints.
This pattern commonly emerges from AI-assisted development where multiple
"slight variation" helpers accumulate without being consolidated.

Example:

    def safe_float(x): ...     ┐
    def parse_float(x): ...    ├── cluster: root="float", 1 param, same structure
    def ensure_float(x): ...   ┘

Detection requirements (ALL must hold for a finding to fire):

  1. Two or more functions share the same semantic root after stripping ONE
     recognised transformation prefix or suffix from their names.
  2. Their effective parameter counts (excluding self/cls) are identical.
  3. Their AST fingerprints are identical — same sequence of top-level
     statement types in the function body.
  4. All functions in the cluster have body lengths ≤ _MAX_BODY_STMTS.
     Longer functions are more likely to be intentionally different despite
     similar names.

Conservative design decisions:
  - Exactly ONE affix is stripped per function name — not multiple layers.
  - Parameter counts must match exactly (not ±1 as originally proposed),
    because differ-by-one often means the functions have different contracts.
  - Fingerprints must be IDENTICAL, not "similar" (no fuzzy matching,
    no Jaccard scores, no probabilistic ranking).
  - Clusters only form within a single scan (all files passed to detect()).
    Cross-project comparisons are out of scope.

Classification: REVIEW — never FACT. The detector makes no claim that
the clustered functions are identical in behaviour or should be removed.
Per CLAUDE.md §7.2: output wording is "Review Cluster" — never "duplicate,"
never "these do the same thing," never "delete."
"""

from __future__ import annotations

from collections import defaultdict

from tree_sitter import Node

from codediet.models import Finding, FindingClass

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Maximum number of top-level statements in a function body.
# Functions longer than this are unlikely to be "accidental duplicates"
# and are excluded from clustering to reduce false positives.
_MAX_BODY_STMTS: int = 5

# ---------------------------------------------------------------------------
# Known transformation affixes.
# We strip exactly ONE of these from the start OR end of the function name.
# ---------------------------------------------------------------------------
_PREFIXES: tuple[str, ...] = (
    "safe_",
    "parse_",
    "ensure_",
    "get_",
    "to_",
    "as_",
    "make_",
    "build_",
    "create_",
    "convert_",
    "validate_",
    "check_",
    "is_",
)

_SUFFIXES: tuple[str, ...] = (
    "_safe",
    "_parsed",
    "_clean",
    "_cleaned",
    "_validated",
    "_strict",
    "_fast",
    "_optimized",
    "_optimised",
    "_checked",
)

# Minimum length of the root after stripping an affix.
_MIN_ROOT_LEN: int = 2

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def detect(
    parsed: list[tuple[object, bytes, str]],
) -> list[Finding]:
    """Detect duplicate-helper clusters across all scanned files.

    Args:
        parsed: A list of ``(tree, source, display_path)`` tuples produced
                by the scanner — one entry per successfully parsed file.

    Returns:
        One Finding per cluster (located at the first function in the cluster),
        or an empty list if no clusters meet the detection criteria.
    """
    # Step 1: collect all candidate functions across all files.
    candidates: list[_FuncInfo] = []
    for tree, source, filepath in parsed:
        candidates.extend(_collect_candidates(tree, source, filepath))

    # Step 2: group candidates by (semantic_root, param_count, fingerprint).
    # All three dimensions must match for two functions to be in the same cluster.
    groups: dict[tuple[str, int, tuple], list[_FuncInfo]] = defaultdict(list)
    for info in candidates:
        if info.root is None:
            continue  # no recognised affix → skip
        key = (info.root, info.param_count, info.fingerprint)
        groups[key].append(info)

    # Step 3: emit one Finding per cluster of size ≥ 2.
    findings: list[Finding] = []
    for (root, _param_count, _fp), members in groups.items():
        if len(members) < 2:
            continue
        cluster_names = [m.name for m in members]
        # Locate the finding at the first function in the cluster (file order).
        first = members[0]
        findings.append(
            Finding(
                detector="duplicate_helper",
                classification=FindingClass.REVIEW,
                file=first.filepath,
                line=first.line,
                message=", ".join(cluster_names),
                evidence={
                    "cluster": cluster_names,
                    "root": root,
                    "param_count": _param_count,
                },
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Internal data class
# ---------------------------------------------------------------------------


class _FuncInfo:
    """Lightweight holder for per-function detection data."""

    __slots__ = ("name", "root", "param_count", "fingerprint", "filepath", "line")

    def __init__(
        self,
        name: str,
        root: str | None,
        param_count: int,
        fingerprint: tuple,
        filepath: str,
        line: int,
    ) -> None:
        self.name = name
        self.root = root
        self.param_count = param_count
        self.fingerprint = fingerprint
        self.filepath = filepath
        self.line = line


# ---------------------------------------------------------------------------
# Function collection and analysis
# ---------------------------------------------------------------------------


def _collect_candidates(
    tree: object, source: bytes, filepath: str
) -> list[_FuncInfo]:
    """Walk the parse tree and collect function-level analysis data."""
    results: list[_FuncInfo] = []
    _walk(tree.root_node, source, filepath, results, inside_function=False)
    return results


def _walk(
    node: Node,
    source: bytes,
    filepath: str,
    results: list[_FuncInfo],
    inside_function: bool,
) -> None:
    if node.type == "function_definition":
        if not inside_function:
            info = _analyse_function(node, source, filepath)
            if info is not None:
                results.append(info)
        # Recurse into the body, marking it as inside a function.
        for child in node.children:
            _walk(child, source, filepath, results, inside_function=True)
        return

    for child in node.children:
        _walk(child, source, filepath, results, inside_function=inside_function)


def _analyse_function(
    node: Node, source: bytes, filepath: str
) -> "_FuncInfo | None":
    """Extract analysis data for a single function_definition node.

    Returns None if the function body exceeds _MAX_BODY_STMTS or if
    other data cannot be extracted.
    """
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None
    name = _text(name_node, source)

    body_node = node.child_by_field_name("body")
    if body_node is None:
        return None

    statements = [c for c in body_node.children if c.is_named]
    if len(statements) > _MAX_BODY_STMTS or len(statements) == 0:
        return None

    params_node = node.child_by_field_name("parameters")
    param_count = _count_params(params_node, source) if params_node else 0

    fingerprint = _compute_fingerprint(statements)
    root = _extract_root(name)

    return _FuncInfo(
        name=name,
        root=root,
        param_count=param_count,
        fingerprint=fingerprint,
        filepath=filepath,
        line=node.start_point[0] + 1,
    )


def _compute_fingerprint(statements: list[Node]) -> tuple:
    """Compute a deterministic structural fingerprint from the statement list.

    The fingerprint is the tuple of top-level statement node type strings.
    Two functions with identical fingerprints have the same control-flow
    skeleton, regardless of variable names or called targets.
    """
    return tuple(s.type for s in statements)


def _count_params(params_node: Node, source: bytes) -> int:
    """Count parameters, excluding self and cls."""
    count = 0
    for child in params_node.children:
        if child.type in (",", "(", ")"):
            continue
        if child.type == "identifier":
            name = _text(child, source)
            if name in ("self", "cls"):
                continue
            count += 1
        elif child.type in (
            "typed_parameter",
            "default_parameter",
            "typed_default_parameter",
        ):
            count += 1
        elif child.type in ("list_splat_pattern", "dictionary_splat_pattern"):
            count += 1
    return count


def _extract_root(name: str) -> str | None:
    """Return the semantic root of a function name by stripping ONE known affix.

    Tries prefixes first, then suffixes. Returns None if no affix matches
    or if the resulting root is too short.
    """
    for prefix in _PREFIXES:
        if name.startswith(prefix):
            root = name[len(prefix):]
            if len(root) >= _MIN_ROOT_LEN:
                return root
    for suffix in _SUFFIXES:
        if name.endswith(suffix):
            root = name[: -len(suffix)]
            if len(root) >= _MIN_ROOT_LEN:
                return root
    return None


def _text(node: Node, source: bytes) -> str:
    """Extract UTF-8 text of a tree-sitter node from source bytes."""
    return source[node.start_byte : node.end_byte].decode("utf-8")
