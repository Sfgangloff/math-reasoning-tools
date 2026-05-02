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

## When to use which tool (for Claude Code sessions using the full-stack config)

| Task | Preferred tool |
|------|---------------|
| Simplify / factor / differentiate / integrate symbolically | `sympy_eval`, `sympy_solve` |
| Compute small examples to find a pattern | `batch_examples` |
| Check if a formula holds in a decidable fragment | `z3_check` |
| Look up an integer sequence | `oeis_lookup` or `oeis_search` |
| Find a Lean4 lemma in Mathlib | `mathlib_search` (via lean-lsp-mcp Loogle) |
| Find a relevant paper | `arxiv_search` |
| Look up a definition / theorem statement | `mathworld_lookup` or `wikipedia_math` |
| Plot a function or surface | `plot_function`, `plot_surface` |
| Visualize a graph, poset, or simplicial complex | `draw_graph`, `draw_poset`, `draw_simplicial_complex` |
| Render a LaTeX formula as an image | `render_latex` |
| Draw a commutative diagram | `render_tikzcd` or `render_quiver` |
| Understand the current Lean4 proof state | `proof_tree`, `goal_explain` |
| Find all `sorry`s in a Lean4 file | `sorry_map` |

## Lean4 workflow

1. Write the theorem statement in Lean4
2. Use `goal_explain` to read the initial goal in plain language
3. Use `mathlib_search` / `arxiv_search` to find relevant lemmas
4. Use `sympy_eval` / `batch_examples` to compute evidence for the approach
5. Use `render_tikzcd` or `draw_graph` to visualize structure if needed
6. Apply tactics; use `proof_tree` to track progress
7. Use `sorry_map` to audit incomplete proofs before committing

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
