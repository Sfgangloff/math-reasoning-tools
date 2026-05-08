# Skill Reference

Multi-tool procedures installed via `scripts/setup-skills.py`. Skills sit on top of the MCP tools documented in [`tools.md`](tools.md) — each one captures a workflow a mathematician would naturally walk through, naming the underlying tools at each step.

> Tools are primitives, skills are procedures. For one-shot operations (a single integral, a single plot) call the tool directly via [`tool-routing.md`](tool-routing.md). For recurring multi-step workflows, use the matching skill via [`skill-routing.md`](skill-routing.md).

## How invocation works

- **Auto-invoke**: Claude reads each skill's `description` frontmatter at session start; a matching user message loads the full `SKILL.md` and runs the procedure.
- **Manual invoke**: type `/<skill-name>` (e.g. `/math-function-intuition`).
- **Edit live**: skills are symlinked from `skills/<category>/<name>/` in this repo to `~/.claude/skills/<name>/`. Edits to the source files propagate without reinstalling.

## Math intuition

### `math-function-intuition`

Build intuition for a one-variable function: plot, sample key values, find critical points, characterize asymptotic behavior.

**Use when** the user asks to "understand", "explore", "get a feel for", or "investigate" a single-variable `f(x)`, or when a function shows up in a problem and a quick mental model would help.

| Step | Tool |
|------|------|
| Plot on a sensible interval | `plot_function` |
| Sample distinguished values | `sympy_eval` |
| Find critical points (`f'=0`) | `sympy_diff`, `sympy_solve` |
| Characterize asymptotics | `sympy_eval` (limits) |

### `math-explore-sequence`

Identify and explore an integer or rational sequence: OEIS lookup, generate further terms, plot growth.

**Use when** the user gives a sequence by formula, recursive rule, generating function, or by listing the first few terms.

| Step | Tool |
|------|------|
| Identify | `oeis_lookup` (or `oeis_search` if described in words) |
| Generate further terms | `batch_examples` |
| Plot growth | `plot_partial_sums` (summable) or `plot_function` (closed form) |

## Conjecture craft

### `math-test-conjecture`

Stress-test a "for all" claim by cascading from cheap to expensive checks.

**Use when** the user states a "for all" claim, asks "is it true that…", or wants evidence before attempting a proof.

| Step | Tool | Stop condition |
|------|------|---------------|
| Small examples | `batch_examples` | counterexample found → report and stop |
| Random sampling | `conjecture_test` | counterexample found → report and stop |
| Structured search | `find_counterexample` | counterexample found → report and stop |
| SMT (when applicable) | `z3_check` | UNSAT → strong evidence; SAT → counterexample |

## Paper exploration

### `math-explore-paper`

Build a structured map of an arXiv paper: outline + glossary of definitions + main results + citation graph.

**Use when** the user gives an arXiv ID or title and asks what's in the paper, what it says, or whether it's relevant.

| Step | Tool |
|------|------|
| Metadata + abstract | `arxiv_get` |
| Section/subsection skeleton | `arxiv_outline` |
| Glossary of definitions | `arxiv_extract_definitions` |
| Theorem statements | `arxiv_extract_math` |
| Citation graph | `arxiv_extract_citations` |

## Lean proof workflow

### `lean-find-mathlib-lemma`

Cascade through Mathlib search backends to find a lemma when the name is unknown. Stops at the first hit and shows the signature.

**Use when** the user is looking for a Mathlib lemma by description, type pattern, or natural-language question, and doesn't know the exact name.

| Step | Tool | Why this rung |
|------|------|--------------|
| Local project + stdlib | `lean_local_search` | fastest, project-aware |
| Natural-language search | `lean_leansearch` | informal phrasing → name |
| Type-pattern search | `lean_loogle` | structural match |
| Semantic search | `lean_leanfinder` | concept-level match |
| Goal-applicable lemmas | `lean_state_search` | filtered by current goal |
| Confirm signature | `lean_hover_info` | verify before using |

