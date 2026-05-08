# Math reasoning skills — routing

**Before answering any question involving multi-step mathematical work — building intuition for a function, exploring a sequence, testing a conjecture, exploring an arXiv paper, finding a Mathlib lemma, decoding a Lean goal, or auditing a Lean project — scan the table below and prefer the listed skill over ad-hoc tool calls or free-form reasoning.**

Skills orchestrate several tools into a procedure a mathematician would naturally walk through. They are *not* replacements for tools — they are higher-level workflows. For one-shot operations (a single integral, a single plot, a single arXiv lookup), call the underlying tool directly via [tool-routing.md](tool-routing.md).

Skills are installed globally via `scripts/setup-skills.py` and available in every Claude Code session.

## When to use which skill

| Task | Preferred skill | Tools it orchestrates |
|------|----------------|----------------------|
| Build intuition for a 1-variable function — plot, key values, critical points, asymptotics | `math-function-intuition` | `plot_function`, `sympy_eval`, `sympy_diff`, `sympy_solve` |
| Identify and explore an integer / rational sequence (OEIS lookup, further terms, growth) | `math-explore-sequence` | `oeis_lookup`, `oeis_search`, `batch_examples`, `plot_function`, `plot_partial_sums` |
| Stress-test a "for all" conjecture (cascade examples → sampling → counterexample → SMT) | `math-test-conjecture` | `batch_examples`, `conjecture_test`, `find_counterexample`, `z3_check` |
| Explore an arXiv paper (outline + glossary + main results + citations) | `math-explore-paper` | `arxiv_get`, `arxiv_outline`, `arxiv_extract_definitions`, `arxiv_extract_math`, `arxiv_extract_citations` |
| Find a Lean4 / Mathlib lemma when the name is unknown (cascade search) | `lean-find-mathlib-lemma` | `lean_local_search`, `lean_leansearch`, `lean_loogle`, `lean_leanfinder`, `lean_state_search`, `lean_hover_info` |
| Decode a stuck Lean goal (English explanation + hyp graph + minimal hyps + tactic history) | `lean-understand-goal` | `lean_goal`, `goal_explain`, `hypothesis_graph`, `lean_minimal_hypotheses`, `tactic_history` |
| Pre-commit / pre-PR audit of a Lean project (build + sorries + axioms) | `lean-proof-checkpoint` | `lean_build`, `sorry_map`, `lean_verify` |

## How skill invocation works

- **Auto-invoke**: Claude reads the skill's `description` field at session start. When the user's message matches, Claude loads the full SKILL.md and runs the procedure.
- **Manual invoke**: the user can type `/<skill-name>` to force a specific skill (e.g. `/math-function-intuition`).
- **Skill body**: the procedure body lists the tools to call in order. Follow the steps unless the procedure's own "skip if" conditions apply.

## When NOT to use a skill

A skill is overhead if the user wants exactly one operation:

- "Plot `x^2 sin(1/x)`" → call `plot_function` directly.
- "Integrate `x e^x dx`" → call `sympy_integrate` directly.
- "What's `Nat.add_comm`?" → call `lean_hover_info` directly.

Skills earn their place when the workflow combines ≥ 2 tools and benefits from a stop-condition or synthesis step.

## Adding a new skill

When a multi-tool procedure recurs across sessions, capture it as a skill rather than re-deriving it. See `skills/README.md` ("Adding a new skill" + "Skill design principles").

## Deferred skills (not yet authored)

These workflows are recognized as common multi-tool procedures but the SKILL.md hasn't been written yet. If the user's request matches one of these, walk through the procedure manually using the listed tools, then propose authoring the skill:

| Workflow | Tools that would be orchestrated |
|------|----------------------|
| `math-iterate-map-1d` — analyze an iterated 1-D map (cobweb + fixed points + stability) | `plot_cobweb`, `sympy_solve`, `sympy_diff` |
| `math-phase-portrait-2d` — analyze a 2-D ODE | `plot_phase_portrait`, `sympy_solve`, `sympy_diff` |
| `math-series-convergence` — investigate convergence of a series | `plot_partial_sums`, `sympy_integrate`, `sympy_eval` |
| `math-find-pattern` — pattern-finding from data | `oeis_lookup`, `batch_examples`, `sympy_eval` |
| `math-survey-topic` — literature survey on a topic | `arxiv_search`, `zbmath_search`, `mathworld_lookup`, `wikipedia_math` |
| `math-formalize-paper-defs` — match paper definitions to Mathlib | `arxiv_extract_math`, `lean_leansearch`, `lean_leanfinder`, `render_latex` |
| `math-commutative-diagram-from-paper` — extract + render a diagram | `arxiv_extract_math`, `diagram_from_description`, `render_tikzcd` |
| `lean-attempt-tactics` — try a tactic library, escalate on failure | `lean_multi_attempt`, `lean_state_search`, `lean_hammer_premise` |
| `lean-debug-failed-proof` — diagnose a failing proof | `lean_diagnostic_messages`, `lean_goal`, `lean_state_search`, `lean_code_actions` |
| `lean-explain-proof` — narrate a completed proof | `proof_tree`, `goal_explain`, `tactic_history` |
