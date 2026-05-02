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

### `math-compute` — Symbolic computation

| Tool | Description |
|------|-------------|
| `sympy_eval` | Evaluate and simplify a SymPy expression; returns result + LaTeX |
| `sympy_solve` | Solve equations symbolically (single or system) |
| `sympy_diff` | Differentiate an expression |
| `sympy_integrate` | Definite or indefinite integration |
| `sympy_factor` | Factor a polynomial over ℤ, ℚ, or ℂ |
| `sympy_expand` | Expand a product or power |
| `batch_examples` | Evaluate an expression for a range of integer values — useful for pattern-finding |
| `z3_check` | Check satisfiability of a formula with Z3 (requires `pip install z3-solver`) |
| `oeis_lookup` | Look up an integer sequence on OEIS by A-number or terms |

### `math-viz` — Mathematical visualization

All tools return inline PNG images rendered by Claude Code.

| Tool | Description |
|------|-------------|
| `plot_function` | Plot one or more real functions on an interval |
| `plot_parametric` | Parametric curve in 2D or 3D |
| `plot_surface` | 3D surface `z = f(x, y)` |
| `draw_graph` | Graph from edge list (directed or undirected, multiple layouts) |
| `draw_poset` | Hasse diagram from cover relations |
| `draw_simplicial_complex` | 2D simplicial complex from facets |
| `render_latex` | LaTeX math formula → PNG (no LaTeX installation required) |
| `draw_matrix` | Matrix with optional row/column labels and cell highlighting |

### `math-search` — Mathematical knowledge search

| Tool | Description |
|------|-------------|
| `arxiv_search` | Search ArXiv (math.* categories) by keyword |
| `arxiv_get` | Retrieve abstract and metadata of a paper by ArXiv ID |
| `mathlib_search` | Search Mathlib4 declarations via Loogle |
| `mathworld_lookup` | Look up a concept on Wolfram MathWorld |
| `wikipedia_math` | Retrieve a Wikipedia math article (full page or specific section) |
| `oeis_search` | Search OEIS by description or sequence terms |
| `zbmath_search` | Search zbMATH Open by keyword, author, or MSC class |

### `commutative-diagrams` — Diagram rendering

| Tool | Description |
|------|-------------|
| `diagram_from_description` | Render a diagram from a simple text DSL (no LaTeX needed) |
| `render_tikzcd` | Render tikz-cd source to PNG (requires `pdflatex` + `pdf2image`) |
| `render_quiver` | Render a diagram from [Quiver](https://q.uiver.app) JSON export |

**DSL example for `diagram_from_description`:**
```
objects: A B C D
arrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D
commutes: g ∘ f = k ∘ h
```

### `proof-explorer` — Lean4 proof navigation

| Tool | Description | Requires |
|------|-------------|---------|
| `sorry_map` | List all `sorry` placeholders in a `.lean` file with line numbers | file access only |
| `tactic_history` | Extract the tactic sequence for a named theorem | file access only |
| `proof_tree` | Visual proof tree at a cursor position | lean-lsp-mcp |
| `goal_explain` | Plain-language explanation of the current Lean4 goal | lean-lsp-mcp |
| `hypothesis_graph` | Dependency graph of local context hypotheses | lean-lsp-mcp |

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
