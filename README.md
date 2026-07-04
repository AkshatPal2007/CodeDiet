# CodeDiet 🥗

**Put AI-generated code on a diet.**

[![PyPI version](https://img.shields.io/pypi/v/codediet)](https://pypi.org/project/codediet/)
[![Python 3.12+](https://img.shields.io/pypi/pyversions/codediet)](https://pypi.org/project/codediet/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/AkshatPal2007/CodeDiet/actions/workflows/ci.yml/badge.svg)](https://github.com/AkshatPal2007/CodeDiet/actions/workflows/ci.yml)

CodeDiet is a read-only static analysis CLI that detects structural bloat introduced by AI coding assistants (Cursor, Claude Code, Copilot, Windsurf, ChatGPT). It answers one question: *"does this code exist but probably not need to?"*

It does not look for bugs, security issues, style violations, performance problems, or dead code. Other tools already do those well (Ruff, Pylint, Vulture, Semgrep). CodeDiet's territory is narrower and currently underserved: **structural bloat that is syntactically valid, passes every test, and is invisible in a normal code review.**

---

## 📖 Table of Contents
- [🚀 Quick Start](#-quick-start)
- [🤔 Why This Exists](#-why-this-exists)
- [🎯 What It Detects](#-what-it-detects)
- [🌐 Supported Languages](#-supported-languages)
- [⚠️ Limitations](#️-limitations)
- [💻 Usage](#-usage)
- [🧩 Programmatic API](#-programmatic-api)
- [⚖️ Design Principles](#️-design-principles)
- [🛠️ Development & Contributing](#️-development--contributing)

---

## 🚀 Quick Start

Requires Python 3.12+.

Install globally as a standalone command-line tool (recommended):
```bash
uv tool install codediet
# or
pipx install codediet
```

Or install in your project environment:
```bash
pip install codediet
```

**Run a scan:**
```bash
# Scan current directory
codediet doctor .

# Output findings as a Markdown file with a ready-to-copy prompt for your LLM
codediet doctor . --export findings.md --prompt
```

---

## 🤔 Why This Exists

AI-generated code now accounts for a significant share of new commits in AI-heavy repositories — and with it, code churn has risen substantially. For the first time on record, duplicated/copy-pasted code volume has exceeded refactored/moved code volume. The "path of least resistance" for an LLM is additive, not corrective: it layers new wrapper/helper functions over existing logic rather than reorganizing it.

Duplicate helpers, abandoned `_v2`/`_final` implementations, sprawling `utils.py` files, pass-through wrapper functions — these don't break tests, pass code review, and accumulate silently until the codebase becomes genuinely hard to navigate.

---

## 🎯 What It Detects

CodeDiet separates findings into two categories — the distinction is always visible in output and is a core part of the tool's honesty model:

- **Facts** — mechanically verifiable structural claims. True by construction; no interpretation required.
- **Review Recommendations** — heuristic signals worth a human look, with no claim about what inspection will find.

### Shipped (v0.4)

**Wrapper Functions** *(Fact)* — functions whose entire body is a single pass-through call to another function, forwarding arguments unchanged with no added logic:

```python
# CodeDiet flags these as Facts — structurally confirmed
def parse_float(x):
    return float(x)

def file_exists(path):
    return os.path.exists(path)

def send(self, payload):
    return self._http.post(payload)
```

Detection is deterministic and mechanical — no AI, no heuristics, no probabilistic scoring. Every fact-class finding is reproducible from the AST.

**Abandoned Implementation Detection** *(Review)* — functions whose names suggest they are versioned replacements of an earlier implementation left behind after iterative AI-assisted development:

```python
def search(query):        # original
    ...

def search_v2(query):     # ← flagged: Potentially Superseded Implementation
    ...

def search_final(query):  # ← flagged: Potentially Superseded Implementation
    ...
```

Only fires when the presumed original function also exists in the same file. Standalone `search_v2` with no `search` present is never flagged.

Supported suffixes: `_v2`, `_v3`, `_vN`, `_new`, `_final`, `_old`, `_temp`, `_backup`, `_deprecated`, `_legacy`, `_orig`, `_original`, `_revised`, `_refactored`, and more.

**Utility Explosion Detection** *(Review)* — projects that have accumulated three or more utility-named modules (`utils.py`, `helpers.py`, `common.py`, `shared.py`, `misc.py`, etc.):

```
Review Utility Growth — Project has 4 utility-named modules
  src/utils.py
  src/helpers.py
  core/common.py
  api/misc.py
```

A single `utils.py` is unremarkable; three or more is a heuristic signal that helper code is accumulating without structure.

### Roadmap (specified, not yet implemented)

- **Duplicate Helper Detection** *(Review)* — functions with similar names, signatures, and structure (`safe_float`, `parse_float`, `ensure_float`). Implementation exists; deferred to v0.5 pending improved cross-directory exclusion to reach an acceptable false-positive rate on real repositories.
- **Similar Module Detection** *(Review)* — files with unusually high structural overlap. Deferred to v0.6+.
- **Dead Function Detection** *(Review)* — unreferenced functions. Highest false-positive risk (decorators, dynamic dispatch, pytest fixtures); requires an opt-in flag. Deferred.

*Roadmap detectors are fully designed with exact output wording and reliability tiers — not placeholders. The README will be updated as each ships.*

---

## 🌐 Supported Languages

Currently, **Python (3.12+)** is the only supported language.

CodeDiet is built on top of `tree-sitter` specifically so that the detection rules can be ported to other languages (like JavaScript, TypeScript, or Go) in the future without a complete rewrite. However, expanding to new languages is not currently on the immediate roadmap, as the focus remains on refining detection accuracy in Python first.

---

## ⚠️ Limitations

CodeDiet is strictly a structural bloat detector. It is important to know what it **does not** do:

- **No Semantic Analysis:** It does not check for bugs, type errors, or logic flaws.
- **No Style/Linting:** It does not enforce PEP8, naming conventions, or formatting (use Ruff or Pylint for this).
- **False Negatives > False Positives:** CodeDiet aggressively avoids false positives. It intentionally ignores near-wrapper edge cases (e.g., functions with default arguments, guards, or logging) to maintain absolute trust.
- **Read-Only:** It will never automatically delete, auto-fix, or refactor your code.

---

## 💻 Usage

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

# Exit with code 1 if FACT-class findings are detected (for CI pipelines)
codediet doctor . --error-on-facts
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

Writes a portable Markdown (or plain-text) findings file — always written even when there are no findings, because a clean run is itself useful information (e.g. for a PR comment or changelog entry):

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

Appends a ready-to-copy prompt to the export file — paste it directly into your own coding assistant (Claude Code, Cursor, Copilot Chat, ChatGPT, or any other tool). CodeDiet never calls an LLM itself; it just builds the prompt from its own findings so the handoff is exact and safe:

```text
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

No scores. No percentages. No rankings. No suggestions. CodeDiet reports observations, never judgments — the developer decides what to do.

---

## 🧩 Programmatic API

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

## ⚖️ Design Principles

- **Trust over feature count.** A tool that's wrong even occasionally gets uninstalled and not reconsidered. CodeDiet aggressively avoids false positives — it would rather miss a real wrapper than flag something that isn't one.
- **Deterministic.** No LLMs, no embeddings, no AI scoring. Every finding is mechanically reproducible from the AST alone.
- **Honest about uncertainty.** The Fact/Review distinction is a user-facing contract. Users always know whether a finding is a structural certainty or a "go look at this" signal.
- **Read-only.** CodeDiet never modifies source code, never generates fixes, never suggests deletions.
- **No composite scores.** No "Bloat Score: 57" — that's exactly the kind of output this project exists to NOT produce.
- **LLM-adjacent, not LLM-powered.** v0.3 generates prompts you can hand to your own AI assistant. CodeDiet itself uses zero LLM/embedding inference.

---

## 🛠️ Development & Contributing

We welcome contributions! If you're interested in implementing any of the roadmap detectors or improving the core engine, please check the issues and open a PR.

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

## 📜 License

[MIT](LICENSE)
