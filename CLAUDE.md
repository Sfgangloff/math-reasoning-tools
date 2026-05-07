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

## Tool routing

@docs/tool-routing.md

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
