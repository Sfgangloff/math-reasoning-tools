# Math reasoning tools — routing

**Before answering any question involving symbolic computation, conjecture testing, paper search/extraction, plotting, commutative diagrams, or Lean4 proofs, scan the routing tables below and prefer the listed tool over ad-hoc reasoning or generic web search.** These MCP servers are installed globally; they are available in every project, not only in the math-reasoning-tools repo.

Tool schemas are loaded on demand. If a tool name from these tables does not appear in your top-level tool list, fetch it via `ToolSearch` with `select:<tool_name>` before calling it.

## When to use which tool

The routing tables below are split by concern: general-purpose tools that
help in any session, and Lean/proof-specific tools that only matter when
working in a Lean4 project.

### General-purpose

| Task | Preferred tool |
|------|---------------|
| Evaluate / simplify a symbolic expression | `sympy_eval` |
| Solve an equation or system | `sympy_solve` |
| Differentiate symbolically | `sympy_diff` |
| Integrate symbolically | `sympy_integrate` |
| Factor a polynomial / expression | `sympy_factor` |
| Expand a product / power | `sympy_expand` |
| Compute small examples to find a pattern | `batch_examples` |
| Stress-test a conjecture by random sampling | `conjecture_test` |
| Search for a counterexample over a structured domain | `find_counterexample` |
| Check if a formula holds in a decidable fragment | `z3_check` |
| Look up an integer sequence | `oeis_lookup` or `oeis_search` |
| Find a relevant paper | `arxiv_search` |
| Get metadata for a known arXiv ID | `arxiv_get` |
| Read the full text / source of an arXiv paper | `arxiv_fetch_source` (LaTeX, preferred) or `arxiv_fetch_text` (PDF text fallback) |
| Extract theorems/definitions for formalization | `arxiv_extract_math` |
| Pull a paper's definitions as a glossary | `arxiv_extract_definitions` |
| Pull a paper's citations + bibliography | `arxiv_extract_citations` |
| Skim a paper's section structure | `arxiv_outline` |
| Look up a definition / theorem statement | `mathworld_lookup` or `wikipedia_math` |
| Search zbMATH for a paper / review | `zbmath_search` |
| Plot a function or surface | `plot_function`, `plot_surface` |
| Plot a parametric curve | `plot_parametric` |
| Plot an iterated map / partial sums / phase portrait | `plot_cobweb`, `plot_partial_sums`, `plot_phase_portrait` |
| Plot an implicit curve or shaded region | `plot_implicit`, `plot_region`, `plot_integrand_with_shading` |
| Visualize a graph, poset, or simplicial complex | `draw_graph`, `draw_poset`, `draw_simplicial_complex` |
| Visualize a matrix as a heatmap / sparsity pattern | `draw_matrix` |
| Render a LaTeX formula as an image | `render_latex` |
| Draw a commutative diagram | `render_tikzcd`, `render_quiver`, or `diagram_from_description` |

### Lean / proof-specific

| Task | Preferred tool |
|------|---------------|
| Find a Lean4 lemma in Mathlib (project open) | `loogle` (lean-lsp-mcp) — project-aware, LSP-driven |
| Find a Lean4 lemma in Mathlib (no Lean install) | `loogle_search` (math-search) — HTTP-only fallback |
| Natural-language Mathlib search | `lean_leansearch` |
| Semantic / conceptual Mathlib search | `lean_leanfinder` |
| Find lemmas applicable to current goal | `lean_state_search` |
| Suggest premises for `simp` / `aesop` | `lean_hammer_premise` |
| Inspect proof state at a position | `lean_goal`, `lean_term_goal` |
| Inspect type signature + docs of a symbol | `lean_hover_info` |
| Try tactics without editing | `lean_multi_attempt` |
| Audit axioms used by a theorem | `lean_verify` |
| Understand the current Lean4 proof state | `proof_tree`, `goal_explain` |
| Visualize hypothesis dependencies | `hypothesis_graph` |
| Find all `sorry`s in a Lean4 file | `sorry_map` |
| Identify which hypotheses of a theorem are actually load-bearing | `lean_minimal_hypotheses` |
| Review tactic attempts / proof history at a position | `tactic_history` |

## Lean4 workflow

1. Write the theorem statement in Lean4
2. Use `goal_explain` to read the initial goal in plain language
3. Use `loogle` / `lean_leansearch` / `arxiv_search` to find relevant lemmas
4. Use `arxiv_extract_math` if formalizing from a paper
5. Use `sympy_eval` / `batch_examples` to compute evidence for the approach
6. Use `render_tikzcd` or `draw_graph` to visualize structure if needed
7. Apply tactics; use `proof_tree` to track progress
8. Use `sorry_map` to audit incomplete proofs before committing
