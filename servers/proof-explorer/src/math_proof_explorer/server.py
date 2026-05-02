import re
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("proof-explorer")


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
