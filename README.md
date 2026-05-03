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

### Use locally in Claude Code

Add to your project's `.claude/mcp.json` (see [`configs/`](configs/) for full examples):

```json
{
  "mcpServers": {
    "math-compute": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/math-reasoning-tools/servers/math-compute", "math-compute-mcp"]
    },
    "math-viz": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/math-reasoning-tools/servers/math-viz", "math-viz-mcp"]
    },
    "math-search": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/math-reasoning-tools/servers/math-search", "math-search-mcp"]
    },
    "commutative-diagrams": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/math-reasoning-tools/servers/commutative-diagrams", "math-commutative-diagrams-mcp"]
    },
    "proof-explorer": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/math-reasoning-tools/servers/proof-explorer", "math-proof-explorer-mcp"]
    }
  }
}
```

See [`configs/full-stack.json`](configs/full-stack.json) for the configuration including lean-lsp-mcp.

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
