# Architecture

## Two layers

The repo provides Claude Code with two parallel extension layers:

```
Claude Code session
   │
   ├── Tool layer (MCP servers — primitives)
   │     ├── lean-lsp-mcp           (external — Lean4 LSP + tactic search)
   │     ├── math-compute-mcp       (this repo — SymPy, Z3, OEIS, batch examples)
   │     ├── math-viz-mcp           (this repo — plots, graphs, LaTeX render)
   │     ├── math-search-mcp        (this repo — ArXiv, MathWorld, Wikipedia, zbMATH)
   │     ├── commutative-diagrams-mcp (this repo — tikz-cd / Quiver → PNG)
   │     └── proof-explorer-mcp     (this repo — Lean4 proof tree, goal explain)
   │
   └── Skill layer (markdown procedures — workflows)
         ├── math-function-intuition  (orchestrates plot_function + sympy_*)
         ├── math-explore-sequence    (orchestrates oeis_* + batch_examples + plot_*)
         ├── math-test-conjecture     (orchestrates batch_examples + conjecture_test + …)
         ├── math-explore-paper       (orchestrates arxiv_*)
         ├── lean-find-mathlib-lemma  (orchestrates lean_local_search + lean_loogle + …)
         ├── lean-understand-goal     (orchestrates lean_goal + goal_explain + …)
         └── lean-proof-checkpoint    (orchestrates lean_build + sorry_map + lean_verify)
```

**Tool layer**: independent stdio MCP server processes registered in `~/.claude.json` via `scripts/setup-mcp.py`. Each server is stateless. Each tool is a single primitive operation.

**Skill layer**: directories under `~/.claude/skills/<name>/` containing `SKILL.md` (frontmatter + procedure body). Symlinked from this repo's `skills/` by `scripts/setup-skills.py`. No process. Loaded into the model's context only when the skill triggers (auto from description match, or manual via `/<skill-name>`). Procedures call the tools above.

The two layers are independent: installing skills does not touch `~/.claude.json`, and vice versa. You can run with both, either, or neither.

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

## Skill structure

Each skill under `skills/<category>/<skill-name>/` follows this layout:

```
skills/intuition/math-function-intuition/
└── SKILL.md           # frontmatter (name, description, paths) + procedure body
```

Optional supporting files (per the [Skills standard](https://code.claude.com/docs/en/skills)):

```
skills/<category>/<name>/
├── SKILL.md
├── reference.md       # detailed reference loaded when the skill needs it
└── scripts/
    └── helper.py      # bundled scripts callable via Bash, used as glue only
```

None of the current skills bundle scripts — the MCP tools already do the work, so the procedure body just names them in order. Add `scripts/` only when a skill genuinely needs glue (parsing tool output across calls, or a transformation no tool exposes).

The category folder (`intuition/`, `lean/`, `paper/`, `conjecture/`) is organizational — Claude Code identifies skills by the leaf directory name only.

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
