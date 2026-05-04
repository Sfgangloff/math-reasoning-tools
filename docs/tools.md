# Tool Reference

All tools across the 5 original servers + lean-lsp-mcp. Grouped by concern:
**general-purpose** tools work in any session; **Lean / proof-specific** tools
only matter inside a Lean4 project.

## General-purpose

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
| `z3_check` | Check satisfiability of a formula with Z3 |
| `oeis_lookup` | Look up an integer sequence on OEIS by A-number or terms |

### `math-viz` — Mathematical visualization

All tools save a PNG to `<project>/images/` and return the file path.

| Tool | Description |
|------|-------------|
| `plot_function` | Plot one or more real functions on an interval |
| `plot_parametric` | Parametric curve in 2D or 3D |
| `plot_surface` | 3D surface `z = f(x, y)` |
| `plot_cobweb` | Cobweb plot of an iterated 1D map (fixed points, periodic orbits) |
| `plot_partial_sums` | Partial sums of a series, with optional log-scale for convergence rate |
| `plot_phase_portrait` | Phase portrait of an autonomous 2D ODE system, with trajectories |
| `plot_implicit` | Zero set of a 2-variable expression |
| `plot_region` | Shade a 2D region defined by Boolean inequalities |
| `plot_integrand_with_shading` | Plot a function and shade the area between `a` and `b`; computes the numerical integral |
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
| `arxiv_fetch_source` | Download an arXiv paper's LaTeX source — highest fidelity for theorem statements |
| `arxiv_fetch_text` | Download an arXiv paper's PDF and return extracted text (lossy on math) |
| `arxiv_extract_math` | Extract `\begin{theorem}...\end{theorem}`-style environments from a paper's LaTeX source |
| `loogle_search` | Search Mathlib4 declarations via the public Loogle HTTP service (no Lean install needed) |
| `mathworld_lookup` | Look up a concept on Wolfram MathWorld |
| `wikipedia_math` | Retrieve a Wikipedia math article (full page or specific section) |
| `oeis_search` | Search OEIS by description or sequence terms |
| `zbmath_search` | Search zbMATH Open by keyword, author, or MSC class |

All arXiv tools share a 3-second-per-request throttle (per arXiv's policy).

### `commutative-diagrams` — Diagram rendering

All tools save a PNG to `<project>/images/` and return the file path.

| Tool | Description |
|------|-------------|
| `diagram_from_description` | Render a diagram from a simple text DSL (no LaTeX needed) |
| `render_tikzcd` | Render tikz-cd source to PNG (requires `pdflatex` + `poppler`) |
| `render_quiver` | Render a diagram from [Quiver](https://q.uiver.app) JSON export |

**DSL example for `diagram_from_description`:**
```
objects: A B C D
arrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D
commutes: g ∘ f = k ∘ h
```

## Lean / proof-specific

### `lean-lsp-mcp` — Lean4 LSP-backed tools

The full set lives upstream at https://github.com/oOo0oOo/lean-lsp-mcp. The
ones most relevant in a proof workflow:

| Tool | Description |
|------|-------------|
| `lean_goal` | Proof state at a position (`column` omitted = before/after) |
| `lean_term_goal` | Term-mode goal at a position |
| `lean_hover_info` | Type signature + docs for a symbol |
| `lean_diagnostic_messages` | Compiler errors / warnings / hints for a file |
| `lean_completions` | LSP autocomplete on incomplete code |
| `lean_multi_attempt` | Try multiple tactics at a position; return the goal/diagnostics for each |
| `lean_code_actions` | LSP "Try This" suggestions |
| `lean_run_code` | Compile/execute a standalone snippet |
| `lean_verify` | Axiom audit + unsafe-pattern scan |
| `lean_profile_proof` | Per-line tactic timing |
| `lean_local_search` | Search local project + stdlib for a declaration (uses ripgrep) |
| `lean_leansearch` | Natural-language Mathlib search |
| `loogle` | Type / pattern-based Mathlib search (project-aware) |
| `lean_leanfinder` | Semantic Mathlib search from informal descriptions |
| `lean_state_search` | Theorems applicable to the current goal |
| `lean_hammer_premise` | Premises relevant to the current goal (for `simp` / `aesop`) |
| `lean_build` | Rebuild project + restart LSP |

### `proof-explorer` — Lean4 proof navigation (this repo)

| Tool | Description | Requires |
|------|-------------|----------|
| `sorry_map` | List all `sorry` placeholders in a `.lean` file with line numbers | file access only |
| `tactic_history` | Extract the tactic sequence for a named theorem | file access only |
| `proof_tree` | Visual proof tree at a cursor position | lean-lsp-mcp |
| `goal_explain` | Plain-language explanation of the current Lean4 goal | lean-lsp-mcp |
| `hypothesis_graph` | Dependency graph of local context hypotheses | lean-lsp-mcp |

## Session profiles

The repo ships several `configs/*.json` snippets that bundle a subset of
servers for a particular kind of work. See [`configs/`](../configs/):

| Profile | Servers | Use when |
|---------|---------|----------|
| `minimal.json` | math-compute, math-search | quick computations, no Lean, no plotting |
| `compute-session.json` | math-compute, math-viz | numeric/symbolic computation with plots |
| `search-session.json` | math-search, math-viz | literature search, paper reading, formula rendering |
| `diagram-session.json` | commutative-diagrams, math-viz | diagram-heavy authoring (`render_tikzcd` etc.) |
| `lean-session.json` | lean-lsp-mcp, proof-explorer, math-search, math-viz | active Lean4 work — proof + lemma discovery |
| `lean4-only.json` | lean-lsp-mcp, proof-explorer | Lean4 only, nothing else |
| `full-stack.json` | all five original servers + lean-lsp-mcp | everything (largest tool surface) |
