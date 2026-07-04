# CLAUDE.md — CodeDiet Project Guide (v0.3)

This file is the source of truth for working on CodeDiet. Read it fully
before writing or modifying any code. This is a complete replacement of the
v0.2 guide, not a patch — v0.2 is preserved at `CLAUDE.v0.2.archive.md` for
history, but is no longer authoritative. If a request conflicts with this
document, flag the conflict explicitly rather than silently resolving it in
either direction.

**What changed in v0.3, in one sentence:** no new detectors, no new
languages, no new ambition — v0.3 makes the existing findings easier to
*act on* by writing them to a shareable file and assembling a plain-text
prompt the user can hand to their own coding LLM. Everything else from v0.2
carries forward unchanged. See §0 for why this scope was chosen over the
broader "think big" direction that was briefly considered and deliberately
rejected.

---

## 0. Why v0.3 Is Scoped This Way

Before this version was planned, a much bigger direction was on the table:
new detectors, a second language, new platforms — "think big, catch a large
number of users." That direction was deliberately rejected, not because
ambition is bad, but because of a basic sequencing problem: v0.2 *documented*
five new detectors and shipped *none* of them. Adding more ambition on top of
an undelivered roadmap would have repeated the exact mistake the original
project planning (the old MLForge 12-feature draft) was rejected for in the
first place.

So v0.3 deliberately does not add detectors, languages, or scoring. Instead
it answers a narrower, real question: **the findings CodeDiet already
produces are good, but they currently live only in a terminal scroll-back or
a JSON blob — how does a developer actually *use* them?** Most developers
working with AI coding assistants are going to act on findings by handing
them back to that same assistant. v0.3 makes that handoff easy and exact,
without CodeDiet ever touching an LLM itself.

This is "user-friendly" growth, not "feature count" growth — it increases
how usable the existing, validated detector is, rather than increasing how
much CodeDiet claims to detect.

---

## 1. Mission (unchanged from v0.2)

CodeDiet detects unnecessary code growth commonly introduced by AI-assisted
development — duplicate code, abandoned implementations, helper/utility
explosion, pass-through wrappers, and structurally similar modules. It does
not look for bugs, security issues, style, or type errors.

Tagline (unchanged): **"Put AI-generated code on a diet."**

---

## 2. Philosophy (unchanged, restated because it directly governs §5 below)

Four properties matter, in this order: **Trust, Precision, Explainability,
Evidence** — over recall, fancy metrics, or marketing claims.

Every finding is either a **Fact** (deterministic, mechanically defensible,
true by construction) or a **Review Recommendation** (a heuristic signal,
explicitly not a claim about the outcome of inspection). This distinction is
not just a CLI display detail — as of v0.3, it must also survive intact into
every exported file and every generated LLM prompt. See §5.3. This is the
part of v0.3 most likely to be gotten wrong by accident, so it gets repeated
here deliberately.

---

## 3. Product Positioning (unchanged from v0.2)

CodeDiet remains:
- Read-only, static analysis only
- Deterministic where a finding is labeled Fact; explicitly heuristic where
  labeled Review
- Free of LLMs, embeddings, AI scoring, and any probabilistic/generative
  component **inside CodeDiet itself**

### CodeDiet is NOT
- An AI code reviewer
- An auto-refactoring tool
- A dead-code removal tool
- A clone/duplicate *remover* (it finds candidates; it removes nothing)
- A code quality scoring system
- An LLM wrapper of any kind
- An agentic tool that takes action on your behalf

### CodeDiet IS
- A structural diagnostics tool
- A static analysis tool
- An AI-era code-bloat detector
- A read-only CLI

### Absolute invariants (apply to every detector, every version, no exceptions)
- **Never modifies source code.** Read-only, always.
- **Never generates fixes, diffs, or patches.**
- **Never suggests deletion.** Not "delete this," not "safe to remove," not
  "this is unnecessary." CodeDiet identifies; the developer decides.
- **Never uses LLMs, embeddings, or any probabilistic/generative model.**
  Every finding must be reproducible deterministically from static analysis
  of the code alone — same input, same output, every time, on any machine.
- **Never produces a composite score.** No "Bloat Score," no "Maintainability
  Score," no percentage, no 0–100 risk number, no letter grade. This is
  permanent.