### `lean-understand-goal`

Decode a stuck Lean goal: English explanation + hypothesis dependency graph + minimal hypotheses + tactic history at the position.

**Use when** the user is stuck at a `lean_goal` they can't read, or wants to understand the structure of a position before attempting tactics.

| Step | Tool |
|------|------|
| Read goal at position | `lean_goal` |
| Plain-language explanation | `goal_explain` |
| Hypothesis dependencies | `hypothesis_graph` |
| Drop-each-and-recompile | `lean_minimal_hypotheses` |
| Tactic attempts at position | `tactic_history` |

### `lean-proof-checkpoint`

Pre-commit / pre-PR audit of a Lean project: build + `sorry` map + axiom audit on key theorems.

**Use when** the user is about to commit, push, or open a PR on Lean changes and wants confidence the project compiles and isn't smuggling in axioms.

| Step | Tool | Stop condition |
|------|------|---------------|
| Rebuild from scratch | `lean_build` | build error → fix and re-run |
| List remaining `sorry`s | `sorry_map` | report locations |
| Audit named theorems | `lean_verify` | unexpected axiom → flag |

## Deferred (not yet authored)

These workflows are recognized as common multi-tool procedures but the `SKILL.md` hasn't been written yet. If the user's request matches one of these, walk through the procedure manually using the listed tools and propose authoring the skill.

| Skill | Tools that would be orchestrated |
|------|----------------------|
| `math-iterate-map-1d` | `plot_cobweb`, `sympy_solve`, `sympy_diff` |
| `math-phase-portrait-2d` | `plot_phase_portrait`, `sympy_solve`, `sympy_diff` |
| `math-series-convergence` | `plot_partial_sums`, `sympy_integrate`, `sympy_eval` |
| `math-find-pattern` | `oeis_lookup`, `batch_examples`, `sympy_eval` |
| `math-survey-topic` | `arxiv_search`, `zbmath_search`, `mathworld_lookup`, `wikipedia_math` |
| `math-formalize-paper-defs` | `arxiv_extract_math`, `lean_leansearch`, `lean_leanfinder`, `render_latex` |
| `math-commutative-diagram-from-paper` | `arxiv_extract_math`, `diagram_from_description`, `render_tikzcd` |
| `lean-attempt-tactics` | `lean_multi_attempt`, `lean_state_search`, `lean_hammer_premise` |
| `lean-debug-failed-proof` | `lean_diagnostic_messages`, `lean_goal`, `lean_state_search`, `lean_code_actions` |
| `lean-explain-proof` | `proof_tree`, `goal_explain`, `tactic_history` |

## Session profiles

Each session profile in [`configs/`](../configs/) bundles a subset of MCP servers; the skills below are the ones whose procedures stay fully runnable in that profile (every tool they call is present).

| Profile | Skills that pair |
|---------|-----------------|
| `minimal.json` | `math-test-conjecture` (no plotting), `math-explore-paper` (search-only steps) |
| `compute-session.json` | `math-function-intuition`, `math-explore-sequence`, `math-test-conjecture` |
| `search-session.json` | `math-explore-paper` |
| `diagram-session.json` | (none yet — `math-commutative-diagram-from-paper` is deferred) |
| `lean-session.json` | `lean-find-mathlib-lemma`, `lean-understand-goal`, `lean-proof-checkpoint` |
| `lean4-only.json` | `lean-understand-goal`, `lean-proof-checkpoint` (no Mathlib search backends) |
| `full-stack.json` | all authored skills |

## Adding a new skill

See [`skills/README.md`](../skills/README.md) ("Adding a new skill" + "Skill design principles") for the full process. Short version: pick a recurring multi-tool procedure, write `skills/<category>/<name>/SKILL.md` with a triggerable `description` and a procedure body that names each tool, then run `python3 scripts/setup-skills.py`.
