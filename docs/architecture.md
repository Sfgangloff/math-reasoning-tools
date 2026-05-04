# Architecture

## Overview

```
Claude Code session
       │
       ├── lean-lsp-mcp          (external — Lean4 LSP + tactic search)
       │
       ├── math-compute-mcp      (this repo — SymPy, Z3, OEIS, batch examples)
       ├── math-viz-mcp          (this repo — plots, graphs, LaTeX render)
       ├── math-search-mcp       (this repo — ArXiv, MathWorld, Wikipedia, zbMATH)
       ├── commutative-diagrams-mcp (this repo — tikz-cd / Quiver → PNG)
       └── proof-explorer-mcp    (this repo — Lean4 proof tree, goal explain)
```

All servers are independent processes communicating with Claude Code via the MCP protocol (stdio transport). Each server is stateless.

## MCP transport

All servers use **stdio transport** (the default for local MCP servers). The `.claude/mcp.json` entry for each server looks like:

```json
{
  "command": "uvx",
  "args": ["math-compute-mcp"],
  "env": {}
}
```

For servers requiring API keys (e.g., `math-search` for some backends), keys are passed via `env`.

## Server structure

Each server under `servers/<name>/` follows this layout:

```
servers/math-compute/
├── pyproject.toml          # package metadata + dependencies
├── src/
│   └── math_compute/
│       ├── __init__.py
│       └── server.py       # FastMCP app + all @mcp.tool() definitions
└── tests/
    └── test_tools.py
```

The entry point declared in `pyproject.toml`:

```toml
[project.scripts]
math-compute-mcp = "math_compute.server:main"
```

`main()` calls `mcp.run()` which starts the stdio server.

## Return types

Tools return one of two shapes:

**Text output** (symbolic results, Lean4 fragments, search results):
```python
str  # plain text or Markdown
```

**Visual output** (plots, diagrams, rendered formulas):
```python
{
    "type": "text",
    "text": "/abs/path/to/image.png"   # PNG written to <project>/images/
}
```

Claude Code reads images on demand from the path. The image directory is
resolved as: `MATH_TOOLS_IMAGE_DIR` → `CLAUDE_PROJECT_DIR/images` →
`$PWD/images` → `cwd/images`.

## Dependency map

```
proof-explorer  ──depends on──▶  lean-lsp-mcp (external, optional)
math-viz        ──depends on──▶  matplotlib, networkx
math-compute    ──depends on──▶  sympy, z3-solver, restrictedpython
                                 sagemath (optional — heavy, separate install)
math-search     ──depends on──▶  httpx (pure HTTP, no local math deps)
commutative-diagrams ──depends on──▶  option A: pdflatex + pdf2image (tikz-cd)
                                      option B: quiver renderer (HTTP)
                                      option C: matplotlib fallback
```

`math-search` has zero local math dependencies and is the easiest to install. `math-compute` is the most universally useful. `proof-explorer` is the most Lean4-specific.

## Evaluation security

`math-compute` evaluates user-supplied SymPy expressions. The threat model is accidental misuse (not adversarial), but we still enforce:

1. **`RestrictedPython`** parses the expression AST before execution; `import`, `open`, `exec`, `__class__`, `__subclasses__` are blocked.
2. **Timeout**: every evaluation runs with a `signal.alarm` / `concurrent.futures` timeout (default 10s).
3. **No filesystem access**: the execution namespace contains only SymPy symbols and math functions.

SageMath evaluation runs in a subprocess with a separate timeout; the parent process is never exposed to the evaluated code.

## Monorepo tooling

The repo uses [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/) to manage all servers as a single monorepo while keeping each server independently publishable:

```toml
# pyproject.toml (root)
[tool.uv.workspace]
members = ["servers/*"]
```

Running `uv sync` at root installs all servers in development mode. Each server can still be published and installed independently via `uvx`.
