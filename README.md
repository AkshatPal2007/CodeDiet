# CodeDiet

**Put AI-generated code on a diet.**

[![PyPI version](https://img.shields.io/pypi/v/codediet)](https://pypi.org/project/codediet/)
[![Python 3.12+](https://img.shields.io/pypi/pyversions/codediet)](https://pypi.org/project/codediet/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CodeDiet is a read-only static analysis CLI that detects structural bloat
introduced by AI coding assistants (Cursor, Claude Code, Copilot, Windsurf,
ChatGPT). It answers one question: *"does this code exist but probably not
need to?"*

It does not look for bugs, security issues, style violations, performance
problems, or dead code. Other tools already do those well (Ruff, Pylint,
Vulture, Semgrep). CodeDiet's territory is narrower and currently underserved:
structural bloat that is syntactically valid, passes every test, and is
invisible in a normal code review.

---

## Why This Exists

AI-generated code now accounts for a significant share of new commits in
AI-heavy repositories — and with it, code churn has risen substantially.
For the first time on record, duplicated/copy-pasted code volume has exceeded
refactored/moved code volume. The "path of least resistance" for an LLM is
additive, not corrective: it layers new wrapper/helper functions over existing
logic rather than reorganizing it.

Duplicate helpers, abandoned `_v2`/`_final` implementations, sprawling
`utils.py` files, pass-through wrapper functions — these don't break tests,
pass code review, and accumulate silently until the codebase becomes
genuinely hard to navigate.

---

## What It Detects

CodeDiet separates findings into two categories — the distinction is always
visible in output and is a core part of the tool's honesty model:

- **Facts** — mechanically verifiable structural claims. True by construction;
  no interpretation required.
- **Review Recommendations** — heuristic signals worth a human look, with no
  claim about what inspection will find.

### Shipped (v0.3)

**Wrapper Functions** *(Fact)* — functions whose entire body is a single
pass-through call to another function, forwarding arguments unchanged with no
added logic:

```python
# CodeDiet flags these as Facts — structurally confirmed
def parse_float(x):
    return float(x)

def file_exists(path):
    return os.path.exists(path)

def send(self, payload):
    return self._http.post(payload)
```

Detection is deterministic and mechanical — no AI, no heuristics, no
probabilistic scoring. Every fact-class finding is reproducible from the AST.

### Roadmap (specified, not yet implemented)

- **Duplicate Helper Detection** *(Review)* — functions with similar names,
  signatures, and structure (`safe_float`, `parse_float`, `ensure_float`).
- **Abandoned Implementation Detection** *(Review)* — `search_v2`, `search_new`,
  `search_final` left behind after iterative AI prompting.
- **Similar Module Detection** *(Review)* — files with unusually high structural
  overlap.
- **Utility Explosion Detection** *(Review)* — projects accumulating an unusual
  number of `helpers.py`, `utils.py`, `common.py` files.

Roadmap detectors are fully designed with exact output wording and reliability
tiers — not placeholders. The README will be updated as each ships.

---

## Installation

Requires Python 3.12+.

```bash
pip install codediet
```

Or install globally as a standalone command-line tool:
```bash
uv tool install codediet
pipx install codediet
```

---

## Usage

### Command Line

```bash
# Scan a directory — prints findings to stdout
codediet doctor .

# Scan a single file
codediet doctor path/to/file.py

# Output findings as structured JSON
codediet doctor . --json

# Write a portable findings file (Markdown or plain text)
codediet doctor . --export findings.md
codediet doctor . --export findings.txt

# Write findings + append a ready-to-copy LLM hand-off prompt
codediet doctor . --export findings.md --prompt
```

### Terminal Output

```
Files scanned: 42

FACTS — Mechanically Verifiable (3 found)

  [WRAPPER]
    utils.py:18
    parse_float -> float

  [WRAPPER]
    helpers.py:44
    file_exists -> os.path.exists

  [WRAPPER]
    client.py:91
    send -> self._http.post

REVIEW RECOMMENDATIONS — Heuristic Signals (0 found)
  (none)
```

### JSON Output (`--json`)

```json
{
  "facts": [
    {
      "detector": "wrapper",
      "file": "utils.py",
      "line": 18,
      "message": "parse_float -> float",
      "evidence": {
        "function": "parse_float",
        "target": "float"
      }
    }
  ],
  "review_recommendations": []
}
```

### Export File (`--export findings.md`)

Writes a portable Markdown (or plain-text) findings file — always written even
when there are no findings, because a clean run is itself useful information
(e.g. for a PR comment or changelog entry):

```markdown
# CodeDiet Findings — /my/project
Generated: 2026-07-01T12:00:00Z
Detector(s) run: wrapper

## Facts
(deterministic — these are structurally true as written)

### Wrapper
- `utils.py:18` — parse_float -> float
- `helpers.py:44` — file_exists -> os.path.exists

## Review Recommendations
(heuristic signals — worth a look, not a claim about the outcome)

_None in this run._

---
## Summary
- 2 Facts
- 0 Review Recommendations
- 42 files scanned
```

### LLM Hand-off Prompt (`--export findings.md --prompt`)

Appends a ready-to-copy prompt to the export file — paste it directly into
your own coding assistant (Claude Code, Cursor, Copilot Chat, ChatGPT, or
any other tool). CodeDiet never calls an LLM itself; it just builds the
prompt from its own findings so the handoff is exact and safe:

```
The following is output from CodeDiet, a read-only static analysis tool.
CodeDiet made no changes to this codebase. It performed purely structural,
deterministic static analysis — no LLMs, no embeddings, no probabilistic
inference of any kind was used to produce these findings.

Findings are split into two categories. Please treat them differently:

FACTS (structurally confirmed — true as written, by construction):
- utils.py:18 — `parse_float` is a pure pass-through wrapper around `float`.
  Consider whether it can be inlined or removed.

REVIEW RECOMMENDATIONS (heuristic signals — investigate before acting,
do not assume these are confirmed issues):
(none in this run)

For FACTS, you may propose a direct fix (for example, inlining a pure
pass-through wrapper) if it is appropriate for the context.

For REVIEW RECOMMENDATIONS, please investigate first and report back what
you find — do not modify code based on these signals alone.

Please summarize your proposed plan before making any edits.
```

No scores. No percentages. No rankings. No suggestions. CodeDiet reports
observations, never judgments — the developer decides what to do.

---

## Programmatic API

CodeDiet can be imported and used directly inside other Python codebases:

```python
from codediet import scan, Finding
from codediet.models import FindingClass

# Scan a project folder or a single file
findings = scan("/path/to/project")

# Separate facts from review recommendations
facts   = [f for f in findings if f.classification == FindingClass.FACT]
reviews = [f for f in findings if f.classification == FindingClass.REVIEW]

# Inspect findings
for f in facts:
    print(f"[{f.detector.upper()}] {f.file}:{f.line}")
    print(f"  {f.message}")
    print(f"  evidence: {f.evidence}")
```

The `Finding` dataclass fields:

| Field | Type | Description |
|---|---|---|
| `detector` | `str` | Detector name, e.g. `"wrapper"` |
| `classification` | `FindingClass` | `FACT` or `REVIEW` |
| `file` | `str` | Relative file path |
| `line` | `int` | Line number |
| `message` | `str` | Human-readable summary |
| `evidence` | `dict` | Structured, detector-specific data |

---

## Design Principles

- **Trust over feature count.** A tool that's wrong even occasionally gets
  uninstalled and not reconsidered. CodeDiet aggressively avoids false
  positives — it would rather miss a real wrapper than flag something that
  isn't one.
- **Deterministic.** No LLMs, no embeddings, no AI scoring. Every finding is
  mechanically reproducible from the AST alone.
- **Honest about uncertainty.** The Fact/Review distinction is a user-facing
  contract. Users always know whether a finding is a structural certainty or
  a "go look at this" signal.
- **Read-only.** CodeDiet never modifies source code, never generates fixes,
  never suggests deletions.
- **No composite scores.** No "Bloat Score: 57" — that's exactly the kind of
  output this project exists to NOT produce.
- **LLM-adjacent, not LLM-powered.** v0.3 generates prompts you can hand to
  your own AI assistant. CodeDiet itself uses zero LLM/embedding inference.

---

## Development

```bash
git clone https://github.com/AkshatPal2007/CodeDiet.git
cd CodeDiet
uv sync

# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check .

# Build distribution
uv build
```

---

## License

MIT
