# Tool Design Principles

All original MCP servers in this repo follow these constraints.

## 1. Lean4-first output

Where relevant, tools return output usable alongside Lean4. For example:
- `sympy_factor` returns the factored form both as a human-readable string and as a Lean4 expression fragment
- `batch_examples` output is formatted so patterns can be directly stated as `∀ n, ...` conjectures
- `z3_check` reports results in terms that map to Lean4 tactic goals

## 2. Visual output as inline base64 PNG

All image-producing tools return:

```python
{"image": "<base64-encoded PNG>", "alt": "human-readable description", "width": int, "height": int}
```

Claude Code renders these inline. Tools never write image files to disk or return file paths.

## 3. Stateless and idempotent

Tools have no server-side state. Calling the same tool twice with the same input returns the same result. No session management, no temporary files persisted across calls.

## 4. Fail loudly with mathematical context

Errors include math context, not just stack traces:

- Bad: `"SymPy error: cannot factor"`
- Good: `"sympy_factor: could not factor x^5 + x + 1 over ℤ. Try over ℝ (roots='real') or ℂ (roots='complex'), or check if the polynomial is irreducible with sympy_eval('factor(x**5+x+1, extension=True)')."`

## 5. FastMCP throughout

All servers use [FastMCP](https://github.com/jlowin/fastmcp). Minimal boilerplate:

```python
from fastmcp import FastMCP

mcp = FastMCP("math-compute")

@mcp.tool()
def sympy_eval(expression: str) -> str:
    """Evaluate a SymPy expression. Example: 'expand((x+1)**3)'"""
    ...
```

## 6. `uvx`-installable

Each server is a standalone Python package published to PyPI (or installable from this repo) so it can be added to `.claude/mcp.json` with:

```json
{"command": "uvx", "args": ["math-compute-mcp"]}
```

No global install required.

## 7. Safe evaluation

User-supplied expressions are evaluated with one of:
- `RestrictedPython` — for SymPy/NumPy expressions where the full Python AST must be constrained
- Subprocess with timeout — for SageMath (which has its own process model anyway)
- A typed DSL parsed before any execution — for diagram descriptions

Direct `eval()` on unsanitized input is never used.

## 8. Tool docstrings are the interface

The docstring on each `@mcp.tool()` function is what Claude Code reads to decide whether and how to call the tool. It must:
- State what the tool does in one sentence
- Give at least one concrete input example
- State what the output format is
- Mention any required dependencies or API keys

## 9. No external mutation

Tools are read-only with respect to external systems. They may call read-only APIs (ArXiv, OEIS, MathWorld) but never POST, never write to databases, never mutate Lean4 files.

## 10. Independence

Each server in `servers/` is independently useful. Installing `math-compute` without `math-search` or Lean4 must work correctly. Inter-server dependencies are documented but optional.

---

# Skill Design Principles

Skills (`skills/`) layer on top of the tools above. They follow a different set of constraints because they are *procedures*, not primitives.

## 1. Procedure, not primitive

A skill is a multi-step workflow that combines several tools. If a "skill" can be replaced by one tool call, it shouldn't be a skill — it adds context overhead with no benefit.

The bar: at least 2 tools, with a procedure worth capturing (a cascade, a stop-condition, a synthesis step that combines multiple tool outputs).

## 2. Name tools explicitly

The procedure body should say `call lean_loogle with X`, not `search Mathlib`. Specific tool references make Claude follow the steps. Generic descriptions invite improvisation, which is what the skill is meant to replace.

## 3. Triggerable description

The frontmatter `description` is what Claude reads at session start to decide when to auto-invoke the skill. Front-load the words the user would actually say:

- Bad: `"Performs a multi-step workflow for analyzing one-variable functions."`
- Good: `"Build intuition for a one-variable function by plotting it … Use when the user asks to 'understand', 'explore', 'get a feel for' a function."`

## 4. Stop-conditions are first-class

Cascade skills (`lean-find-mathlib-lemma`) say "stop at the first match". Check skills (`math-test-conjecture`) say "stop at the first failure". Audit skills (`lean-proof-checkpoint`) run all checks and report. State which model the skill follows in the procedure body — Claude won't guess correctly otherwise.

## 5. Synthesis step

End every skill with a synthesis step that combines outputs from earlier steps into a single user-facing report. Without it, the user sees a sequence of raw tool outputs and has to assemble the picture themselves — which defeats the purpose of the skill.

## 6. No scripts unless necessary

Skills can bundle scripts under `scripts/`, but the MCP tools already do the work. Add a script only when the skill genuinely needs glue — parsing tool output across calls, transforming a representation no tool exposes, or wiring two tools whose I/O don't quite match.

The current 7 skills bundle zero scripts. That's the target.

## 7. Skip-if conditions

Every step in a procedure should state when to skip it. Not every plot needs a derivative; not every paper needs its citation graph extracted. Without skip-if conditions, the skill runs every step every time and feels mechanical.

## 8. Independence from MCP setup

Skills must work even if some MCP tools aren't registered (the user removed them, the network is down, etc.). The procedure body should treat each tool call as fallible and degrade gracefully — if `oeis_lookup` fails, the rest of `math-explore-sequence` should still produce useful output.

## 9. Naming convention

`kebab-case` with a domain prefix:

- `math-*` for general mathematics
- `lean-*` for Lean4-specific workflows

Add a new prefix only when a domain has 3+ skills (e.g. `viz-*`, `algebra-*`).

## 10. Skills are versioned with the repo

Edit a skill in this repo, run `setup-skills.py` (or rely on the existing symlink — Claude Code watches `~/.claude/skills/` for changes), and the live behavior updates within the session. No restart required for edits to existing skills. Add a new top-level skill directory and Claude Code requires one restart to pick up the new watcher.
