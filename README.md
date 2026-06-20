# CodeDiet

**Put AI-generated code on a diet.**

CodeDiet is a read-only static analysis CLI that detects structural bloat
introduced by AI coding assistants (Cursor, Claude Code, Copilot, Windsurf,
ChatGPT). It answers one question: *"does this code exist but probably not
need to?"*

It does not look for bugs, security issues, style violations, performance
problems, or dead code. Other tools already do those well (Ruff, Pylint,
Vulture, Semgrep). CodeDiet's territory is narrower and currently underserved:
structural bloat that is syntactically valid, passes every test, and is
invisible in a normal code review.

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

## What It Detects

CodeDiet separates findings into two categories — the distinction matters and
is always visible in output:

- **Facts** — mechanically verifiable structural claims. True by construction;
  no interpretation required.
- **Review Recommendations** — heuristic signals worth a human look, with no
  claim about what inspection will find.

### Shipped (v0.2)

**Wrapper Functions** *(Fact)* — functions whose entire body is a single
pass-through call to another function, forwarding arguments unchanged with no
added logic:

```python
# These are wrappers — CodeDiet will flag them as Facts
def parse_float(x):
    return float(x)

def file_exists(path):
    return os.path.exists(path)
```

Detection is deterministic and mechanical — no AI, no heuristics, no
probabilistic scoring. Every fact-class finding is reproducible from the AST.

### Roadmap (documented, not yet implemented)

- **Duplicate Helper Detection** *(Review)* — functions with similar names,
  signatures, and structure, often the AI equivalent of reinventing the same
  helper under three names.
- **Abandoned Implementation Detection** *(Review)* — `search_v2`, `search_new`,
  `search_final` left behind after iterative prompting.
- **Similar Module Detection** *(Review)* — files with unusually high structural
  overlap.
- **Utility Explosion Detection** *(Review)* — projects accumulating an
  unusually large number of `helpers.py`, `utils.py`, `common.py` files.

Roadmap detectors are fully specified and designed — not placeholders — but
not yet implemented. The README will be updated as each ships.

## Installation

Requires Python 3.12+.

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

### Command Line

```bash
# Scan a directory
codediet .

# Scan a specific file
codediet path/to/file.py

# JSON output
codediet . --json
```

### Text Output

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

### JSON Output

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

No scores. No percentages. No rankings. No suggestions. CodeDiet reports
observations, never judgments — the developer decides what to do.

### Programmatic Library API

CodeDiet can be imported and used directly inside other Python codebases:

```python
from codediet import scan, Finding
from codediet.models import FindingClass

# Scan a project folder or a single file
findings = scan("/path/to/other/project")

# Separate facts from review recommendations
facts = [f for f in findings if f.classification == FindingClass.FACT]
reviews = [f for f in findings if f.classification == FindingClass.REVIEW]

# Inspect a finding
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

## Design Principles

- **Trust over feature count.** A tool that's wrong even occasionally gets
  uninstalled and not reconsidered. CodeDiet aggressively avoids false
  positives — it would rather miss a real wrapper than flag something that
  isn't one.
- **Deterministic.** No LLMs, no embeddings, no AI scoring. Every finding is
  mechanically reproducible from the AST.
- **Honest about uncertainty.** The Fact/Review distinction is a user-facing
  contract, not an internal note. Users can always tell whether a finding is a
  structural certainty or a "go look at this."
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

# Build
uv build
```

## License

MIT
