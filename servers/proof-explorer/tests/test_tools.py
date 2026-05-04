import os
import tempfile
from pathlib import Path

import pytest
from math_proof_explorer.server import (
    _find_balanced_close,
    _find_lake_root,
    _find_theorem_binders,
    lean_minimal_hypotheses,
    sorry_map,
    tactic_history,
)

_LEAN_SRC = """\
theorem Nat.add_zero (n : Nat) : n + 0 = n := by
  sorry

theorem easy (n : Nat) : n = n := by
  rfl

theorem harder (n m : Nat) : n + m = m + n := by
  induction n with
  | zero => simp
  | succ k ih => sorry
"""


@pytest.fixture
def lean_file(tmp_path):
    p = tmp_path / "test.lean"
    p.write_text(_LEAN_SRC)
    return str(p)


def test_sorry_map_finds_two(lean_file):
    result = sorry_map(lean_file)
    assert "2 sorry" in result
    assert "Line" in result


def test_sorry_map_no_sorry():
    with tempfile.NamedTemporaryFile(suffix=".lean", mode="w", delete=False) as f:
        f.write("theorem trivial : True := trivial\n")
        tmp = f.name
    try:
        result = sorry_map(tmp)
        assert "No 'sorry' found" in result
    finally:
        os.unlink(tmp)


def test_sorry_map_missing_file():
    result = sorry_map("/nonexistent/path/file.lean")
    assert "not found" in result.lower()


def test_tactic_history_harder(lean_file):
    result = tactic_history(lean_file, "harder")
    assert "induction" in result
    assert "simp" in result


def test_tactic_history_missing_theorem(lean_file):
    result = tactic_history(lean_file, "nonexistent_theorem")
    assert "not found" in result.lower()


def test_find_balanced_close_simple():
    s = "((a)(b))"
    assert _find_balanced_close(s, 0, "(", ")") == 7
    assert _find_balanced_close(s, 1, "(", ")") == 3


def test_find_balanced_close_unbalanced():
    assert _find_balanced_close("(((a)", 0, "(", ")") == -1


def test_find_theorem_binders_explicit_and_implicit():
    src = (
        "theorem foo (h1 : P) (h2 : Q) {x : Nat} [DecidableEq α] : R := by\n"
        "  exact h1\n"
    )
    binders = _find_theorem_binders(src, "foo")
    texts = [b[0] for b in binders]
    assert texts == ["(h1 : P)", "(h2 : Q)", "{x : Nat}", "[DecidableEq α]"]


def test_find_theorem_binders_no_binders():
    src = "theorem trivial : True := trivial\n"
    assert _find_theorem_binders(src, "trivial") == []


def test_find_theorem_binders_unknown_name():
    src = "theorem foo (h : P) : Q := sorry\n"
    assert _find_theorem_binders(src, "bar") == []


def test_find_theorem_binders_nested_parens():
    src = "theorem foo (h : P → (Q ∧ R)) (k : S) : T := sorry\n"
    binders = [b[0] for b in _find_theorem_binders(src, "foo")]
    assert binders == ["(h : P → (Q ∧ R))", "(k : S)"]


def test_find_lake_root_walks_up(tmp_path):
    project = tmp_path / "myproj"
    project.mkdir()
    (project / "lakefile.lean").write_text("")
    sub = project / "src" / "deep"
    sub.mkdir(parents=True)
    assert _find_lake_root(sub) == project.resolve()


def test_find_lake_root_none(tmp_path):
    sub = tmp_path / "no_lake_here"
    sub.mkdir()
    assert _find_lake_root(sub) is None


def test_lean_minimal_hypotheses_missing_file():
    out = lean_minimal_hypotheses("/nonexistent/foo.lean", "thm")
    assert "not found" in out.lower()


def test_lean_minimal_hypotheses_no_binders(tmp_path):
    p = tmp_path / "trivial.lean"
    p.write_text("theorem trivial : True := trivial\n")
    out = lean_minimal_hypotheses(str(p), "trivial")
    assert "no binders" in out.lower() or "No explicit" in out


def test_lean_minimal_hypotheses_formatting(tmp_path, monkeypatch):
    p = tmp_path / "demo.lean"
    p.write_text("theorem foo (h1 : True) (h2 : True) : True := by exact h1\n")

    # First hyp needed (h1 referenced); second hyp removable
    def fake_compile(file_path, lake_root, timeout):
        text = Path(file_path).read_text()
        # If the h1 binder is missing, body fails (still references h1)
        if "(h1 :" not in text:
            return False, "error: unknown identifier 'h1'"
        # If h2's binder is missing, body still works
        return True, ""

    monkeypatch.setattr(
        "math_proof_explorer.server._compile_lean",
        fake_compile,
    )

    out = lean_minimal_hypotheses(str(p), "foo")
    assert "load-bearing" in out
    assert "removable" in out
    assert "(h1 : True)" in out
    assert "(h2 : True)" in out
    assert "Summary: 1 load-bearing, 1 removable" in out
