"""Tree-sitter setup, file discovery, and syntax tree construction.

Centralises all I/O and parsing concerns so detectors only receive
pre-built tree-sitter trees and never read files themselves.
"""

from __future__ import annotations

import os
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# Build the Python language object once at module import time.
PY_LANGUAGE = Language(tspython.language())

_parser = Parser(PY_LANGUAGE)


def parse_file(path: Path) -> tuple[object, bytes]:
    """Parse a single Python source file.

    Returns:
        A (tree, source_bytes) tuple where `tree` is the tree-sitter parse
        tree and `source_bytes` is the raw file content (needed by detectors
        to extract node text).
    """
    source = path.read_bytes()
    tree = _parser.parse(source)
    return tree, source


def walk_python_files(root: Path) -> list[Path]:
    """Recursively collect all .py files under `root`, excluding common virtual
    env and tool directories, sorted for stability."""
    ignored_dirs = {
        ".git", ".venv", "venv", "env", ".pytest_cache", ".ruff_cache",
        "__pycache__", "build", "dist", "node_modules"
    }
    python_files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Modify dirnames in-place to prevent os.walk from descending into them
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs and not d.startswith(".")]
        for filename in filenames:
            if filename.endswith(".py"):
                python_files.append(Path(dirpath) / filename)

    return sorted(python_files)

