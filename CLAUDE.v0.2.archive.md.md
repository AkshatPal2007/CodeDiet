# CLAUDE.md — CodeDiet Project Guide (v0.2)

This file is the source of truth for working on CodeDiet. Read it fully before
writing or modifying any code. This is a complete replacement of the v0.1
guide, not a patch — the v0.1 document is preserved at
`CLAUDE.v0.1.archive.md` for historical context, but it is no longer
authoritative. If a request conflicts with this document, flag the conflict
explicitly rather than silently resolving it in either direction.

---

## 1. Mission

CodeDiet detects unnecessary code growth commonly introduced by AI-assisted
development.

It does not look for bugs, security issues, style violations, formatting,
linting, or type errors. Mature tools already do those well (Ruff, Pylint,
Semgrep, mypy). CodeDiet's territory is narrower and currently underserved:
structural bloat that is syntactically valid, passes every test, and is
invisible in a normal code review.

### What "bloat" means for this project

CodeDiet looks for:
- Duplicate code and duplicate helpers
- Abandoned / superseded implementations left in place
- Dead experiments
- Utility/helper-module explosion
- Pass-through wrapper functions
- Structurally similar modules

### Why v0.2 exists — the lesson from v0.1

v0.1 shipped a single detector: pass-through wrapper functions (the "Middle
Man" smell). It was validated and works as designed — high precision, low
false positives, exactly as intended.

Real-world testing surfaced a problem that has nothing to do with the
detector's *quality* and everything to do with its *coverage*: pass-through
wrappers are a relatively uncommon pattern in real AI-generated codebases.
The detector was correct but the category was too narrow to carry a product.
Most of what developers actually accumulate from AI-assisted development —
duplicate helpers, abandoned `_v2`/`_final` implementations, sprawling
`utils.py` files — wasn't being caught at all.

This is why CodeDiet is repositioning from "wrapper detection tool" to "AI
code bloat detection tool." Wrapper detection remains, fully intact, as the
proof that this approach can be done with high precision. The rest of v0.2 is
about extending the same precision discipline to the patterns that actually
show up at volume.

---

## 2. Philosophy

Four properties matter, in this order, and the order is not negotiable:

1. **Trust**
2. **Precision**
3. **Explainability**
4. **Evidence**

These are prioritized over recall, over impressive-sounding metrics, and over
marketing claims. A detector that finds fewer real issues but never cries
wolf is more valuable to this project than a detector that finds everything
but erodes confidence in the tool after the third false alarm.

### Why this ordering, specifically

Developer trust in static analysis tooling is asymmetric. A tool that is
right is appreciated quietly. A tool that is wrong — even occasionally — gets
uninstalled and is rarely given a second chance. There is no meaningful
"we'll improve the false-positive rate in the next release" recovery path,
because by the next release the user is already gone. This asymmetry is the
single most important fact shaping every decision in this document.

### The fact-vs-recommendation distinction

This is the most important conceptual tool in the whole project. Every
detector's output falls into exactly one of two categories, and the category
must be obvious from the wording alone, not just from internal documentation:

- **Fact.** A structural, mechanically verifiable claim about the code as
  written. "This function's entire body is a single forwarding call." There
  is no interpretation involved; the claim is true by construction.
- **Review recommendation.** A heuristic signal that something is *worth a
  human looking at*, with no claim about what the human will find. "These
  three functions share a naming pattern and an overlapping signature" is
  true regardless of whether the functions turn out to be meaningfully
  different on inspection — the recommendation to review them is the entire
  claim, not a prediction about the outcome.

A detector is only allowed to phrase output as a fact if it would still be
defensible as a fact in 100% of cases, including adversarial or unusual code.
If a detector cannot meet that bar, its output must be phrased as a review
recommendation, permanently — not as a stepping stone to "fact" status later.
Some detectors in this document (see §5) are heuristic by nature and will
never graduate to fact-level claims, no matter how good the implementation
gets. That's fine. It's not every detector's job to be deterministic; it's
every detector's job to be honest about whether it is.

---

## 3. Product Positioning

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
  permanent, not a v0.2-specific restriction — see §6 for why this matters
  architecturally, not just stylistically.
- **Never takes autonomous action.** No agentic workflows, no auto-fixes, no
  auto-refactoring, now or in any currently planned future version.

Tagline (unchanged): **"Put AI-generated code on a diet."**

---

## 4. Architecture

### Parser: tree-sitter

Unchanged from v0.1. Tree-sitter was chosen over stdlib `ast` specifically so
detection rules could eventually port to JS/TS/Go grammars with a fraction of
the rewrite cost. That bet pays off more directly in v0.2: several of the new
detectors (duplicate helpers, similar modules, utility explosion) are
*structural pattern* checks that translate naturally across languages once
the grammar exists. Do not reconsider stdlib `ast` — this has already been
decided and re-confirmed once.

Packages: `tree-sitter`, `tree-sitter-python`.

### Repository structure (v0.2)

```text
codediet/
├── codediet/
│   ├── cli.py
│   ├── parser.py
│   ├── reporter.py
│   ├── models.py
│   └── detectors/
│       ├── __init__.py
│       ├── wrappers.py        # v0.1, shipped, unchanged in spirit
│       └── (future detectors land here one at a time — see §7)
│
├── tests/
├── examples/
├── README.md
├── CLAUDE.md
├── CLAUDE.v0.1.archive.md
├── pyproject.toml
└── LICENSE
```

### Data model

```python
from dataclasses import dataclass
from enum import Enum

class FindingClass(Enum):
    FACT = "fact"                # deterministic, mechanically defensible
    REVIEW = "review"             # heuristic signal, explicitly not a claim

@dataclass
class Finding:
    detector: str          # e.g. "wrapper", "duplicate_helper_cluster"
    classification: FindingClass
    file: str
    line: int
    message: str            # must match the wording rules in each detector spec
    evidence: dict          # structured, detector-specific supporting data
                             # (e.g. {"function": "parse_float", "target": "float"}
                             # or {"cluster": ["safe_float", "parse_float", "ensure_float"]})
```

Every detector returns `list[Finding]`. The reporter is the only thing that
formats output for display; detectors never format their own strings beyond
populating `message` and `evidence`. The `classification` field exists so
that `reporter.py` can visually and structurally separate facts from review
recommendations in both terminal and JSON output — this separation must be
visible to the user, not just present in the data model. A user glancing at
the output should immediately be able to tell which findings are facts and
which are "go look at this."

### Stack (unchanged)
- Python 3.12+
- CLI: Typer
- Parsing: tree-sitter + tree-sitter-python
- Testing: pytest
- Formatting/linting: Ruff
- Packaging: uv
- No database, no web server, no frontend, no LLM dependencies, no embeddings

---

## 5. Detector Specifications

Each detector below states its purpose, reliability level, false-positive
risk, and whether its output is a **Fact** or a **Review Recommendation**.
Reliability levels are not marketing language — they are an honest internal
classification that should also be communicated to users in documentation.

### 5.1 Wrapper Detection
**Status:** Shipped (v0.1), carried forward unchanged.
**Reliability:** High.
**False positive risk:** Near zero, by construction — this is a pure
structural/geometric AST check, not a heuristic.
**Output class:** Fact.

Detects functions whose entire body is a single pass-through call to another
function or builtin, with arguments forwarded unchanged and no added logic,
branching, transformation, or side effects.

```python
def parse_float(x):
    return float(x)
```

Detection requirements (unchanged from v0.1): exactly one statement in the
body; that statement is a `Return`; the return value is a `Call`; arguments
are forwarded unchanged. Any ambiguity means do not flag. This detector's
job is to remain the proof that a CodeDiet finding can be a Fact — its
standards should not be loosened to catch more cases.

### 5.2 Duplicate Helper Detection
**Status:** Roadmap (not implemented in v0.2 code — see §7 for what v0.2
actually ships).
**Reliability:** Medium.
**False positive risk:** Real and expected — this is why output is
permanently constrained to review language.
**Output class:** Review Recommendation, always. This detector must never
graduate to Fact-level claims, in this version or any future version — see
§2 on why some detectors are heuristic by nature.

Goal: find functions with similar names, similar signatures, and similar
implementation structure — the AI-generated equivalent of reinventing the
same helper under three names because the model had no visibility into
functions written under a different prompt.

```python
safe_float()
parse_float()
ensure_float()
```

Output wording: **"Review Cluster"** — never "duplicate," never "these do the
same thing." The detector reports that a naming-and-signature pattern exists
across N functions; it makes no claim about what inspection will reveal.

### 5.3 Abandoned Implementation Detection
**Status:** Roadmap.
**Reliability:** Medium.
**False positive risk:** Moderate — versioned function/file names are
sometimes intentional (e.g., genuine API versioning), so this detector will
occasionally flag legitimate patterns.
**Output class:** Review Recommendation, always.

Goal: detect likely-superseded implementations left behind after iterative
AI-assisted development — a pattern that's extremely common in practice
(prompt, regenerate, prompt again, never delete the first attempt).

```python
search()
search_v2()
search_new()
search_final()
```
or
```python
old_pipeline()
new_pipeline()
```

Output wording: **"Potentially Superseded Implementation"** — never "delete
the old one," never "this is dead."

### 5.4 Dead Function Detection
**Status:** Roadmap. If implemented, must ship default-OFF (opt-in flag),
consistent with the v0.1-era decision to gate this specific detector — that
reasoning still applies and is restated here because it's easy to lose track
of across version boundaries.
**Reliability:** Medium.
**False positive risk:** High without mitigation — this is empirically the
worst-behaved category of static check in this entire space. The mature
incumbent Python dead-code tool (Vulture) produces roughly 14 false positives
for every genuine finding on real popular repositories, almost entirely from
framework decorators and dynamic dispatch (Flask routes, FastAPI/Pydantic
models, pytest fixtures, dependency injection, plugin/registry patterns) that
static analysis cannot see.
**Output class:** Review Recommendation, always.

Detects functions with no static references anywhere in the traced call
graph. Must ship with explicit, prominent warnings — in both the CLI output
and documentation — about dynamic dispatch, dependency injection, reflection,
and plugin systems as known blind spots. If implemented, the mechanism should
prefer BFS reachability from configurable entry points (`__main__.py`,
`app.py`, package `__init__.py`) over attempting to resolve individual
dynamic calls, plus pre-baked exclusion rules for at minimum Flask,
FastAPI/Pydantic, Django, and pytest.

Output wording: **"Possibly Unused Function"** — never **"Safe to delete."**
That exact phrase is forbidden; it is the single clearest way this detector
could violate the trust model if implemented carelessly.

### 5.5 Similar Module Detection
**Status:** Roadmap.
**Reliability:** Medium-Low.
**False positive risk:** Significant — structural overlap between files is a
weak signal on its own and needs care to avoid flagging legitimately
parallel code (e.g., two services that are similar by design, not by
accident).
**Output class:** Review Recommendation, always.

Detects files with unusually high structural overlap — the file-level
equivalent of §5.2, often produced when an AI assistant is asked to "do the
same thing but for X" and regenerates a near-copy rather than
parameterizing the original.

```text
user_service.py
user_service_v2.py
```

Output wording: **"Review Similar Modules."**

### 5.6 Utility Explosion Detection
**Status:** Roadmap.
**Reliability:** Low. This detector should be documented to users explicitly
as a heuristic-only signal, with lower confidence than every other detector
in this document.
**False positive risk:** High in absolute terms, but low-stakes in
consequence — it flags a project-level pattern, not a specific function or
line, so a wrong flag costs a developer a quick glance rather than chasing
a misleading specific claim.
**Output class:** Review Recommendation, always — and should be visually/
textually distinguished even from the other review-level detectors as the
*least* confident finding type CodeDiet produces.

Goal: identify projects accumulating an unusually large number of
helper/utility modules and small helper functions — a project-level smell
rather than a function-level one.

```text
helpers.py
utils.py
common.py
shared.py
misc.py
```

Output wording: **"Review Utility Growth."**

---

## 6. Reliability Model

Every detector in this project sits on a single honesty spectrum, and that
spectrum — not feature count — is what CodeDiet is actually selling.

| Detector | Reliability | Output Class |
|---|---|---|
| Wrapper Detection | High | Fact |
| Duplicate Helper Detection | Medium | Review |
| Abandoned Implementation Detection | Medium | Review |
| Dead Function Detection | Medium (high FP risk without mitigation) | Review |
| Similar Module Detection | Medium-Low | Review |
| Utility Explosion Detection | Low | Review |

Two rules govern this table permanently:

1. **A detector's reliability tier is a property of the underlying technique,
   not of implementation effort.** You cannot raise "Duplicate Helper
   Detection" from Medium to High reliability by writing better code — name
   and signature similarity is inherently a heuristic, no matter how
   carefully implemented. If a future contributor believes a detector should
   move tiers, that's a claim about the *technique* changing (e.g., adding a
   fundamentally different verification step), not about polish.