- **Never takes autonomous action.** No agentic workflows, no auto-fixes.

### A clarification made necessary by v0.3's new feature

v0.3 introduces a feature that *generates a prompt for the user's own LLM*.
This does **not** weaken the "no LLM dependency" invariant, and the
distinction must be preserved precisely in both code and documentation:

- CodeDiet does not call any LLM API, locally or remotely, at any point.
- CodeDiet does not use embeddings, completions, or any model inference to
  produce findings, the exported file, or the prompt text.
- The generated prompt is plain, deterministic, templated text — built
  entirely from CodeDiet's own structured findings (§4's data model) —
  that the *user* chooses to paste into whatever tool they already use
  (Claude Code, Cursor, Copilot Chat, ChatGPT, etc.).
- CodeDiet has no knowledge of, dependency on, or integration with any
  specific LLM provider. The prompt is provider-agnostic by design — it must
  read correctly whether pasted into Claude, GPT, Gemini, or anything else.

If a future contributor proposes calling an LLM API directly from CodeDiet
("just to make the prompt better" or "just to summarize findings"), that is
a violation of a permanent invariant, not a minor implementation choice —
treat it the same as a proposal to add a composite bloat score.

---

## 4. Architecture

### Parser: tree-sitter (NOT stdlib `ast`)

Unchanged from v0.1 and v0.2. Tree-sitter was chosen over stdlib `ast`
specifically so detection rules could eventually port to JS/TS/Go grammars
with a fraction of the rewrite cost. Do not reconsider stdlib `ast` — this
has already been decided and re-confirmed across multiple versions.

Packages: `tree-sitter`, `tree-sitter-python`.

### Repository structure (v0.3)

```text
codediet/
├── codediet/
│   ├── __init__.py          # Package root; exports scan and Finding
│   ├── api.py               # Programmatic scan() API
│   ├── cli.py               # Typer CLI — codediet doctor <path> [options]
│   ├── parser.py            # tree-sitter setup, file walking, tree building
│   ├── reporter.py          # Terminal text & JSON output (Facts / Reviews)
│   ├── models.py            # FindingClass enum + Finding dataclass
│   ├── exporter.py          # NEW (v0.3) — writes findings to .md / .txt
│   ├── prompt_builder.py    # NEW (v0.3) — assembles LLM hand-off prompt
│   └── detectors/
│       ├── __init__.py
│       └── wrappers.py      # Wrapper function detector (only shipped detector)
│
├── tests/
│   ├── test_api.py          # Programmatic API integration tests
│   ├── test_cli.py          # CLI integration tests (text, JSON, --export, --prompt)
│   ├── test_exporter.py     # NEW (v0.3) — exporter module tests
│   ├── test_prompt_builder.py  # NEW (v0.3) — prompt safety invariant tests
│   ├── test_reporter.py     # Reporter tests (FACTS / REVIEW RECOMMENDATIONS)
│   └── test_wrappers.py     # 40+ detector tests (positive + near-miss negatives)
│
├── examples/
│   ├── obvious_wrappers.py  # 5 clear-cut wrappers (positive examples)
│   ├── tricky_non_wrappers.py  # Near-misses that must NOT be flagged
│   └── mixed_realistic.py   # Realistic mix for manual testing
│
├── README.md
├── CLAUDE.md                # ← this file (authoritative spec, v0.3)
├── CLAUDE.v0.1.archive.md   # Historical reference only, not authoritative
├── CLAUDE.v0.2.archive.md   # Historical reference only, not authoritative
├── pyproject.toml
└── LICENSE
```

`exporter.py` and `prompt_builder.py` are deliberately separate modules, not
one combined "export" feature, because they have different jobs and different
risk profiles: `exporter.py` is a pure data-formatting concern (low risk,
same rigor as `reporter.py`); `prompt_builder.py` is the one place in the
codebase where wording precision is directly load-bearing for the trust model
(see §5.3), and keeping it isolated makes it easy to review in isolation.

### Data model

```python
from dataclasses import dataclass
from enum import Enum

class FindingClass(Enum):
    FACT = "fact"    # deterministic, mechanically defensible
    REVIEW = "review" # heuristic signal, explicitly not a claim

@dataclass
class Finding:
    detector: str          # e.g. "wrapper", "duplicate_helper"
    classification: FindingClass
    file: str
    line: int
    message: str           # must match wording rules in §6 for the detector
    evidence: dict         # structured, detector-specific supporting data
                           # wrapper: {"function": "parse_float", "target": "float"}
                           # duplicate_helper: {"cluster": ["safe_float", "parse_float"]}
```

