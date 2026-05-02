import ast
import textwrap
from typing import Any

import httpx
import sympy
from fastmcp import FastMCP
from sympy import latex, pretty
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

mcp = FastMCP("math-compute")

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

# Safe SymPy namespace: all public SymPy names + common single-letter symbols
_SYMPY_NS: dict[str, Any] = {
    name: getattr(sympy, name)
    for name in dir(sympy)
    if not name.startswith("_")
}
_SYMPY_NS.update(
    {
        name: sympy.Symbol(name)
        for name in list("xyzabnmkstuvwpqr")
        + ["alpha", "beta", "gamma", "delta", "epsilon", "theta",
           "lam", "mu", "nu", "xi", "rho", "sigma", "tau", "phi", "psi", "omega"]
    }
)
# Remove anything that could be dangerous
for _bad in ("eval", "exec", "compile", "open", "__import__", "input"):
    _SYMPY_NS.pop(_bad, None)


def _parse(expr_str: str) -> sympy.Expr:
    return parse_expr(expr_str, local_dict=_SYMPY_NS, transformations=_TRANSFORMATIONS)


def _fmt(expr: sympy.Expr) -> str:
    return f"{expr}\nLaTeX: {latex(expr)}"


@mcp.tool()
def sympy_eval(expression: str) -> str:
    """Evaluate and simplify a SymPy expression. Returns the result and its LaTeX form.
    Example: 'expand((x+1)**3)' or 'simplify(sin(x)**2 + cos(x)**2)'"""
    try:
        result = _parse(expression)
        # Try to simplify if it's not already a simplified call
        if not any(expression.startswith(fn) for fn in ("expand", "factor", "simplify", "cancel")):
            result = sympy.simplify(result)
        return _fmt(result)
    except Exception as e:
        return f"Error: {e}\nHint: use Python syntax, e.g. x**2 not x^2, and * for multiplication."


