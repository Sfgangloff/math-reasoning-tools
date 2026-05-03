# Tool Reference

All 32 tools across the 5 original servers. Every tool is implemented.

## `math-compute` — Symbolic computation

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

## `math-viz` — Mathematical visualization

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

## `math-search` — Mathematical knowledge search

| Tool | Description |
|------|-------------|
| `arxiv_search` | Search ArXiv (math.* categories) by keyword |
| `arxiv_get` | Retrieve abstract and metadata of a paper by ArXiv ID |
| `mathlib_search` | Search Mathlib4 declarations via Loogle |
| `mathworld_lookup` | Look up a concept on Wolfram MathWorld |
| `wikipedia_math` | Retrieve a Wikipedia math article (full page or specific section) |
| `oeis_search` | Search OEIS by description or sequence terms |
| `zbmath_search` | Search zbMATH Open by keyword, author, or MSC class |

## `commutative-diagrams` — Diagram rendering

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

## `proof-explorer` — Lean4 proof navigation

| Tool | Description | Requires |
|------|-------------|---------|
| `sorry_map` | List all `sorry` placeholders in a `.lean` file with line numbers | file access only |
| `tactic_history` | Extract the tactic sequence for a named theorem | file access only |
| `proof_tree` | Visual proof tree at a cursor position | lean-lsp-mcp |
| `goal_explain` | Plain-language explanation of the current Lean4 goal | lean-lsp-mcp |
| `hypothesis_graph` | Dependency graph of local context hypotheses | lean-lsp-mcp |
