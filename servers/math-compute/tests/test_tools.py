from math_compute.server import (
    batch_examples,
    conjecture_test,
    find_counterexample,
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


def test_conjecture_test_holds_for_triangular_identity():
    result = conjecture_test(
        "Eq((n*(n+1))/2, n + n*(n-1)/2)",
        {"n": "int 0 1000"},
        n_samples=30,
        seed=0,
    )
    assert "Verified" in result


def test_conjecture_test_finds_counterexample_to_strict_positive_square():
    # 0 is in the sampling range and breaks x**2 > 0
    result = conjecture_test("x**2 > 0", {"x": "int -5 5"}, n_samples=200, seed=1)
    assert "Counterexample" in result
    assert "x=0" in result


def test_conjecture_test_unbound_symbol_errors_clearly():
    result = conjecture_test("x + y > 0", {"x": "int 0 10"}, n_samples=10)
    assert "unbound free symbols" in result
    assert "y" in result


def test_conjecture_test_choice_spec():
    result = conjecture_test("Eq(x*x, x)", {"x": "choice 0 1"}, n_samples=30, seed=0)
    assert "Verified" in result


def test_find_counterexample_breaks_false_claim_quickly():
    result = find_counterexample("Eq(n**2, 2*n)", domain="integers", max_size=5)
    assert "Counterexample" in result


def test_find_counterexample_holds_on_integers():
    # n*(n+1) is always even
    result = find_counterexample("Eq((n*(n+1)) % 2, 0)", domain="integers", max_size=10)
    assert "No counterexample" in result


def test_find_counterexample_unknown_domain():
    result = find_counterexample("x > 0", domain="bogus")
    assert "Unknown domain" in result


def test_find_counterexample_caps_search_space():
    # 4 free vars × ~21 values = ~194k > default 5000
    result = find_counterexample("Eq(a + b + c + d, 0)", domain="integers", max_size=10)
    assert "search space" in result
    assert "max_total" in result