2. **Output class tracks reliability, not ambition.** Nothing below "High"
   reliability is permitted to produce Fact-class output, ever. This is the
   mechanism that keeps the whole product honest as it grows — it is much
   easier to accidentally let a Medium-reliability detector's wording drift
   toward fact-like certainty over many small copy edits than to make that
   mistake in one big decision. Review every detector's exact output strings
   against this table before any release.

This is also why CodeDiet refuses composite scores (§3): collapsing six
detectors of wildly different reliability into one number necessarily hides
exactly the information this table exists to surface. A single "Bloat Score"
would average away the difference between a Fact and a Low-confidence
heuristic, which is the opposite of what this project is for.

---

## 7. Roadmap

This section exists to separate **what v0.2 documents** from **what v0.2
ships in code**. Do not conflate the two — the detector specifications in §5
describe the full intended product surface, but most of them are not yet
implemented.

### What v0.2 actually ships in code
- Wrapper Detection (§5.1) — unchanged, carried forward from v0.1
- Updated `Finding` data model with `classification` (Fact / Review) — this
  is a real v0.2 deliverable even though it has no user-visible detector
  attached to it yet beyond wrapper detection
- Reporter updates so the Fact/Review distinction is visible in both
  terminal and JSON output
- This document, repositioning the product and specifying the roadmap

