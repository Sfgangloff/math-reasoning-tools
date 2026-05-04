# math-reasoning-tools

MCP tools for theorem proving and mathematical reasoning with Claude Code.

**Two roles:**
1. **Curated catalog** — assessed references to every existing MCP tool relevant to formal proof and mathematical reasoning.
2. **Original servers** — new MCP servers filling the gaps: human-style intuition tools (visualization, example computation, diagram rendering, search) that pair with Lean4.

## Philosophy

A human mathematician proves theorems by: drawing diagrams, computing small examples, searching the literature, and consulting a proof assistant. This repo gives Claude Code the same toolkit.

- Lean4 is the formal layer (via [lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp), included as a submodule)
- The original servers here are the intuition layer: compute, visualize, search, draw diagrams
- Everything speaks MCP so it integrates into any Claude Code workflow

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`brew install uv` or `pip install uv`)
- Clone with submodules: `git clone --recurse-submodules https://github.com/Sfgangloff/math-reasoning-tools`

### Install all servers

```bash
uv sync
```

### Register the servers globally

Run once after cloning. This discovers every server under `servers/` (and `external/`)
and writes them into the top-level `mcpServers` block of `~/.claude.json`, so they're
available in every Claude Code session — no per-project config needed:

```bash
python3 scripts/setup-mcp.py
```

To verify the servers boot correctly:

```bash
python3 scripts/check-mcp.py
```

**Re-run `setup-mcp.py` whenever:**
- You add a new server under `servers/` or `external/`.
- You **move or rename the repo** — the entries in `~/.claude.json` use absolute paths, so they break if the repo's location changes. Re-running rewrites them.

### Where generated images go

Tools that produce images (`plot_function`, `draw_graph`, `render_tikzcd`, …) write
the PNG to **`<your project root>/images/`** — i.e. the directory Claude Code was
launched from. The directory is created if it doesn't exist. Resolution order:

1. `MATH_TOOLS_IMAGE_DIR` env var (absolute path, overrides everything)
2. `CLAUDE_PROJECT_DIR/images` (set by Claude Code in some contexts)
3. `$PWD/images` (the launcher's working dir — works under `uv run --directory`)
4. `cwd/images` (last resort)

To override per-project, set `MATH_TOOLS_IMAGE_DIR` in your shell or in the
`env` block of the server entry in `~/.claude.json`.

### Manual config (alternative)

If you'd rather not use the auto-setup script, see [`configs/full-stack.json`](configs/full-stack.json)
and add the entries to your project's `.claude/mcp.json` by hand.

## Original Servers

Five servers covering symbolic computation, visualization, search, diagram rendering, and proof navigation. See [docs/tools.md](docs/tools.md) for the full tool reference (32 tools total, all implemented).

## Catalog

Assessed references to existing tools, organized by category:

- [Proof assistants](catalog/proof-assistants.md) — Lean4, Coq, Agda, Isabelle
- [Symbolic computation](catalog/symbolic-computation.md) — SymPy, SageMath, Wolfram, Z3
- [Visualization](catalog/visualization.md) — plotting, graphs, geometry
- [Formal verification](catalog/formal-verification.md) — SMT solvers, model checkers
- [Meta-lists](catalog/meta-lists.md) — curated indexes and academic surveys

## Running tests

```bash
uv run pytest servers/math-compute/tests/ servers/math-viz/tests/ \
              servers/commutative-diagrams/tests/ servers/proof-explorer/tests/ -v
```

Network-dependent tests (math-search) are marked `@pytest.mark.network` and skipped by default. Run them with:

```bash
uv run pytest servers/math-search/tests/ -v -m network
```

## Development

Each server has a FastMCP dev inspector:

```bash
cd servers/<name>
uv run fastmcp dev src/<package>/server.py
```

See [docs/architecture.md](docs/architecture.md), [docs/tool-design-principles.md](docs/tool-design-principles.md), and [docs/contributing.md](docs/contributing.md).

## License

MIT
