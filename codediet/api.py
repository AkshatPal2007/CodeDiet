"""Programmatic API for CodeDiet."""

from __future__ import annotations

from pathlib import Path

from codediet.detectors import abandoned, utility_explosion, wrappers
from codediet.models import Finding
from codediet.parser import parse_file, walk_python_files

# duplicate_helpers is implemented but excluded from v0.4 after real-repo
# validation showed an unacceptable false-positive rate on projects with
# tutorial/docs directories (e.g. FastAPI's docs_src/). Targeted for v0.5
# with an improved cross-directory exclusion strategy.
# from codediet.detectors import duplicate_helpers


def scan(path: str | Path) -> list[Finding]:
    """Scan a Python file or directory for structural code bloat.

    Runs all enabled detectors:
      - Wrapper Functions  (Fact)       — per-file, AST-based
      - Abandoned Implementations (Review) — per-file, AST-based
      - Duplicate Helpers  (Review)    — cross-file, AST-based
      - Utility Explosion  (Review)    — file-list heuristic

    Args:
        path: The filesystem path to the Python file or directory to scan.

    Returns:
        A list of Finding objects representing all detected issues,
        ordered facts first (by detector run order), then reviews.

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

    # ── Parse all files once; share the results across all detectors ────────
    parsed: list[tuple[object, bytes, str]] = []
    for file in files:
        try:
            tree, source = parse_file(file)
        except (OSError, UnicodeDecodeError):
            continue
        display_path = (
            str(file.relative_to(path_obj)) if path_obj.is_dir() else str(file)
        )
        parsed.append((tree, source, display_path))

    all_findings: list[Finding] = []

    # ── Per-file detectors ───────────────────────────────────────────────────
    for tree, source, display_path in parsed:
        all_findings.extend(wrappers.detect(tree, source, display_path))
        all_findings.extend(abandoned.detect(tree, source, display_path))

    # ── Cross-file detectors (excluded in v0.4 — see comment above) ─────────
    # all_findings.extend(duplicate_helpers.detect(parsed))

    # ── File-list detectors (receive display paths only) ─────────────────────
    display_paths = [dp for _, _, dp in parsed]
    all_findings.extend(utility_explosion.detect(display_paths))

    return all_findings
