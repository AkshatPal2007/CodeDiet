"""CodeDiet CLI — entrypoint for the `codediet` command."""

from __future__ import annotations

from pathlib import Path

import typer

from codediet.api import scan
from codediet.parser import walk_python_files
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
        num_files = 1
    else:
        num_files = len(walk_python_files(path))

    all_findings = scan(path)

    if json:
        report_json(all_findings)
    else:
        report_text(all_findings, num_files)


def main() -> None:
    app()

