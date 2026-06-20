# CodeDiet

**Put AI-generated code on a diet.**

CodeDiet is a read-only static analysis CLI that detects unnecessary structural
bloat caused by AI coding assistants (Cursor, Claude Code, Copilot, Windsurf,
ChatGPT). It answers one question: *"does this code exist but probably not
need to?"*

It does not look for bugs, security issues, style violations, performance
problems, or dead code. Other tools already do those well (Ruff, Pylint,
Vulture, Semgrep). CodeDiet's niche is structural bloat that is syntactically
valid, passes tests, and is invisible in normal code review.

## Why This Exists

AI-generated code now accounts for a significant share of new commits in
AI-heavy repositories — and with it, code churn has risen substantially.
For the first time on record, duplicated/copy-pasted code volume has exceeded
refactored/moved code volume. The "path of least resistance" for an LLM is
additive, not corrective: it layers new wrapper/helper functions over existing
logic rather than reorganizing it.

The specific anti-pattern CodeDiet targets — a function that does nothing but
forward a call — is a long-recognized code smell ("Middle Man"). LLMs simply
produce it at much higher volume because they operate on localized prompts
without awareness of existing utilities elsewhere in the codebase.

## What It Detects (v0.1)

**Wrapper Functions** — functions whose entire body is a single pass-through
call to another function, forwarding arguments unchanged with no added logic:

```python
# These are wrappers — CodeDiet will flag them
def parse_float(x):
    return float(x)

def process_number(x):
    return helper(x)
```

Detection is deterministic and mechanical — no AI, no heuristics, no
probabilistic scoring. Every finding is a structural fact derived from the AST.

## Installation

Requires Python 3.13+.

Install via `pip`:
```bash
pip install codediet
```

Or install globally as a command-line tool via `uv`:
```bash
uv tool install codediet
```

### Developing from Source
```bash
git clone https://github.com/AkshatPal2007/CodeDiet.git
cd CodeDiet
uv sync
```

## Usage

### Command Line Interface

If installed globally or via pip:
```bash
# Scan a directory
codediet .

# Scan a specific file
codediet path/to/file.py

# JSON output
codediet . --json
```

If running from the source tree with `uv`:
```bash
uv run codediet .
```

### Programmatic Library API

CodeDiet can also be imported and run directly inside other Python codebases:

```python
from codediet import scan

# Scan a project folder or a single file
findings = scan("/path/to/other/project")

# Process the findings programmatically
for finding in findings:
    print(f"[{finding.kind.upper()}] {finding.file}:{finding.line}")
    print(f"  {finding.function} -> {finding.target}")
```


### Text Output

```
Files scanned: 42

Wrapper Functions Found: 3

WRAPPER
  utils.py:18
  parse_float -> float

WRAPPER
  helpers.py:44
  process_number -> helper
```

### JSON Output

```json
{
  "wrappers": [
    {
      "file": "utils.py",
      "line": 18,
      "function": "parse_float",
      "target": "float"
    }
  ]
}
```

No scores. No percentages. No rankings. No suggestions. CodeDiet reports
observations, never judgments — the developer decides what to do.

## Design Principles

- **Trust over feature count.** A tool that's wrong even occasionally gets
  uninstalled and not reconsidered. CodeDiet aggressively avoids false
  positives — it would rather miss a real wrapper than flag something that
  isn't one.
- **Deterministic.** No LLMs, no embeddings, no AI scoring. Every finding is
  mechanically reproducible from the AST.
- **Read-only.** CodeDiet never modifies source code, never generates fixes,
  never suggests deletions.
- **No composite scores.** No "Bloat Score: 57" — that's exactly the kind of
  output this project exists to NOT produce.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check .
```

## License

MIT
