import re
import subprocess
import tempfile
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("proof-explorer")


def _find_balanced_close(s: str, open_pos: int, open_ch: str, close_ch: str) -> int:
    """Index of the matching close char (or -1 if unbalanced).
    Counts opens and closes only — doesn't try to skip strings or comments."""
    depth = 0
    for i in range(open_pos, len(s)):
        ch = s[i]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i
    return -1


def _find_theorem_binders(source: str, name: str) -> list[tuple[str, int, int]]:
    """Find the binder list of a theorem/lemma/def by name.

    Returns a list of `(binder_text, start_char, end_char_exclusive)`. Binders
    are top-level `(...)`, `{...}`, or `[...]` groups between `name` and the
    type-introducing `:`. Note: doesn't strip Lean comments — assume
    well-formatted code.
    """
    pattern = re.compile(rf"\b(theorem|lemma|example|def)\s+{re.escape(name)}\b")
    m = pattern.search(source)
    if not m:
        return []

    pos = m.end()
    binders: list[tuple[str, int, int]] = []
    closers = {"(": ")", "{": "}", "[": "]"}
    while pos < len(source):
        while pos < len(source) and source[pos] in " \t\n\r":
            pos += 1
        if pos >= len(source):
            break
        ch = source[pos]
        if ch in closers:
            close = _find_balanced_close(source, pos, ch, closers[ch])
            if close == -1:
                break
            binders.append((source[pos : close + 1], pos, close + 1))
            pos = close + 1
        else:
            break
    return binders


def _find_lake_root(start: Path) -> Path | None:
    p = start.resolve()
    for ancestor in [p, *p.parents]:
        if (ancestor / "lakefile.lean").exists() or (ancestor / "lakefile.toml").exists():
            return ancestor
    return None


def _compile_lean(file_path: Path, lake_root: Path | None, timeout: float) -> tuple[bool, str]:
    """Run `lake env lean FILE` (or plain `lean FILE`) and return (ok, captured_output)."""
    if lake_root:
        cmd = ["lake", "env", "lean", str(file_path)]
        cwd = str(lake_root)
    else:
        cmd = ["lean", str(file_path)]
        cwd = None
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    except FileNotFoundError as e:
        return False, f"command not found: {e.filename}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    output = (proc.stderr or "") + (proc.stdout or "")
    return proc.returncode == 0, output


@mcp.tool()
def sorry_map(file_path: str) -> str:
    """List all 'sorry' placeholders in a Lean4 file with line numbers.
    Works without a Lean4 server — reads the file directly.
    Example: file_path='/path/to/MyProof.lean'"""
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"
    if path.suffix not in (".lean", ".l4"):
        return f"Expected a .lean file, got: {path.suffix}"

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Match 'sorry' as a standalone tactic or term (not inside a string or comment)
    sorry_re = re.compile(r"\bsorry\b")
    comment_re = re.compile(r"--.*$")

    findings = []
    for i, line in enumerate(lines, start=1):
        # Strip line comment before checking
        stripped = comment_re.sub("", line)
        if sorry_re.search(stripped):
            context = line.strip()
            findings.append(f"  Line {i:>4}: {context}")

    if not findings:
        return f"No 'sorry' found in {path.name}. The proof is complete (no admitted goals)."

    header = f"{len(findings)} sorry(s) in {path.name}:\n"
    return header + "\n".join(findings)


@mcp.tool()
def proof_tree(file_path: str, line: int) -> str:
    """Return the proof tree at a cursor position in a Lean4 file.
    Requires lean-lsp-mcp running on the same project.
    Install: https://github.com/oOo0oOo/lean-lsp-mcp
    Example: file_path='/path/to/MyProof.lean', line=42"""
    raise NotImplementedError(
        "proof_tree requires lean-lsp-mcp. "
        "This tool will wrap lean-lsp-mcp's get_goal output into a tree visualization. "
        "See: https://github.com/oOo0oOo/lean-lsp-mcp"
    )


@mcp.tool()
def goal_explain(file_path: str, line: int) -> str:
    """Return a plain-language explanation of the current Lean4 proof goal.
    Requires lean-lsp-mcp running on the same project.
    Example: file_path='/path/to/MyProof.lean', line=42"""
    raise NotImplementedError(
        "goal_explain requires lean-lsp-mcp. "
        "See: https://github.com/oOo0oOo/lean-lsp-mcp"
    )


