import os
import tempfile
import pytest
from math_proof_explorer.server import sorry_map, tactic_history

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