Every detector returns `list[Finding]`. The reporter, exporter, and
prompt_builder are the only things that format output — detectors never
format their own strings beyond populating `message` and `evidence`.

### Stack

- Python 3.12+
- CLI: Typer
- Parsing: tree-sitter + tree-sitter-python
- Testing: pytest
- Linting: Ruff
- Packaging: uv / hatchling
- No database, no web server, no frontend, no LLM dependencies, no embeddings

### Public programmatic API

```python
from codediet import scan, Finding
from codediet.models import FindingClass

findings = scan("/path/to/project")
facts = [f for f in findings if f.classification == FindingClass.FACT]
```

`scan()` and `Finding` are re-exported from `codediet/__init__.py`.

---

## 5. CLI & Output Contract

### The CLI command

```bash
codediet doctor <path>                    # text output
codediet doctor <path> --json             # JSON output
codediet doctor <path> --export out.md   # text + write Markdown findings file
codediet doctor <path> --export out.txt  # text + write plain-text findings file
codediet doctor <path> --export out.md --prompt  # + append LLM hand-off prompt
```

**Important:** the CLI command is `codediet doctor <path>`, not
`codediet <path>`. `doctor` is the Typer subcommand. Running `codediet .`
directly will fail with "No such command '.'".

### Terminal text output format

```
Files scanned: 42

FACTS — Mechanically Verifiable (3 found)

  [WRAPPER]
    utils.py:18
    parse_float -> float

  [WRAPPER]
    helpers.py:44
    file_exists -> os.path.exists

REVIEW RECOMMENDATIONS — Heuristic Signals (0 found)
  (none)
```

### JSON output format (`--json`)

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

No scores. No percentages. No rankings. No suggestions in any output — ever.

---

## 6. New in v0.3: Findings Export & LLM Hand-off Prompt

### 6.1 `--export` flag

```bash
codediet doctor . --export findings.md
```

Writes a Markdown file containing every finding from the run, grouped by
classification (Fact / Review), with file:line references identical to
terminal output. If no findings exist, the file still gets written, stating
plainly that no findings were detected — never silently skip the file, since
an empty result is itself useful information (a clean run is worth confirming
in writing, e.g. for a PR comment or changelog).

Plain text mode (`--export findings.txt`) produces the same content without
Markdown formatting, for users piping into other tooling.

### 6.2 Export file structure

```markdown
# CodeDiet Findings — <repo name or path>
Generated: <ISO timestamp>
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

Notes on this structure:
- Facts and Review Recommendations are **always** rendered as separate
  sections, never merged into one flat list — this mirrors the terminal/JSON
  separation and is non-negotiable.
- The summary counts are descriptive only. No score, no percentage.
- If a Review section has no findings, say so explicitly ("None in this
  run") rather than omitting the section.

### 6.3 `--prompt` flag

```bash
codediet doctor . --export findings.md --prompt
```

Adds a final section to the same export file: a single, ready-to-copy prompt
intended for the user's own LLM-based coding assistant, built only from the
findings already present in the file. `--prompt` has no effect without
`--export` — there is no reason to generate a hand-off prompt the user can't
also see the underlying evidence for.

### 6.4 The generated prompt — the part that needs the most care

This is the highest-risk addition in v0.3, not because it's technically
hard, but because a poorly worded prompt could cause an LLM to treat a
Review-class finding as a confirmed problem and "fix" something CodeDiet
never claimed was broken. The prompt template must structurally prevent
this.

**Required properties of the prompt template (enforced by tests):**

- It must explicitly state that CodeDiet performed read-only static analysis
  and made no changes, and that the findings are a mix of structural facts
  and heuristic review flags — and it must say which is which for every
  single item.
- Facts and Review Recommendations must be in visually distinct sections in
  the prompt. Never flatten them into one combined list.
- For Fact-class findings, the prompt may ask the LLM to take direct action
  (e.g., "consider whether it can be inlined or removed").
- For Review-class findings, the prompt must ask the LLM to *investigate and
  report back*, not to act. The difference between "review and report" and
  "go ahead and fix" is the entire safety mechanism here.
- The prompt must never use the words "duplicate," "dead," "unused,"
  "unsafe," or "delete" for any Review-class finding — only the exact
  sanctioned wording from each detector's spec (e.g., "Review Cluster,"
  "Potentially Superseded Implementation," "Possibly Unused Function").
- The prompt must close by asking the LLM to summarize what it would change
  and why, *before* making changes.
- The prompt must contain no provider-specific syntax (no @mentions, no
  slash commands) — it must work verbatim in Claude, GPT, Gemini, or any
  other tool.

**Example shape:**

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
- helpers.py:5 — Review Cluster: `safe_float`, `parse_float`, `ensure_float`
  share a naming pattern and overlapping signatures. Please review whether
  they are genuinely redundant before proposing any change.

For FACTS, you may propose a direct fix (for example, inlining a pure
pass-through wrapper) if it is appropriate for the context.

For REVIEW RECOMMENDATIONS, please investigate first and report back what
you find — do not modify code based on these signals alone.

Please summarize your proposed plan before making any edits.
```

