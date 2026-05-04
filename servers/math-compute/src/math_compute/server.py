import ast
import itertools
import random
import textwrap
from typing import Any, Iterable

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


def _sampler_from_spec(spec: str):
    """Compile a string DSL like 'int 1 100' into a 0-arg sampler that yields a sympy value.

    Grammar:
      'int low high'      — uniform integer in [low, high]
      'real low high'     — uniform float in [low, high]
      'prime low high'    — uniform prime in [low, high]
      'choice v1 v2 …'    — uniform pick from the listed sympy values
    """
    parts = spec.strip().split()
    if not parts:
        raise ValueError(f"empty variable spec")
    kind = parts[0]
    if kind == "int" and len(parts) == 3:
        lo, hi = int(parts[1]), int(parts[2])
        return lambda: sympy.Integer(random.randint(lo, hi))
    if kind == "real" and len(parts) == 3:
        lo, hi = float(parts[1]), float(parts[2])
        return lambda: sympy.Float(random.uniform(lo, hi))
    if kind == "prime" and len(parts) == 3:
        lo, hi = int(parts[1]), int(parts[2])
        primes = list(sympy.primerange(lo, hi + 1))
        if not primes:
            raise ValueError(f"no primes in [{lo}, {hi}]")
        return lambda: sympy.Integer(random.choice(primes))
    if kind == "choice" and len(parts) >= 2:
        choices = [_parse(p) for p in parts[1:]]
        return lambda: random.choice(choices)
    raise ValueError(
        f"bad spec '{spec}'. Expected 'int LO HI', 'real LO HI', 'prime LO HI', or 'choice V1 V2 …'"
    )


def _truth_value(expr: sympy.Expr) -> bool | None:
    """Reduce a fully-substituted sympy expression to True/False if possible."""
    try:
        simp = sympy.simplify(expr)
    except Exception:
        simp = expr
    if simp is sympy.S.true:
        return True
    if simp is sympy.S.false:
        return False
    if isinstance(simp, sympy.logic.boolalg.BooleanTrue):
        return True
    if isinstance(simp, sympy.logic.boolalg.BooleanFalse):
        return False
    return None


@mcp.tool()
def conjecture_test(
    claim: str,
    variables: dict[str, str],
    n_samples: int = 200,
    seed: int = 0,
) -> str:
    """Stress-test a conjecture by random sampling. Returns the first counterexample
    found, or 'verified for N samples' if none.

    claim: a sympy expression that should evaluate to True. Use Eq(a, b) for equality,
           and <, <=, >, >= for inequalities. Combine with And(...), Or(...), Not(...).
    variables: dict mapping each free variable to a sampling spec string. Specs:
        'int LO HI'      uniform integer
        'real LO HI'     uniform float
        'prime LO HI'    uniform prime
        'choice V1 V2 …' uniform pick from listed values

    Examples:
      claim='Eq((n*(n+1))/2, n + n*(n-1)/2)', variables={'n': 'int 0 1000'}
      claim='x**2 >= 0', variables={'x': 'real -1000 1000'}
      claim='Eq(p % 2, 1)', variables={'p': 'prime 3 1000'}  (false: p=2 excluded by spec — but also p=2 is even)
    """
    try:
        expr = _parse(claim)
    except Exception as e:
        return f"Error parsing claim: {e}"
    try:
        samplers = {name: _sampler_from_spec(spec) for name, spec in variables.items()}
    except ValueError as e:
        return f"Error: {e}"

    free_syms = {str(s) for s in expr.free_symbols}
    missing = free_syms - set(samplers)
    if missing:
        return f"Claim has unbound free symbols: {sorted(missing)}. Add them to `variables`."

    random_state = random.getstate()
    random.seed(seed)
    try:
        indeterminate = 0
        passed = 0
        for i in range(int(n_samples)):
            assignment = {sympy.Symbol(name): sampler() for name, sampler in samplers.items()}
            try:
                substituted = expr.subs(assignment)
            except Exception as e:
                return f"Error substituting at sample {i + 1}: {e}"
            tv = _truth_value(substituted)
            if tv is False:
                pretty_assign = ", ".join(f"{k}={v}" for k, v in assignment.items())
                return (
                    f"Counterexample at sample {i + 1} (seed={seed}): {pretty_assign}\n"
                    f"  claim:        {claim}\n"
                    f"  substituted:  {substituted}"
                )
            if tv is True:
                passed += 1
            else:
                indeterminate += 1
    finally:
        random.setstate(random_state)

    if passed == 0 and indeterminate > 0:
        return (
            f"Indeterminate for all {n_samples} samples — sympy could not decide "
            f"the truth value. Try a more concrete formulation (e.g. wrap with Eq, "
            f"or pick narrower variable ranges)."
        )
    suffix = f" ({indeterminate} indeterminate)" if indeterminate else ""
    return f"Verified: {passed}/{n_samples} samples held{suffix}. (seed={seed})"


