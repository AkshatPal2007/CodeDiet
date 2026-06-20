"""Wrapper function detector.

Detects functions whose entire body is a single pass-through call to another
function or builtin, forwarding arguments unchanged, with no added logic.

Detection requirements (ALL must hold for a finding to fire):
  - Function body contains exactly one statement.
  - That statement is a `return`.
  - The return value is a call expression.
  - Arguments are forwarded unchanged — same identifiers, same order, or a
    clean *args/**kwargs passthrough. No reordering, no transformation.
  - No branching, no side effects, no decorators that add logic.

When in doubt, do NOT flag. False negatives are acceptable; false positives
are not. See CLAUDE.md §6 for the full rationale.
"""

from __future__ import annotations

from tree_sitter import Node

from codediet.models import Finding


def detect(tree: object, source: bytes, filepath: str) -> list[Finding]:
    """Walk the parse tree and return wrapper-function findings.

    Args:
        tree: A tree-sitter parse Tree for a single Python file.
        source: The raw source bytes of the file (used to extract node text).
        filepath: Display path to include in each Finding.

    Returns:
        A list of Finding objects, one per detected wrapper function.
        Returns an empty list if none are found.
    """
    findings: list[Finding] = []
    _walk(tree.root_node, source, filepath, findings)
    return findings


def _walk(node: Node, source: bytes, filepath: str, findings: list[Finding]) -> None:
    """Recursively walk the tree, checking every function definition."""
    if node.type == "function_definition":
        finding = _check_function(node, source, filepath)
        if finding is not None:
            findings.append(finding)
        # Still recurse — nested functions can be wrappers too.

    for child in node.children:
        _walk(child, source, filepath, findings)


def _check_function(node: Node, source: bytes, filepath: str) -> Finding | None:
    """Return a Finding if `node` is a wrapper function, else None."""
    # --- locate the function name ---
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None
    func_name = _text(name_node, source)

    # --- locate the body block ---
    body_node = node.child_by_field_name("body")
    if body_node is None:
        return None

    # body is a `block` node; its children include newline/indent tokens.
    # We only want actual statement nodes.
    statements = [c for c in body_node.children if c.is_named]
    if len(statements) != 1:
        return None

    stmt = statements[0]
    if stmt.type != "return_statement":
        return None

    # return_statement children: the keyword token + the expression.
    return_value = stmt.child_by_field_name("value") if hasattr(stmt, "child_by_field_name") else None
    if return_value is None:
        # Fallback: find the first named child that isn't the keyword.
        named_children = [c for c in stmt.children if c.is_named]
        if not named_children:
            return None
        return_value = named_children[0]

    if return_value.type != "call":
        return None

    # --- extract and validate the call target ---
    call_func_node = return_value.child_by_field_name("function")
    if call_func_node is None:
        return None
    if not _is_simple_target(call_func_node):
        return None
    target_name = _text(call_func_node, source)

    # --- validate argument pass-through ---
    if not _args_are_passthrough(node, return_value, source):
        return None

    return Finding(
        kind="wrapper",
        file=filepath,
        line=node.start_point[0] + 1,  # tree-sitter rows are 0-indexed
        function=func_name,
        target=target_name,
    )


def _is_simple_target(node: Node) -> bool:
    """Return True if node is an identifier or attribute chain (e.g. self.helper),
    and does not contain nested calls, indexing, or other operations.
    """
    if node.type == "identifier":
        return True
    if node.type == "attribute":
        obj = node.child_by_field_name("object")
        return obj is not None and _is_simple_target(obj)
    return False


def _args_are_passthrough(func_node: Node, call_node: Node, source: bytes) -> bool:
    """Return True only if call arguments are a clean forwarding of the
    function's own parameters (same names, same order, no transformations).

    Accepts:
      - Identical positional args in the same order.
      - *args/**kwargs splat passthrough (individually or combined).
      - Empty args on both sides (zero-argument wrapper).
      - Method wrappers where `self`/`cls` is the first param but not forwarded.

    Rejects anything that looks like a transformation or reordering.
    """
    params_node = func_node.child_by_field_name("parameters")
    args_node = call_node.child_by_field_name("arguments")

    func_params = _extract_param_names(params_node, source) if params_node else []
    call_args = _extract_call_arg_names(args_node, source) if args_node else []

    # If the function takes no params and the call has no args — it's a wrapper.
    if not func_params and not call_args:
        return True

    # Strip self/cls from the parameter list for method wrappers.
    effective_params = func_params
    if func_params and func_params[0] in ("self", "cls"):
        effective_params = func_params[1:]

    # Direct positional match (with or without self/cls stripped).
    if effective_params == call_args:
        return True

    # Pure *args/**kwargs forwarding (combined or individual).
    splat_args = {a for a in call_args if a.startswith("*")}
    if call_args and splat_args == set(call_args):
        # All call args are splats — check the function also declares them.
        splat_params = {p for p in effective_params if p.startswith("*")}
        if splat_args == splat_params:
            return True

    return False


def _extract_param_names(params_node: Node, source: bytes) -> list[str]:
    """Extract bare parameter identifiers from a `parameters` node."""
    names: list[str] = []
    for child in params_node.children:
        if child.type == "identifier":
            names.append(_text(child, source))
        elif child.type in ("typed_parameter", "default_parameter",
                            "typed_default_parameter"):
            # Try the 'name' field first, fall back to first identifier child.
            ident = child.child_by_field_name("name")
            if ident is None:
                ident = next(
                    (c for c in child.children if c.type == "identifier"), None
                )
            if ident:
                names.append(_text(ident, source))
        elif child.type == "list_splat_pattern":  # *args
            inner = next((c for c in child.children if c.type == "identifier"), None)
            if inner:
                names.append("*" + _text(inner, source))
        elif child.type == "dictionary_splat_pattern":  # **kwargs
            inner = next((c for c in child.children if c.type == "identifier"), None)
            if inner:
                names.append("**" + _text(inner, source))
    return names


def _extract_call_arg_names(args_node: Node, source: bytes) -> list[str]:
    """Extract argument identifiers / splat tokens from an `argument_list` node."""
    names: list[str] = []
    for child in args_node.children:
        if child.type == "identifier":
            names.append(_text(child, source))
        elif child.type == "list_splat":  # *args at call site
            inner = next((c for c in child.children if c.type == "identifier"), None)
            if inner:
                names.append("*" + _text(inner, source))
        elif child.type == "dictionary_splat":  # **kwargs at call site
            inner = next((c for c in child.children if c.type == "identifier"), None)
            if inner:
                names.append("**" + _text(inner, source))
        # keyword_argument, lambda, etc. → not a clean passthrough, skip/reject
        elif child.type not in (",", "(", ")"):
            # Anything unexpected (transformation, keyword arg) → signal failure
            return ["__non_passthrough__"]
    return names


def _text(node: Node, source: bytes) -> str:
    """Extract the UTF-8 text of a tree-sitter node from the source bytes."""
    return source[node.start_byte:node.end_byte].decode("utf-8")