This template lives in `prompt_builder.py`. Tests in `test_prompt_builder.py`
mechanically assert that no Review-class finding's rendered text ever contains
action-implying verbs — this is the backstop against the highest-consequence
failure mode in this feature.

### 6.5 What this feature explicitly does NOT do

- It does not call any LLM. Ever.
- It does not choose or assume which LLM/tool the user is using.
- It does not track whether the user actually used the prompt, or any outcome.
- It does not change detection logic, reliability tiers, or default-on/off
  behavior for any detector.

---

## 7. Detector Specifications

Each detector states its purpose, reliability level, false-positive risk,
and whether its output is a **Fact** or a **Review Recommendation**.

### 7.1 Wrapper Detection
**Status:** Shipped (v0.1), carried forward unchanged.
**Reliability:** High.
**False positive risk:** Near zero — this is a pure structural AST check.
**Output class:** Fact.

Detects functions whose entire body is a single pass-through call to another
function or builtin, with arguments forwarded unchanged and no added logic,
branching, transformation, or side effects.

```python
def parse_float(x):
    return float(x)
```

Detection requirements (all must hold — if any ambiguity, do NOT flag):
- Function body contains **exactly one statement**
- That statement is a `Return`
- The return value is a `Call` with a simple target (identifier or attribute
  chain — no method chains, no subscripts)
- Arguments are forwarded unchanged (same names, same order, or clean
  `*args`/`**kwargs` passthrough)
- No branching, no transformations, no side effects anywhere in the body

This detector's job is to remain the proof that a CodeDiet finding can be a
Fact. Its standards must not be loosened to catch more cases.

### 7.2 Duplicate Helper Detection
**Status:** Roadmap (not implemented — see §8 for what v0.3 ships).
**Reliability:** Medium.
**False positive risk:** Real and expected — output is permanently constrained
to review language.
**Output class:** Review Recommendation, always. Must never graduate to
Fact-level claims.

Goal: find functions with similar names, similar signatures, and similar
implementation structure.

```python
safe_float()
parse_float()
ensure_float()
```

Output wording: **"Review Cluster"** — never "duplicate," never "these do the
same thing."

### 7.3 Abandoned Implementation Detection
**Status:** Roadmap.
**Reliability:** Medium.
**False positive risk:** Moderate.
**Output class:** Review Recommendation, always.

Goal: detect likely-superseded implementations left behind after iterative
AI-assisted development.

```python
search()
search_v2()
search_new()
search_final()
```

Output wording: **"Potentially Superseded Implementation"** — never "delete
the old one," never "this is dead."

### 7.4 Dead Function Detection
**Status:** Roadmap. Must ship default-OFF (opt-in flag).
**Reliability:** Medium.
**False positive risk:** High without mitigation (framework decorators,
dynamic dispatch, pytest fixtures, DI patterns).
**Output class:** Review Recommendation, always.

Output wording: **"Possibly Unused Function"** — never **"Safe to delete."**
That exact phrase is permanently forbidden.

### 7.5 Similar Module Detection
**Status:** Roadmap.
**Reliability:** Medium-Low.
**False positive risk:** Significant.
**Output class:** Review Recommendation, always.

Output wording: **"Review Similar Modules."**