def _enum_naturals(max_size: int) -> list[sympy.Expr]:
    return [sympy.Integer(n) for n in range(max_size + 1)]


def _enum_integers(max_size: int) -> list[sympy.Expr]:
    return [sympy.Integer(n) for n in range(-max_size, max_size + 1)]


def _enum_rationals(max_size: int) -> list[sympy.Expr]:
    seen = set()
    out: list[sympy.Expr] = []
    for q in range(1, max_size + 1):
        for p in range(-max_size, max_size + 1):
            r = sympy.Rational(p, q)
            if r not in seen:
                seen.add(r)
                out.append(r)
    return out


def _enum_polynomials_1var(max_size: int, var: str = "x") -> list[sympy.Expr]:
    """Polynomials in `var` of degree ≤ 3 with integer coefficients in [-max_size, max_size]."""
    x = sympy.Symbol(var)
    out: list[sympy.Expr] = []
    rng = range(-max_size, max_size + 1)
    for c0 in rng:
        for c1 in rng:
            for c2 in rng:
                for c3 in rng:
                    out.append(sympy.expand(c0 + c1 * x + c2 * x**2 + c3 * x**3))
    # de-duplicate (low-degree polys with leading 0 collapse)
    seen = set()
    uniq: list[sympy.Expr] = []
    for p in out:
        key = sympy.srepr(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


_DOMAINS = {
    "naturals": _enum_naturals,
    "integers": _enum_integers,
    "rationals": _enum_rationals,
    "polynomials_1var": _enum_polynomials_1var,
}


@mcp.tool()
def find_counterexample(
    claim: str,
    domain: str = "integers",
    max_size: int = 10,
    max_total: int = 5000,
) -> str:
    """Search for a counterexample to a claim by exhaustively enumerating values
    from a structured domain. Returns the first failing assignment, or
    'no counterexample found in N candidates'.

    domain: 'naturals', 'integers', 'rationals', or 'polynomials_1var'.
      For polynomials_1var, the free symbol in the claim is substituted by
      polynomials in 'x' of degree ≤ 3 with integer coefficients in [-max_size, max_size].
    max_size: range bound (used differently per domain).
    max_total: hard cap on the number of substitutions tried (cartesian-product can blow up).

    Example:
      claim='Eq(x*(x+1) % 2, 0)', domain='integers', max_size=20
      claim='(p**2).is_nonnegative', domain='polynomials_1var', max_size=2
    """
    if domain not in _DOMAINS:
        return f"Unknown domain '{domain}'. Allowed: {sorted(_DOMAINS)}"

    try:
        expr = _parse(claim)
    except Exception as e:
        return f"Error parsing claim: {e}"

    free_syms = sorted(expr.free_symbols, key=lambda s: s.name)
    if not free_syms:
        tv = _truth_value(expr)
        if tv is False:
            return f"Claim is identically false (no free symbols): {claim}"
        if tv is True:
            return f"Claim is identically true (no free symbols): {claim}"
        return f"Claim has no free symbols and is indeterminate: {claim}"

    values = _DOMAINS[domain](max_size)
    if not values:
        return f"Domain '{domain}' yielded no values for max_size={max_size}."

    # Cartesian product, capped at max_total
    n_vars = len(free_syms)
    total = len(values) ** n_vars
    if total > max_total:
        return (
            f"Domain '{domain}' yields {len(values)} values per variable; with "
            f"{n_vars} free variables the search space is {total} > max_total={max_total}. "
            f"Reduce max_size or fix some variables before calling."
        )

    tried = 0
    indeterminate = 0
    for combo in itertools.product(values, repeat=n_vars):
        assignment = dict(zip(free_syms, combo))
        try:
            substituted = expr.subs(assignment)
        except Exception:
            continue
        tv = _truth_value(substituted)
        tried += 1
        if tv is False:
            pretty_assign = ", ".join(f"{k}={v}" for k, v in assignment.items())
            return (
                f"Counterexample after {tried} candidates: {pretty_assign}\n"
                f"  claim:        {claim}\n"
                f"  substituted:  {substituted}"
            )
        if tv is None:
            indeterminate += 1

    suffix = f" ({indeterminate} indeterminate)" if indeterminate else ""
    return f"No counterexample found in {tried} candidates from '{domain}' (max_size={max_size}){suffix}."


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
