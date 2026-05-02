from math_compute.server import (
    batch_examples,
    sympy_diff,
    sympy_eval,
    sympy_expand,
    sympy_factor,
    sympy_integrate,
    sympy_solve,
    z3_check,
    oeis_lookup,
)


def test_sympy_eval_expand():
    result = sympy_eval("expand((x+1)**2)")
    assert "x**2 + 2*x + 1" in result
    assert "LaTeX" in result


def test_sympy_eval_simplify():
    result = sympy_eval("sin(x)**2 + cos(x)**2")
    assert "1" in result


def test_sympy_solve_quadratic():
    result = sympy_solve("x**2 - 5*x + 6", "x")
    assert "2" in result and "3" in result


def test_sympy_diff_product():
    result = sympy_diff("x**3", "x")
    assert "3*x**2" in result or "3x**2" in result


def test_sympy_integrate_definite():
    result = sympy_integrate("x**2", "x", "0", "1")
    assert "1/3" in result


def test_sympy_factor_polynomial():
    result = sympy_factor("x**3 - x")
    assert "x - 1" in result
    assert "x + 1" in result


def test_sympy_expand_product():
    result = sympy_expand("(x+y)**2")
    assert "x**2" in result


def test_batch_examples_triangular():
    result = batch_examples("n*(n+1)//2", "n", 0, 5)
    assert "n=   0: 0" in result
    assert "n=   5: 15" in result


def test_z3_check_unavailable_message():
    result = z3_check("x > 0 and x < 0", "x:Int")
    # Either z3 works and returns unsat, or it's not installed and returns a helpful message
    assert "unsat" in result or "z3-solver" in result