### 7.6 Utility Explosion Detection
**Status:** Roadmap.
**Reliability:** Low (documented to users explicitly as lowest-confidence).
**False positive risk:** High in absolute terms.
**Output class:** Review Recommendation, always.

Output wording: **"Review Utility Growth."**

---

## 8. Reliability Model

| Detector | Reliability | Output Class |
|---|---|---|
| Wrapper Detection | High | Fact |
| Duplicate Helper Detection | Medium | Review |
| Abandoned Implementation Detection | Medium | Review |
| Dead Function Detection | Medium (high FP risk without mitigation) | Review |
| Similar Module Detection | Medium-Low | Review |
| Utility Explosion Detection | Low | Review |

Two permanent rules:

1. **A detector's reliability tier is a property of the underlying technique,
   not of implementation effort.** You cannot raise "Duplicate Helper
   Detection" from Medium to High by writing better code.
2. **Output class tracks reliability, not ambition.** Nothing below "High"
   reliability is permitted to produce Fact-class output, ever.

---

## 9. Roadmap

### What v0.3 ships in code
- Wrapper Detection (§7.1) — unchanged, carried forward from v0.1/v0.2
- `exporter.py` — writes Markdown/text findings file via `--export`
- `prompt_builder.py` — assembles LLM hand-off prompt via `--prompt`
- Tests: `test_exporter.py` and `test_prompt_builder.py` (including mechanical
  safety-invariant tests on prompt wording, per §6.4)

### What v0.3 documents but does NOT implement
Sections 7.2 through 7.6 in full. These are real, considered designs — not
placeholders — but implementing them is future work, one detector at a time,
each validated against real repositories for false-positive rate before
being considered done.

### Suggested implementation order for future versions
1. Duplicate Helper Detection (name/signature pattern matching — most contained)
2. Abandoned Implementation Detection (similar implementation complexity)
3. Similar Module Detection (requires file-level structural comparison)
4. Utility Explosion Detection (project-level heuristic, needs calibration)
5. Dead Function Detection (highest complexity + highest FP risk; ship last,
   default-OFF)

The "think big" direction considered before v0.3 — multi-language support,
CI/GitHub Action delivery, broader distribution — remains a reasonable future
direction, but only once at least one more detector ships from the roadmap
above and the export/prompt workflow proves genuinely useful in practice.

---

## 10. Development Rules

All v0.2 rules carry forward:
- **One detector at a time.** Each new detector is validated against real,
  popular open-source repositories for false-positive rate before being
  considered shippable — hand-written test fixtures alone are not sufficient.
- **Negative test cases are mandatory.** For every detector, write deliberate
  near-miss tests that confirm the detector does *not* fire.
- **Output wording is reviewed against §7 on every change.** "Safe to
  delete," "this is unnecessary," "duplicate," and similar certainty-implying
  language are bugs, not style preferences, when attached to a Review-class
  detector.
- **No detector ships enabled by default unless its reliability tier is
  High.** Currently only Wrapper Detection.
- **Resist scope creep explicitly.**

**New for v0.3:** any change to `prompt_builder.py` requires re-reading §6.4
in full before merging. This is the one file in the project where wording
choices have a direct, mechanical path to causing an LLM to take an
unwarranted action on a user's codebase. Treat changes here with the same
scrutiny as changes to detector logic itself, not as copywriting.

---

## 11. Success Criteria

v0.3 is successful if:

- `codediet doctor <path>` continues to work exactly as in v0.2, with no
  regression in detection precision.
- `--export` produces a clean, accurate Markdown/text file matching §6.2,
  with Facts and Review Recommendations always visually separated.
- `--prompt` produces a prompt that a developer could paste into any major
  LLM coding assistant and get a sensible, safe response — one that
  investigates Review-class findings rather than blindly acting on them.
- `test_prompt_builder.py` mechanically verifies no action-implying language
  appears attached to any Review-class finding in the generated prompt.
- Nothing about detection logic, reliability tiers, or default-on/off
  behavior changed from v0.2 — v0.3 is purely a usability layer.
- The project has not quietly become an "LLM integration" in positioning or
  in code, despite now producing LLM-facing output.
- All 105+ tests pass: `uv run pytest tests/ -v`

Trust, precision, explainability, and evidence — in that order — remain the
measure of whether this project is working, not feature count.