### What v0.2 documents but does NOT implement
Sections 5.2 through 5.6 in full. These are real, considered designs — not
placeholders — but implementing them is future work, one detector at a time,
each validated against real repositories for false-positive rate before
being considered done. Do not build more than one new detector in a single
work session without an explicit decision to do so; this project's core risk
is scope creep happening faster than validation can keep up.

### Suggested implementation order for future versions
Order roughly follows §6's reliability table, highest-confidence first,
since each shipped detector should reinforce trust before a less certain one
is introduced:
1. Duplicate Helper Detection (name/signature pattern matching — no
   execution analysis needed, relatively contained scope)
2. Abandoned Implementation Detection (name-pattern based, similar
   implementation complexity to #1)
3. Similar Module Detection (requires file-level structural comparison,
   meaningfully more implementation complexity than #1/#2)
4. Utility Explosion Detection (project-level heuristic, low implementation
   complexity but needs careful calibration to avoid being noise by default)
5. Dead Function Detection (highest implementation complexity due to
   required framework whitelisting and BFS reachability machinery; highest
   false-positive risk without that machinery; ship last and default-OFF)

This order is a recommendation, not a hard rule — but any deviation should be
a deliberate decision, not an accident of what seemed easiest that day.

---

## 8. Development Rules

- **One detector at a time.** Each new detector is validated against real,
  popular open-source repositories for false-positive rate before being
  considered shippable — hand-written test fixtures alone are not
  sufficient evidence of real-world reliability.
- **Negative test cases are mandatory, not optional.** For every detector,
  write deliberate near-miss tests that confirm the detector does *not* fire
  — e.g., for duplicate helper detection, two functions with similar names
  but genuinely different logic should not cluster together.
- **Output wording is reviewed against §5 and §6 on every change.** Any pull
  request that touches a detector's output strings must be checked against
  the exact forbidden/required phrasing in that detector's spec. "Safe to
  delete," "this is unnecessary," "duplicate," and similar certainty-
  implying language are bugs, not style preferences, when attached to a
  Review-class detector.
- **No detector ships enabled by default unless its reliability tier is
  High.** Currently this means only Wrapper Detection is on by default,
  permanently, until another detector's technique (not just its
  implementation) earns High reliability.
- **Resist scope creep explicitly.** If a session's stated goal is one
  detector, finishing early is not an invitation to start the next one. Flag
  it as available capacity and ask, rather than proceeding silently — this
  project's v0.1-to-v0.2 transition happened because of a real, validated
  finding, not because of an unplanned feature addition, and that discipline
  is the reason this document still has the room to evolve carefully.
- **The Fact/Review distinction is a user-facing contract, not an internal
  note.** If a refactor of `reporter.py` or `models.py` would make that
  distinction less visible in actual CLI/JSON output, that refactor needs to
  be reconsidered, not just shipped because it's cleaner code.

---

## 9. Success Criteria

v0.2 is successful if:

- Wrapper Detection continues to work exactly as it did in v0.1, with no
  regression in precision.
- The `Finding` data model and reporter changes ship, with the Fact/Review
  distinction clearly visible to users in both terminal and JSON output.
- This document accurately reflects the full intended detector roadmap, such
  that any future contributor — human or Claude — can pick up the next
  detector from §7 without needing to re-derive its design from scratch.
- No detector in the shipped product makes a claim stronger than its
  reliability tier justifies.
- The project's repositioning from "wrapper tool" to "AI code bloat
  detector" is reflected honestly — meaning the README and any public-facing
  copy describe the roadmap as a roadmap, not as shipped capability, until
  each detector is actually implemented and validated.

Trust, precision, explainability, and evidence — in that order — remain the
measure of whether this project is working, not feature count and not how
many detectors are documented in this file.
