# CLAUDE.md — CodeDiet Project Guide

This file is the source of truth for working on CodeDiet. Read it fully before
writing or modifying any code. If a request conflicts with this document, flag
the conflict explicitly rather than silently resolving it in either direction —
several decisions here were made after deliberately reversing earlier ones, so
"it seemed reasonable" is not sufficient justification to deviate.

---

## 1. What CodeDiet Is

CodeDiet is a read-only static analysis CLI that detects unnecessary code
growth caused by AI coding assistants (Cursor, Claude Code, Copilot, Windsurf,
ChatGPT). It answers one question: **"does this code exist but probably not
need to?"**

It does not look for bugs, security issues, style violations, performance
problems, or dead code. Other tools already do those well (Ruff, Pylint,
Vulture, Semgrep). CodeDiet's niche is structural bloat that is syntactically
valid, passes tests, and is invisible in normal code review.

Tagline: **"Put AI-generated code on a diet."**

### What CodeDiet is NOT (do not build toward these in v0.1)
- Not an AI code reviewer
- Not an auto-refactoring tool
- Not a dead-code removal tool
- Not a clone/duplicate detector
- Not a code quality scoring system
- Not an LLM wrapper of any kind

### Absolute invariants (apply to every version, not just v0.1)
- **CodeDiet never modifies source code.** Read-only, always.
- **CodeDiet never generates fixes or suggests deletions.** It reports facts.
- **CodeDiet never uses LLMs, embeddings, AI scoring, or probabilistic
  analysis.** Every finding must be deterministic and mechanically reproducible
  from the AST alone.
- **No composite scores, percentages, rankings, or risk values, ever.** This is
  a deliberate, permanent differentiator from competing tools (see §6). A
  "Bloat Score: 57" is exactly the kind of output this project exists to NOT
  produce. Don't add one even if it seems like it would help marketing.
- **Findings are phrased as observations, never judgments.** "Wrapper function
  detected" — never "delete this," never "this is bad code," never "this is
  unnecessary." The developer decides what to do; CodeDiet only points.

---

## 2. v0.1 Scope (Locked)

v0.1 ships **exactly one detector: Wrapper Detection.**

This is intentional, not a placeholder. Earlier planning considered shipping
three detectors (wrapper, name-cluster duplication, dead-code) with dead-code
gated behind a flag. That plan was superseded — v0.1 ships one detector only,
because wrapper detection is the only one of the three with near-zero false
positive risk *by construction* (it's a pure structural/geometric AST check,
not a heuristic). The other two are real, validated ideas for later versions,
not cut features — see §7.

### Wrapper Detection — exact definition

Detect functions whose entire body is a single pass-through call to another
function or builtin, forwarding arguments unchanged, with no added logic.

```python
def parse_float(x):
    return float(x)

def process_number(x):
    return helper(x)
```

Detection requirements (all must hold for a finding to fire):
- Function body contains **exactly one statement**
- That statement is a `Return`
- The return value is a `Call`
- Arguments to the call are forwarded unchanged (same identifiers, same order,
  or clean `*args`/`**kwargs` passthrough — no reordering, no transformation)
- No branching, no transformations, no side effects anywhere in the body

If there is any ambiguity about whether a case qualifies, **do not flag it.**
False negatives are the acceptable failure mode here; false positives are not.
This is the single most important engineering principle for this detector —
re-read §6 on why before loosening any of these conditions.

