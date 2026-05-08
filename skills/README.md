# Skills

Multi-tool procedures for mathematical work. Skills sit on top of the MCP tools in `servers/` — they don't replace tools, they orchestrate them.

**Tools are primitives. Skills are craft.** A tool answers "evaluate this expression"; a skill answers "build intuition for this function" by combining several tools into a procedure a mathematician would naturally walk through.

## Install

```bash
python3 scripts/setup-skills.py
```

Idempotent. Symlinks each skill into `~/.claude/skills/<name>/` and tracks managed entries in a registry file. Does not touch `~/.claude.json` — MCP servers stay registered as you have them.

```bash
python3 scripts/setup-skills.py --list      # show install status
python3 scripts/setup-skills.py --remove    # uninstall managed skills only
```

> **First-time install**: if `~/.claude/skills/` did not exist before, restart Claude Code once after install so the directory watcher picks it up. Subsequent edits propagate live.

## Catalog

### Authored

| Skill | Purpose | Tools orchestrated |
|---|---|---|
| `math-function-intuition` | Plot, sample, find critical points and asymptotes for a 1-var function. | `plot_function`, `sympy_eval`, `sympy_diff`, `sympy_solve` |
| `math-explore-sequence` | Identify a sequence (OEIS), generate further terms, plot growth. | `oeis_lookup`, `oeis_search`, `batch_examples`, `plot_function`, `plot_partial_sums` |
| `math-test-conjecture` | Cascade: small examples → random sampling → structured search → SMT. | `batch_examples`, `conjecture_test`, `find_counterexample`, `z3_check` |
| `math-explore-paper` | Outline + glossary + main results + citations of an arXiv paper. | `arxiv_get`, `arxiv_outline`, `arxiv_extract_definitions`, `arxiv_extract_math`, `arxiv_extract_citations` |
| `lean-find-mathlib-lemma` | Cascade: local search → leansearch → loogle → leanfinder → state_search. | `lean_local_search`, `lean_leansearch`, `lean_loogle`, `lean_leanfinder`, `lean_state_search`, `lean_hover_info` |
| `lean-understand-goal` | Decode a Lean goal: English explanation + hyp graph + minimal hyps + tactic history. | `lean_goal`, `goal_explain`, `hypothesis_graph`, `lean_minimal_hypotheses`, `tactic_history` |
| `lean-proof-checkpoint` | Pre-commit audit: build + sorry map + axiom audit. | `lean_build`, `sorry_map`, `lean_verify` |

### Deferred (add as the need arises)

| Skill | Purpose |
|---|---|
| `math-iterate-map-1d` | Cobweb diagram + fixed points + stability analysis for an iterated map. |
| `math-phase-portrait-2d` | 2-D ODE: phase portrait + critical points + linearization. |
| `math-series-convergence` | Partial sums + integral comparison + symbolic check for series convergence. |
| `math-find-pattern` | OEIS + batch examples + closed-form fitting for an unknown pattern. |
| `math-survey-topic` | arXiv + zbMATH + reference lookup, deduped, ranked. |
| `math-formalize-paper-defs` | Pull definitions from a paper, search Mathlib for matches, side-by-side LaTeX/Lean. |
| `math-commutative-diagram-from-paper` | Extract a diagram description and render via tikzcd. |
| `lean-attempt-tactics` | Try a curated tactic library, escalate to state_search + hammer_premise. |
| `lean-debug-failed-proof` | Diagnostics + goal + lemma search + code-action proposals. |
| `lean-explain-proof` | Walk through a completed proof: tree + per-step goals + narrative. |

## Layout

Skills are grouped by category for organization, but Claude Code only sees the skill name, not the directory path:

```
skills/
├── intuition/              # math intuition workflows
│   ├── math-function-intuition/
│   └── math-explore-sequence/
├── conjecture/             # truth-testing workflows
│   └── math-test-conjecture/
├── paper/                  # literature workflows
│   └── math-explore-paper/
└── lean/                   # Lean proof workflows
    ├── lean-find-mathlib-lemma/
    ├── lean-understand-goal/
    └── lean-proof-checkpoint/
```

Each `<skill>/` contains a `SKILL.md` (frontmatter + procedure body). Scripts live in `<skill>/scripts/` if needed (none of the current skills bundle scripts).

## Adding a new skill

1. Pick a *recurring multi-tool procedure* — not a wrapper around one tool.
2. Create `skills/<category>/<skill-name>/SKILL.md` with frontmatter (`name`, `description`, optional `paths`) and a procedure body that names each tool to call.
3. Run `python3 scripts/setup-skills.py` to symlink it.
4. Test by triggering the description naturally in a Claude Code session.

Naming convention: `math-*` for general math, `lean-*` for Lean-specific.

## Skill design principles

- **Procedure, not primitive.** If the skill is one tool call, delete it.
- **Name tools explicitly.** The procedure body should say `call lean_loogle with X`, not `search Mathlib`. Specificity makes Claude follow the steps.
- **Triggerable description.** Front-load the words the user would actually say ("intuition", "stuck on this goal", "audit before commit").
- **Stop-conditions matter.** A cascade skill says "stop at first match"; a check skill says "stop at first failure". Be explicit.
- **No scripts unless necessary.** The MCP tools already do the work. Add `scripts/` only when you need glue (e.g. parsing a tool's output across calls).
