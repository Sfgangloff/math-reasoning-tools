# Claude Code instructions for math-reasoning-tools

This repo develops MCP servers for mathematical reasoning. When working here, follow these conventions.

## Working in this repo

- Servers live in `servers/<name>/`. Each is an independent Python package using FastMCP.
- `catalog/` contains Markdown documentation — no code there.
- `configs/` contains ready-to-use `.claude/mcp.json` snippets — keep them in sync with actual server tool names.
- `docs/` contains design documentation — update it when architecture decisions change.

## Code conventions

- All servers use [FastMCP](https://github.com/jlowin/fastmcp). Import as `from fastmcp import FastMCP`.
- Tools return either a plain string (for text/LaTeX/Lean4 output) or a dict with `{"image": "<base64-png>", "description": "..."}` for visual output.
- No tool writes to disk or makes mutating network calls.
- Evaluation of user-supplied expressions uses `RestrictedPython` or subprocess isolation — never `eval()` directly.
- Each server has its own `pyproject.toml` and can be installed independently via `uvx`.

## MCP tool naming conventions

- `snake_case` tool names
- Math domain prefix: `sympy_`, `sage_`, `z3_`, `arxiv_`, `lean_`, `plot_`, `draw_`
- Tool docstrings are what the model sees — make them precise and include example inputs

## When to use which tool

The routing tables below are split by concern: general-purpose tools that
help in any session, and Lean/proof-specific tools that only matter when
working in a Lean4 project.

### General-purpose

| Task | Preferred tool |
|------|---------------|
| Simplify / factor / differentiate / integrate symbolically | `sympy_eval`, `sympy_solve` |
| Compute small examples to find a pattern | `batch_examples` |
| Check if a formula holds in a decidable fragment | `z3_check` |
| Look up an integer sequence | `oeis_lookup` or `oeis_search` |
| Find a relevant paper | `arxiv_search` |
| Read the full text / source of an arXiv paper | `arxiv_fetch_source` (LaTeX, preferred) or `arxiv_fetch_text` (PDF text fallback) |
| Extract theorems/definitions for formalization | `arxiv_extract_math` |
| Look up a definition / theorem statement | `mathworld_lookup` or `wikipedia_math` |
| Search zbMATH for a paper / review | `zbmath_search` |
| Plot a function or surface | `plot_function`, `plot_surface` |
| Plot an iterated map / partial sums / phase portrait | `plot_cobweb`, `plot_partial_sums`, `plot_phase_portrait` |
| Plot an implicit curve or shaded region | `plot_implicit`, `plot_region`, `plot_integrand_with_shading` |
| Visualize a graph, poset, or simplicial complex | `draw_graph`, `draw_poset`, `draw_simplicial_complex` |
| Render a LaTeX formula as an image | `render_latex` |
| Draw a commutative diagram | `render_tikzcd`, `render_quiver`, or `diagram_from_description` |

### Lean / proof-specific

| Task | Preferred tool |
|------|---------------|
| Find a Lean4 lemma in Mathlib (project open) | `loogle` (lean-lsp-mcp) — project-aware, LSP-driven |
| Find a Lean4 lemma in Mathlib (no Lean install) | `loogle_search` (math-search) — HTTP-only fallback |
| Natural-language Mathlib search | `lean_leansearch` |
| Semantic / conceptual Mathlib search | `lean_leanfinder` |
| Find lemmas applicable to current goal | `lean_state_search` |
| Suggest premises for `simp` / `aesop` | `lean_hammer_premise` |
| Inspect proof state at a position | `lean_goal`, `lean_term_goal` |
| Inspect type signature + docs of a symbol | `lean_hover_info` |
| Try tactics without editing | `lean_multi_attempt` |
| Audit axioms used by a theorem | `lean_verify` |
| Understand the current Lean4 proof state | `proof_tree`, `goal_explain` |
| Visualize hypothesis dependencies | `hypothesis_graph` |
| Find all `sorry`s in a Lean4 file | `sorry_map` |

## Lean4 workflow

1. Write the theorem statement in Lean4
2. Use `goal_explain` to read the initial goal in plain language
3. Use `loogle` / `lean_leansearch` / `arxiv_search` to find relevant lemmas
4. Use `arxiv_extract_math` if formalizing from a paper
5. Use `sympy_eval` / `batch_examples` to compute evidence for the approach
6. Use `render_tikzcd` or `draw_graph` to visualize structure if needed
7. Apply tactics; use `proof_tree` to track progress
8. Use `sorry_map` to audit incomplete proofs before committing

## Development

To run a server locally during development:

```bash
cd servers/<name>
uv run fastmcp dev server.py
```

To run tests:

```bash
cd servers/<name>
uv run pytest
```