The detector must not attempt to guess developer intent ("this function seems
pointless"). It only reports the structural fact that a pass-through shape
exists. Naming the function differently from its target, adding a docstring,
or adding a type hint does not exempt it from detection — those are surface
details, not added logic.

---

## 3. Architecture & Tech Stack

### Parser: tree-sitter (NOT stdlib `ast`)

This was decided explicitly, twice, after being reconsidered. The original
plan was stdlib `ast` for v0.1 (simpler, zero dependencies, "good enough for
one Python-only detector"). This was deliberately overridden in favor of
tree-sitter, accepting the extra setup cost now, because:
- Tree-sitter's AST shape is language-agnostic, so the wrapper-detection rule
  can be ported to JS/TS/Go grammars later with much less rewrite work.
- This project's stated long-term roadmap includes multi-language support, and
  that decision should shape the parsing layer from day one rather than
  requiring a rewrite later.

**Do not swap this back to stdlib `ast`** without an explicit instruction to do
so — this has already been decided twice in this project's history.

Packages: `tree-sitter`, `tree-sitter-python` (both confirmed installable via
pip; `tree-sitter-python` provides the prebuilt language grammar, no manual
grammar compilation needed).

Keep the tree-walking logic in `detectors/wrappers.py` as decoupled as
reasonably possible from Python-specific tree-sitter node *types* — e.g.,
prefer checking node shape (statement count, statement kind) over relying on
Python-grammar-specific quirks where an equivalent concept exists in other
grammars. Don't over-engineer an abstraction layer for languages that don't
exist yet, but don't make decisions that would be needlessly painful to port.

### Repository structure

```text
codediet/
├── codediet/
│   ├── cli.py              # Typer entrypoint, `codediet doctor <path>`
│   ├── parser.py           # tree-sitter setup, file walking, tree building
│   ├── reporter.py         # formats Finding list -> terminal text or JSON
│   ├── models.py           # Finding dataclass
│   └── detectors/
│       ├── __init__.py
│       └── wrappers.py     # the one detector
│
├── tests/
├── examples/                # small real-ish .py files for manual testing
├── README.md
├── pyproject.toml
└── LICENSE
```

### Data model

```python
from dataclasses import dataclass

@dataclass
class Finding:
    kind: str       # "wrapper" for v0.1; field exists for future detector kinds
    file: str
    line: int
    message: str
    # consider: function name and target name as structured fields, not just
    # baked into `message` — the JSON output example in the spec shows
    # "function" and "target" as separate keys, so the dataclass should
    # probably carry those explicitly rather than just a flat message string.
    # Resolve this in implementation; structured fields are preferable to
    # string-only output since --json mode needs the real fields anyway.
```

Every detector returns `list[Finding]`. The reporter is the only thing that
knows how to render findings — detectors don't format output themselves.

### Stack

- Python 3.12+
- CLI: Typer
- Parsing: tree-sitter + tree-sitter-python
- Testing: pytest
- Formatting/linting: Ruff (the irony of using a linter to build an
  anti-bloat tool is fine — Ruff checks different things than CodeDiet does)
- Packaging: uv

No database. No web server. No frontend. No LLM dependencies. No embeddings.

---

## 4. CLI & Output Contract

```bash
codediet doctor .
```

```text
Files scanned: 42

Wrapper Functions Found: 3

WRAPPER
utils.py:18
parse_float -> float

WRAPPER
helpers.py:44
process_number -> helper
```

```bash
codediet doctor . --json
```

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

No scores. No percentages. No rankings. No risk values. No generated
commentary or suggestions in the output — ever. If you find yourself adding a
sentence like "consider removing this," delete it. That's a judgment call
CodeDiet explicitly does not make.

---

## 5. Why This Project Exists (context for any copy/docs you write)

Background research (see project history / uploaded research report)
established real empirical grounding for this, not just anecdote:

- AI-generated code now accounts for a large share of new commits in
  AI-heavy repositories, and code churn (code rewritten/reverted within two
  weeks) has risen substantially since AI adoption accelerated.
- For the first time on record, duplicated/copy-pasted code volume has
  exceeded refactored/moved code volume — the "path of least resistance" for
  an LLM is additive, not corrective. It layers new wrapper/helper functions
  over existing logic rather than reorganizing it.
- A large-scale study of verified AI-authored commits found code smells were
  by far the most common category of introduced technical debt, and roughly
  a quarter of these issues survive unnoticed into the latest version of the
  repo — they don't break anything, so they pass review.
- The specific anti-pattern CodeDiet v0.1 targets (a function that does
  nothing but forward a call) is a long-recognized smell ("Middle Man"), not
  a new invention — LLMs simply produce it at much higher volume because they
  operate on localized prompts without awareness of existing utilities
  elsewhere in the codebase.

This grounding is useful for the README and launch copy: lean on "this is an
established code smell, AI just produces it at unprecedented scale" rather
than implying CodeDiet invented the concept.

---

## 6. Non-Negotiable Design Principles

**Trust over feature count.** This is the single most important strategic
decision behind this project, and it should override the instinct to add
"one more useful check" at every stage. The competitive and research analysis
behind this project found:

- The leading dead-code detector for Python (Vulture) produces roughly 14
  false positives for every genuine finding when run against real popular
  repositories (Flask, FastAPI), almost entirely from framework
  decorators/dynamic dispatch it can't see statically. This is *the*
  cautionary data point for this whole project: a mature, well-regarded tool
  in an adjacent category still drowns users in noise.
- Developer trust in static analysis tools is asymmetric: a tool that's
  right is appreciated, but a tool that's wrong even occasionally tends to
  get uninstalled and not reconsidered. There is little room for "we'll fix
  the false positive rate in v0.2" — by then, the user is gone.
- A real existing competitor (an AST-based "AI slop detector") already
  occupies adjacent territory but uses composite risk scoring with inputs
  like "jargon inflation." CodeDiet's refusal to do this is a genuine,
  citable point of differentiation, not just a stylistic choice — keep
  emphasizing it in docs/positioning.

**Practical implication for implementation:** when in doubt during
implementation of the wrapper detector, narrow the detection conditions
rather than broaden them. It is always safer to miss a real wrapper function
than to flag something that isn't one.

---

## 7. Explicitly Deferred (do not build now, but don't discard either)

These were seriously considered and are likely future versions, not rejected
ideas — context is preserved here so future work doesn't have to re-litigate
them from scratch:

- **Name-cluster review flags** — group functions sharing AI-typical naming
  patterns (`safe_*`, `validate_*`, `ensure_*`, `parse_*`, `*_helper`,
  `*_util`) with overlapping signatures, surfaced as "worth a manual look,"
  never asserted as definitive duplicates. Validated as a reasonable
  heuristic in research, specifically *because* of the hedged framing — if
  this is built later, preserve that hedging exactly, don't let it drift
  toward "these are duplicates."
- **Dead-function detection** — deferred specifically because of the Vulture
  false-positive data above. If built later, it must ship default-OFF
  (opt-in via flag), with BFS reachability from configurable entry points
  (`__main__.py`, `app.py`, package `__init__.py`) as the core mechanism
  rather than trying to resolve individual dynamic dispatch calls, plus
  pre-baked exclusion rules for at minimum Flask, FastAPI/Pydantic, Django,
  and pytest — these were identified as the worst false-positive sources for
  existing tools in this category.
- **Semantic/embedding-based similarity** — explicitly rejected for any
  near-term version, not just v0.1. Heavy, non-deterministic, contradicts
  the project's core trust positioning.
- **Multi-language support (JS/TS/Go)** — the reason tree-sitter was chosen
  over stdlib `ast` despite v0.1 only needing Python. Don't build the
  grammars now; just don't make decisions that foreclose it later.
- **`--fix` / auto-remediation** — explicitly out of scope for the
  foreseeable future. The read-only posture is core to the trust story, not
  an MVP limitation. If this is ever revisited, it should only happen long
  after the detection logic has an established track record (the Ruff
  trajectory — prove the linter first, expand later — was cited as the
  model to follow, not a near-term plan).
- **Git history / diff tracking across commits, CI integration, composite
  scoring of any kind** — all out of scope, no current timeline.

---

## 8. Working Conventions for This Repo

- Validate the wrapper detector against real, popular open-source Python
  repos before considering v0.1 "done" — the plan has always been to check
  for false positives against real code, not just hand-written test fixtures,
  before any public launch.
- Write tests that include deliberately tricky near-misses (a function with a
  pass-through call *plus* a single logging statement; a function forwarding
  args in a different order; a function with a default-value transformation)
  to confirm the detector correctly does NOT flag these. Negative test cases
  matter as much as positive ones for this project.
- Keep commit/PR scope narrow and aligned with whichever section of this
  document is being worked on. This project's core risk is scope creep
  undermining the trust story — resist adding "just one more small check"
  without it being a deliberate, discussed decision.
