"""CodeDiet CLI — entrypoint for the `codediet` command."""

from __future__ import annotations

from pathlib import Path

import typer

from codediet.detectors import wrappers
from codediet.models import Finding
from codediet.parser import parse_file, walk_python_files
from codediet.reporter import report_json, report_text

app = typer.Typer(
    name="codediet",
    help="Put AI-generated code on a diet. Detects structural bloat in Python codebases.",
    add_completion=False,
    invoke_without_command=True,
)


@app.command()
def doctor(
    path: Path = typer.Argument(
        ...,
        help="Path to a Python file or directory to analyse.",
        exists=True,
    ),
    json: bool = typer.Option(
        False,
        "--json",
        help="Output findings as JSON instead of plain text.",
    ),
) -> None:
    """Scan PATH for structural code bloat."""
    if path.is_file():
        files = [path]
    else:
        files = walk_python_files(path)

    all_findings: list[Finding] = []
    for file in files:
        try:
            tree, source = parse_file(file)
        except (OSError, UnicodeDecodeError):
            continue

        # Display path relative to the given root for cleaner output.
        display_path = str(file.relative_to(path)) if path.is_dir() else str(file)

        all_findings.extend(wrappers.detect(tree, source, display_path))

    if json:
        report_json(all_findings)
    else:
        report_text(all_findings, len(files))


def main() -> None:
    app()
