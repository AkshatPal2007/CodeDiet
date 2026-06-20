"""Programmatic API for CodeDiet."""

from __future__ import annotations

from pathlib import Path

from codediet.detectors import wrappers
from codediet.models import Finding
from codediet.parser import parse_file, walk_python_files


def scan(path: str | Path) -> list[Finding]:
    """Scan a Python file or directory for wrapper functions programmatically.

    Args:
        path: The filesystem path to the Python file or directory to scan.

    Returns:
        A list of Finding objects representing the detected wrappers.

    Raises:
        FileNotFoundError: If the specified path does not exist.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Path does not exist: {path_obj}")

    if path_obj.is_file():
        files = [path_obj]
    else:
        files = walk_python_files(path_obj)

    all_findings: list[Finding] = []
    for file in files:
        try:
            tree, source = parse_file(file)
        except (OSError, UnicodeDecodeError):
            continue

        # Display path relative to the given root for cleaner programmatic outputs too.
        display_path = str(file.relative_to(path_obj)) if path_obj.is_dir() else str(file)
        all_findings.extend(wrappers.detect(tree, source, display_path))

    return all_findings