@mcp.tool()
def sympy_solve(equations: str, variables: str = "x") -> str:
    """Solve one or more equations symbolically.
    equations: comma-separated equations (use '=' for equality or expressions equal to 0).
    variables: comma-separated variable names to solve for.
    Example: equations='x**2 - 5*x + 6', variables='x'
    Example: equations='x + y - 3, x - y - 1', variables='x, y'"""
    try:
        var_names = [v.strip() for v in variables.split(",")]
        vars_ = [_parse(v) for v in var_names]

        eq_strs = [e.strip() for e in equations.split(",")]
        eqs = []
        for s in eq_strs:
            if "=" in s:
                lhs, rhs = s.split("=", 1)
                eqs.append(sympy.Eq(_parse(lhs), _parse(rhs)))
            else:
                eqs.append(_parse(s))

        solution = sympy.solve(eqs, vars_ if len(vars_) > 1 else vars_[0])

        if not solution:
            return "No solution found."
        if isinstance(solution, dict):
            parts = [f"{k} = {v}  (LaTeX: ${latex(v)}$)" for k, v in solution.items()]
            return "\n".join(parts)
        if isinstance(solution, list):
            if solution and isinstance(solution[0], tuple):
                rows = []
                for sol in solution:
                    row = ", ".join(f"{var_names[i]} = {v}" for i, v in enumerate(sol))
                    rows.append(row)
                return "\n".join(rows)
            return "\n".join(f"{var_names[0]} = {v}  (LaTeX: ${latex(v)}$)" for v in solution)
        return str(solution)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def sympy_diff(expression: str, variable: str = "x", order: int = 1) -> str:
    """Differentiate an expression with respect to a variable.
    Example: expression='sin(x)*exp(x)', variable='x', order=2"""
    try:
        expr = _parse(expression)
        var = _parse(variable)
        result = sympy.diff(expr, var, order)
        return _fmt(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def sympy_integrate(expression: str, variable: str = "x", lower: str = "", upper: str = "") -> str:
    """Integrate an expression. Omit lower/upper for indefinite integral.
    Example (definite): expression='x**2', variable='x', lower='0', upper='1'
    Example (indefinite): expression='exp(-x**2)', variable='x'"""
    try:
        expr = _parse(expression)
        var = _parse(variable)
        if lower and upper:
            lo = _parse(lower)
            hi = _parse(upper)
            result = sympy.integrate(expr, (var, lo, hi))
        else:
            result = sympy.integrate(expr, var)
        return _fmt(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def sympy_factor(expression: str, domain: str = "ZZ") -> str:
    """Factor a polynomial expression over a ring.
    domain: 'ZZ' (integers, default), 'QQ' (rationals), 'RR' (reals), 'CC' (complex).
    Example: expression='x**3 - x', domain='ZZ'"""
    try:
        expr = _parse(expression)
        if domain == "ZZ":
            result = sympy.factor(expr)
        elif domain == "QQ":
            result = sympy.factor(expr, domain="QQ")
        elif domain in ("RR", "CC"):
            result = sympy.factor(expr, extension=True)
        else:
            result = sympy.factor(expr)
        return _fmt(result)
    except Exception as e:
        return f"Error: {e}\nHint: for irreducible polynomials over ZZ, try domain='QQ' or 'CC'."


@mcp.tool()
def sympy_expand(expression: str) -> str:
    """Expand a product, power, or trigonometric expression.
    Example: 'expand((x+y+z)**2)' or 'expand_trig(sin(x+y))'"""
    try:
        result = _parse(expression)
        # If no explicit expand call, apply expand
        if not expression.startswith("expand"):
            result = sympy.expand(result)
        return _fmt(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def batch_examples(expression: str, variable: str, start: int, end: int) -> str:
    """Evaluate a SymPy expression for a range of integer values of a variable.
    Useful for finding patterns and formulating conjectures.
    Example: expression='n*(n+1)//2', variable='n', start=0, end=10"""
    try:
        expr = _parse(expression)
        var = sympy.Symbol(variable)
        rows = []
        for n in range(start, end + 1):
            val = expr.subs(var, n)
            try:
                val = sympy.Integer(val) if val == int(val) else val.evalf(6)
            except Exception:
                pass
            rows.append(f"  {variable}={n:>4}: {val}")
        header = f"Evaluating  {expression}  for {variable} in [{start}, {end}]:\n"
        return header + "\n".join(rows)
    except Exception as e:
        return f"Error: {e}"


class _BoolToZ3(ast.NodeTransformer):
    """Transform Python and/or/not into Z3 And/Or/Not calls."""

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        fn = "And" if isinstance(node.op, ast.And) else "Or"
        return ast.Call(
            func=ast.Name(id=fn, ctx=ast.Load()),
            args=node.values,
            keywords=[],
        )

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.op, ast.Not):
            return ast.Call(
                func=ast.Name(id="Not", ctx=ast.Load()),
                args=[node.operand],
                keywords=[],
            )
        return node


@mcp.tool()
def z3_check(formula: str, variables: str = "") -> str:
    """Check satisfiability of a logical formula using Z3.
    variables: 'name:Type' pairs, comma-separated. Types: Int, Real, Bool.
    formula: Python expression using Z3 operators. Use And/Or/Not or Python and/or/not.
    Returns 'sat' + a model, 'unsat', or 'unknown'.
    Example: formula='x > 0 and x**2 < 4', variables='x:Real'
    Example: formula='And(x >= 0, x + y == 10, y >= 0)', variables='x:Int, y:Int'"""
    try:
        import z3
    except ImportError:
        return "z3-solver is not installed. Run: pip install z3-solver"

    try:
        var_map: dict[str, Any] = {}
        for decl in variables.split(","):
            decl = decl.strip()
            if not decl:
                continue
            name, _, typ = (decl + ":Int").partition(":")
            name, typ = name.strip(), typ.strip()
            if typ == "Real":
                var_map[name] = z3.Real(name)
            elif typ == "Bool":
                var_map[name] = z3.Bool(name)
            else:
                var_map[name] = z3.Int(name)

        ns: dict[str, Any] = {
            **var_map,
            "And": z3.And, "Or": z3.Or, "Not": z3.Not,
            "Implies": z3.Implies, "If": z3.If,
            "ForAll": z3.ForAll, "Exists": z3.Exists,
            "True": True, "False": False,
        }

        # Transform Python and/or/not to Z3 And/Or/Not
        tree = ast.parse(formula, mode="eval")
        tree = _BoolToZ3().visit(tree)
        ast.fix_missing_locations(tree)
        constraint = eval(compile(tree, "<z3_formula>", "eval"), {"__builtins__": {}}, ns)

        solver = z3.Solver()
        solver.add(constraint)
        result = solver.check()

        if result == z3.sat:
            model = solver.model()
            model_str = ", ".join(f"{d} = {model[d]}" for d in model)
            return f"sat\nModel: {model_str}"
        elif result == z3.unsat:
            return "unsat (the formula has no solution)"
        else:
            return "unknown (Z3 could not decide)"

    except Exception as e:
        return f"Error: {e}\nHint: declare variables like 'x:Int, y:Real'. Use ** for powers."


@mcp.tool()
def oeis_lookup(sequence: str) -> str:
    """Look up an integer sequence on OEIS by A-number or comma-separated terms.
    Example: sequence='A000045' (Fibonacci) or sequence='1,1,2,3,5,8,13'"""
    sequence = sequence.strip()
    with httpx.Client(timeout=15) as client:
        if sequence.upper().startswith("A"):
            r = client.get(
                "https://oeis.org/search",
                params={"q": sequence.upper(), "fmt": "json"},
                headers={"User-Agent": "math-reasoning-tools/0.1"},
            )
        else:
            r = client.get(
                "https://oeis.org/search",
                params={"q": sequence, "fmt": "json"},
                headers={"User-Agent": "math-reasoning-tools/0.1"},
            )
    r.raise_for_status()

    data = r.json()
    results = data.get("results") or []
    if not results:
        return f"No OEIS sequence found for '{sequence}'."

    seq = results[0]
    a_num = f"A{seq.get('number', 0):06d}"
    name = seq.get("name", "")
    values = seq.get("data", "").split(",")[:20]
    formulas = seq.get("formula", [])[:2]
    comments = seq.get("comment", [])[:2]

    parts = [
        f"**{a_num}**: {name}",
        f"Terms: {', '.join(values)}{'...' if len(values) == 20 else ''}",
        f"https://oeis.org/{a_num}",
    ]
    if formulas:
        parts.append("Formulas:\n" + "\n".join(f"  {f[:200]}" for f in formulas))
    if comments:
        parts.append("Comments:\n" + "\n".join(f"  {c[:200]}" for c in comments))

    return "\n".join(parts)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
