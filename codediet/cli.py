"""CodeDiet CLI — entrypoint for the `codediet` command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from codediet.api import scan
from codediet.exporter import export_findings
from codediet.models import FindingClass
from codediet.parser import walk_python_files
from codediet.prompt_builder import build_prompt
from codediet.reporter import report_json, report_text

app = typer.Typer(
    name="codediet",
    help="Put AI-generated code on a diet. Detects structural bloat in Python codebases.",
    add_completion=False,
)


@app.callback()
def callback() -> None:
    """Put AI-generated code on a diet. Detects structural bloat in Python codebases."""
    pass


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
    export: Optional[Path] = typer.Option(
        None,
        "--export",
        help=(
            "Write findings to a file.  Extension determines format: "
            ".md for Markdown, anything else for plain text.  "
            "Always written even when there are no findings."
        ),
        writable=True,
        resolve_path=True,
    ),
    prompt: bool = typer.Option(
        False,
        "--prompt",
        help=(
            "Append a ready-to-copy LLM hand-off prompt to the export file.  "
            "Has no effect without --export."
        ),
    ),
    error_on_facts: bool = typer.Option(
        False,
        "--error-on-facts",
        help=(
            "Exit with code 1 if any FACT-class findings are detected.  "
            "Useful for failing CI pipelines on deterministic bloat."
        ),
    ),
) -> None:
    """Scan PATH for structural code bloat."""
    if path.is_file():
        num_files = 1
    else:
        num_files = len(walk_python_files(path))

    all_findings = scan(path)

    # ── Terminal output ───────────────────────────────────────────────────────
    if json:
        report_json(all_findings)
    else:
        report_text(all_findings, num_files)

    # ── File export (optional) ────────────────────────────────────────────────
    if export is not None:
        prompt_text: str | None = None
        if prompt:
            prompt_text = build_prompt(all_findings)

        export_findings(
            findings=all_findings,
            output_path=export,
            repo_path=path,
            files_scanned=num_files,
            prompt_text=prompt_text,
        )

        typer.echo(f"\nFindings written to: {export}", err=True)
        if prompt:
            typer.echo("LLM hand-off prompt appended.", err=True)
    elif prompt:
        typer.echo(
            "Warning: --prompt has no effect without --export.", err=True
        )

    # ── Exit code ─────────────────────────────────────────────────────────────
    if error_on_facts:
        facts = [f for f in all_findings if f.classification == FindingClass.FACT]
        if facts:
            raise typer.Exit(code=1)


def main() -> None:
    app()