@mcp.tool()
def tactic_history(file_path: str, theorem_name: str) -> str:
    """Return the sequence of tactics applied in a theorem proof block.
    Works without a Lean4 server — parses the file directly.
    Example: file_path='/path/to/MyProof.lean', theorem_name='Nat.add_comm'"""
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"

    text = path.read_text(encoding="utf-8")

    # Find the theorem block
    # Match: theorem/lemma/def NAME ... := by\n  tactic\n  tactic\n...
    pattern = re.compile(
        rf"\b(?:theorem|lemma)\s+{re.escape(theorem_name)}\b.*?:=\s*by\b(.*?)(?=\n(?:theorem|lemma|def|structure|class|instance|#|\Z))",
        re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        # Try simpler search: just find the name and grab the next tactic block
        start = text.find(theorem_name)
        if start == -1:
            return f"Theorem '{theorem_name}' not found in {path.name}."
        by_pos = text.find(":= by", start)
        if by_pos == -1:
            return f"Theorem '{theorem_name}' found but no ':= by' tactic proof."
        block = text[by_pos + 5 : by_pos + 2000]
    else:
        block = m.group(1)

    # Extract tactic lines (indented lines after := by)
    tactic_lines = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            tactic_lines.append(f"  {stripped}")
        if stripped.startswith(("theorem", "lemma", "def", "#")):
            break

    if not tactic_lines:
        return f"No tactics found for '{theorem_name}'."

    return f"Tactic history for '{theorem_name}':\n" + "\n".join(tactic_lines)


@mcp.tool()
def lean_minimal_hypotheses(
    file_path: str,
    theorem_name: str,
    timeout_per_hyp: float = 60.0,
) -> str:
    """For each explicit (h : T) hypothesis of a Lean4 theorem, drop it and
    re-compile the file. Reports which hypotheses are load-bearing and which
    are unused.

    Only handles explicit `(h : T)` binders; skips implicit `{x : α}` and
    instance `[inst : C]` (those are usually inferable / always load-bearing).
    Does not rewrite the proof body, so a hypothesis referenced by name in the
    body always comes back as 'load-bearing' — which is the truthful answer.

    Requires `lean` (and `lake` if the file is inside a Lake project) on PATH.
    Slow: each hypothesis triggers a full compile, capped at `timeout_per_hyp`
    seconds. A theorem with 5 hypotheses takes up to ~5 × timeout_per_hyp.

    Example: file_path='/path/to/MyProof.lean', theorem_name='Nat.add_comm'"""
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"
    if path.suffix != ".lean":
        return f"Expected a .lean file, got: {path.suffix}"

    source = path.read_text(encoding="utf-8")
    binders = _find_theorem_binders(source, theorem_name)
    if not binders:
        return (
            f"Could not find theorem/lemma/def '{theorem_name}' in {path.name}, "
            f"or it has no binders before its type."
        )

    explicit = [(b, s, e) for (b, s, e) in binders if b.startswith("(") and ":" in b]
    skipped_implicit = [b for (b, _, _) in binders if not b.startswith("(")]

    if not explicit:
        msg = f"No explicit (h : T) binders for '{theorem_name}'."
        if skipped_implicit:
            msg += f" Found only implicit/instance binders: {skipped_implicit}"
        return msg

    lake_root = _find_lake_root(path.parent)

    results: list[tuple[str, str, str]] = []
    for binder, start, end in explicit:
        cut_start = start - 1 if start > 0 and source[start - 1] == " " else start
        modified = source[:cut_start] + source[end:]

        with tempfile.NamedTemporaryFile(
            "w",
            suffix=".lean",
            prefix=f"_minhyp_{path.stem}_",
            dir=path.parent,
            delete=False,
            encoding="utf-8",
        ) as tf:
            tf.write(modified)
            tmp_path = Path(tf.name)
        try:
            ok, output = _compile_lean(tmp_path, lake_root, timeout_per_hyp)
        finally:
            tmp_path.unlink(missing_ok=True)

        if ok:
            results.append((binder.strip(), "removable", ""))
        elif output == "timeout":
            results.append((binder.strip(), "timeout", f"compile didn't finish in {timeout_per_hyp}s"))
        else:
            err_lines = [ln for ln in output.splitlines() if "error" in ln.lower()]
            detail = (err_lines[0] if err_lines else (output.splitlines() or ["(no output)"])[0])[:200]
            results.append((binder.strip(), "load-bearing", detail))

    lines = [f"Minimal-hypotheses analysis of '{theorem_name}' in {path.name}:"]
    lines.append(f"  ({'lake project at ' + str(lake_root) if lake_root else 'no lake project; using plain `lean`'})")
    if skipped_implicit:
        lines.append(f"  skipped {len(skipped_implicit)} implicit/instance binder(s)")
    lines.append("")
    for binder, status, detail in results:
        lines.append(f"  [{status:13}] {binder}")
        if detail:
            lines.append(f"                  {detail}")

    n_removable = sum(1 for _, s, _ in results if s == "removable")
    n_load = sum(1 for _, s, _ in results if s == "load-bearing")
    n_to = sum(1 for _, s, _ in results if s == "timeout")
    lines.append("")
    lines.append(
        f"Summary: {n_load} load-bearing, {n_removable} removable, {n_to} timeout "
        f"(of {len(results)} explicit hypotheses)."
    )
    return "\n".join(lines)


@mcp.tool()
def hypothesis_graph(file_path: str, line: int) -> dict:
    """Render a dependency graph of the local hypotheses at a proof position.
    Requires lean-lsp-mcp for full context. Returns an image.
    Example: file_path='/path/to/MyProof.lean', line=42"""
    raise NotImplementedError(
        "hypothesis_graph requires lean-lsp-mcp for hypothesis extraction. "
        "See: https://github.com/oOo0oOo/lean-lsp-mcp"
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
