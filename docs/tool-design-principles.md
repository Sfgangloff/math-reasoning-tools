# Tool Design Principles

All original MCP servers in this repo follow these constraints.

## 1. Lean4-first output

Where relevant, tools return output usable alongside Lean4. For example:
- `sympy_factor` returns the factored form both as a human-readable string and as a Lean4 expression fragment
- `batch_examples` output is formatted so patterns can be directly stated as `∀ n, ...` conjectures
- `z3_check` reports results in terms that map to Lean4 tactic goals

## 2. Visual output as inline base64 PNG

All image-producing tools return:

```python
{"image": "<base64-encoded PNG>", "alt": "human-readable description", "width": int, "height": int}
```

Claude Code renders these inline. Tools never write image files to disk or return file paths.

## 3. Stateless and idempotent

Tools have no server-side state. Calling the same tool twice with the same input returns the same result. No session management, no temporary files persisted across calls.

## 4. Fail loudly with mathematical context

Errors include math context, not just stack traces:

- Bad: `"SymPy error: cannot factor"`
- Good: `"sympy_factor: could not factor x^5 + x + 1 over ℤ. Try over ℝ (roots='real') or ℂ (roots='complex'), or check if the polynomial is irreducible with sympy_eval('factor(x**5+x+1, extension=True)')."`

## 5. FastMCP throughout

All servers use [FastMCP](https://github.com/jlowin/fastmcp). Minimal boilerplate:

```python
from fastmcp import FastMCP

mcp = FastMCP("math-compute")

@mcp.tool()
def sympy_eval(expression: str) -> str:
    """Evaluate a SymPy expression. Example: 'expand((x+1)**3)'"""
    ...
```

## 6. `uvx`-installable

Each server is a standalone Python package published to PyPI (or installable from this repo) so it can be added to `.claude/mcp.json` with:

```json
{"command": "uvx", "args": ["math-compute-mcp"]}
```

No global install required.

## 7. Safe evaluation

User-supplied expressions are evaluated with one of:
- `RestrictedPython` — for SymPy/NumPy expressions where the full Python AST must be constrained
- Subprocess with timeout — for SageMath (which has its own process model anyway)
- A typed DSL parsed before any execution — for diagram descriptions

Direct `eval()` on unsanitized input is never used.

## 8. Tool docstrings are the interface

The docstring on each `@mcp.tool()` function is what Claude Code reads to decide whether and how to call the tool. It must:
- State what the tool does in one sentence
- Give at least one concrete input example
- State what the output format is
- Mention any required dependencies or API keys

## 9. No external mutation

Tools are read-only with respect to external systems. They may call read-only APIs (ArXiv, OEIS, MathWorld) but never POST, never write to databases, never mutate Lean4 files.

## 10. Independence

Each server in `servers/` is independently useful. Installing `math-compute` without `math-search` or Lean4 must work correctly. Inter-server dependencies are documented but optional.
