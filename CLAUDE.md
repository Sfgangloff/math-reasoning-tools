# Claude Code instructions for math-reasoning-tools

This repo develops MCP servers for mathematical reasoning. When working here, follow these conventions.

## Two layers: tools and skills

This repo has two parallel layers, both of which Claude Code can use:

- **Tools** (MCP servers in `servers/` and `external/`) — primitive operations: evaluate this expression, plot this function, look up this lemma. Registered into `~/.claude.json` via `scripts/setup-mcp.py`.
- **Skills** (`skills/`) — multi-tool procedures: build intuition for a function, test a conjecture, audit a Lean proof. Each is a `SKILL.md` with frontmatter + a procedure body that names the tools to call. Installed into `~/.claude/skills/` via `scripts/setup-skills.py` (symlinks; does not touch `~/.claude.json`).

**Skills orchestrate tools, they don't replace them.** When adding a skill, first check whether the workflow is genuinely multi-tool — if it's one tool call, leave it as a tool. See `skills/README.md` for the catalog and design principles.

## Working in this repo

- Servers live in `servers/<name>/`. Each is an independent Python package using FastMCP.
- Skills live in `skills/<category>/<skill-name>/SKILL.md`. The category folder is organizational only; Claude Code identifies skills by name.
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

## Skill naming conventions

- `kebab-case` skill names with a domain prefix: `math-*` for general math, `lean-*` for Lean-specific.
- The skill `description` (frontmatter) is what triggers automatic invocation — front-load the words the user would actually say.
- Procedure body names tools explicitly (`call lean_loogle with X`), not generically (`search Mathlib`).

## Tool routing

@docs/tool-routing.md

## Skill routing

@docs/skill-routing.md

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
