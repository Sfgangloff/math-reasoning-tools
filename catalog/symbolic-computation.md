# Symbolic Computation

MCP servers for computer algebra systems, numerical computation, and formal solvers.

## SymPy-based

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| sympy-mcp | [sdiehl/sympy-mcp](https://github.com/sdiehl/sympy-mcp) | Symbolic manipulation tools | 1 | **Recommended.** Clean API, actively maintained (v0.1.1 May 2025). Good baseline for symbolic math. |
| fermat-mcp | [abhiphile/fermat-mcp](https://github.com/abhiphile/fermat-mcp) | SymPy + NumPy + Matplotlib unified | 1 | Broader scope than sympy-mcp. Includes plotting. FastMCP-based. |
| math-mcp (codeprimate) | [codeprimate/math-mcp](https://github.com/codeprimate/math-mcp) | SymPy + SciPy + data viz | 1 | Good coverage of equation solving, calculus, statistics. |

### Tool inventory: sympy-mcp

31 tools. SymPy works on a *registry* of named variables/expressions: you `intro` a symbol, `introduce_expression` to parse a formula into a stored handle, then operate on handles.

**Variables & expressions:**
- `intro(var_name, pos_assumptions, neg_assumptions)` — introduce a symbol with positive/negative assumption flags.
- `intro_many(...)` — introduce several at once.
- `introduce_expression(expr_str)` — parse a string into a stored expression handle.
- `print_latex_expression(expr_key)` — render a stored expression as LaTeX.
- `simplify_expression(expr_key)`, `substitute_expression(expr_key, var, value)`.
- `differentiate_expression(expr_key, variable)`, `integrate_expression(expr_key, variable)`.

**Equation solving:**
- `solve_algebraically(expr_key, variable, domain)` — closed-form solve.
- `solve_linear_system(...)`, `solve_nonlinear_system(...)`.

**Differential equations:**
- `introduce_function(func_name)` — declare a function symbol for ODE/PDE work.
- `dsolve_ode(expr_key, func_name)`, `pdsolve_pde(expr_key, func_name)`.

**Tensor calculus / GR:**
- `create_predefined_metric(metric_name)`, `search_predefined_metrics(...)`, `create_custom_metric(...)`.
- `calculate_tensor(metric_key, tensor_type)`, `print_latex_tensor(tensor_key)`.

**Vector calculus:**
- `create_coordinate_system(...)`, `create_vector_field(coord_sys, components)`.
- `calculate_curl(field_key)`, `calculate_divergence(field_key)`, `calculate_gradient(field_key)`.

**Units:**
- `convert_to_units(quantity, target_units)`, `quantity_simplify_units(quantity_key)`.

**Matrices:**
- `create_matrix(data)`, `matrix_determinant`, `matrix_inverse`, `matrix_eigenvalues`, `matrix_eigenvectors`.

### Tool inventory: fermat-mcp

Three sub-servers under one umbrella.

**Matplotlib (`mpl_mcp`):**
- `plot_barchart(data)`, `plot_scatter(data)`, `plot_chart(data, chart_type)`.
- `plot_stem(data)`, `plot_stack(data)`.
- `eqn_chart(equation, x_range)` — plot a symbolic equation.

**NumPy (`numpy_mcp`):** elementwise (`add`, `sub`, `mul`, `div`, `power`, `abs`, `exp`, `log`, `sqrt`), trig (`sin`, `cos`, `tan`), stats (`mean`, `median`, `std`, `var`, `min`, `max`), linear algebra (`dot`, `matmul`, `inv`, `det`, `eig`, `solve`), array shape (`reshape`, `flatten`, `concatenate`, `transpose`). Exact signatures undocumented upstream.

**SymPy (`sympy_mcp`):** algebraic (`simplify`, `expand`, `factor`), calculus (`diff`, `integrate`, `limit`, `series`), solving (`solve`, `solveset`), matrices (`determinant`, `inverse`, `eigenvalues`). Exact signatures undocumented upstream.

## Wolfram Language / Mathematica

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| mathematica-mcp | [lars20070/mathematica-mcp](https://github.com/lars20070/mathematica-mcp) | Wolfram Language evaluation via `wolframscript` | 4 (requires Wolfram Engine license) | Clean wrapping of `wolframscript` CLI. Only useful if you already have a license. |
| mcp-server-mathematica | [texra-ai/mcp-server-mathematica](https://github.com/texra-ai/mcp-server-mathematica) | Mathematica code execution + derivation verification | 4 | Adds verification step on top of evaluation. Interesting for checking algebraic manipulations. |
| mathematica_mcp | [aac6fef/mathematica_mcp](https://github.com/aac6fef/mathematica_mcp) | Mathematica kernel evaluation | 4 | Manages a persistent kernel session. |
| Wolfram-MCP | [paraporoco/Wolfram-MCP](https://github.com/paraporoco/Wolfram-MCP) | Wolfram Language computation | 4 | FastMCP-based Wolfram Language server. |
| MCPServer (Wolfram) | [rhennigan/MCPServer](https://github.com/rhennigan/MCPServer) | MCP server written in Wolfram Language | 5 | Meta: MCP server implemented inside Mathematica itself. Niche. |

## Wolfram Alpha (API)

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| mcp-wolframalpha | [akalaric/mcp-wolframalpha](https://github.com/akalaric/mcp-wolframalpha) | Wolfram Alpha query | 1 (API key required) | Simple and reliable. Best when you want a quick answer without full Mathematica. |
| mcp-wolfram-alpha | [cnosuke/mcp-wolfram-alpha](https://github.com/cnosuke/mcp-wolfram-alpha) | Wolfram Alpha query | 1 (API key required) | Similar to above. |
| wolframalpha-mcp-server | [StoneDot/wolframalpha-mcp-server](https://github.com/StoneDot/wolframalpha-mcp-server) | Wolfram Alpha LLM API | 1 (API key required) | Uses the LLM-optimized API endpoint — better structured output for Claude. |

### Tool inventory: wolframalpha-mcp-server (StoneDot)

Single tool — uses the Wolfram|Alpha **LLM API** (LLM-optimized), not the standard REST API.

- `query_wolfram(query, maxchars?, units?, location?)` — natural-language computation/lookup; returns structured results across math, physics, chemistry, geography, history, astronomy. `maxchars` defaults to 6800; `units` accepts e.g. "metric"/"imperial"; `location` adds geographic context.

## SMT Solvers / Formal Logic

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| Chiasmus | [yogthos/chiasmus](https://github.com/yogthos/chiasmus) | Z3 satisfiability check, Tau Prolog, tree-sitter analysis | 2 | **Recommended for decidable fragments.** Z3 via MCP is powerful for arithmetic, linear algebra, bit-vectors. Full tool inventory in [formal-verification.md](formal-verification.md#tool-inventory-chiasmus). |
| Chimera-Protocol | [mcp-research/Chimera-Protocol__csl-core](https://github.com/mcp-research/Chimera-Protocol__csl-core) | Z3 + TLA+ (roadmap) | 3 | Neuro-symbolic safety layer. Heavier than Chiasmus; aimed at agent safety. |

## General Mathematical Computation

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| MCP-Mathematics | [SHSharkar/MCP-Mathematics](https://github.com/SHSharkar/MCP-Mathematics) | 52 built-in math functions, 158 unit conversions, financial calculations | 1 | Production-ready, safe AST evaluation. Zero heavy dependencies. Good for quick arithmetic. |
| calculator-mcp-server | [huhabla/calculator-mcp-server](https://github.com/huhabla/calculator-mcp-server) | Symbolic math, statistics, matrix operations | 1 | Broader than a calculator. Covers most basic CAS use cases. |
| math-mcp-learning-server | [clouatre-labs/math-mcp-learning-server](https://github.com/clouatre-labs/math-mcp-learning-server) | Matrix algebra, data viz, persistent workspace | 2 | FastMCP 2.0, educational focus. Persistent workspace is unusual and useful. |

## Notes

- For pure symbolic manipulation in a theorem-proving workflow, **sympy-mcp** is the recommended starting point — then supplement with **Chiasmus** (Z3) for decidable goals.
- Wolfram tools require a license; the **Wolfram Alpha API tools** are free-tier accessible and sufficient for most quick lookups.
- **SageMath** is conspicuously absent from existing MCP tools despite being the most powerful open-source CAS (covers number theory, algebraic geometry, group theory, etc.). This is a gap filled by the `math-compute` server in this repo.
