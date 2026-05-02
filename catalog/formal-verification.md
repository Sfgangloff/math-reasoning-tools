# Formal Verification

MCP servers for SMT solvers, model checkers, and formal methods tools beyond interactive proof assistants.

## SMT Solvers

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| Chiasmus | [yogthos/chiasmus](https://github.com/yogthos/chiasmus) | `z3_check`, Tau Prolog queries, tree-sitter code analysis | 2 | **Recommended.** Z3 via MCP is the most useful formal verification addition to a Lean4 workflow. Handles arithmetic, linear algebra, bit-vectors, array theories. |
| Chimera-Protocol | [mcp-research/Chimera-Protocol__csl-core](https://github.com/mcp-research/Chimera-Protocol__csl-core) | Z3 + TLA+ verification (TLA+ on roadmap) | 3 | Neuro-symbolic safety layer for AI agents. Z3 core is useful; TLA+ integration would add model checking. Heavier than Chiasmus. |

## Code Verification

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| formal-verification-skills | [Beneficial-AI-Foundation/formal-verification-skills](https://github.com/Beneficial-AI-Foundation/formal-verification-skills) | Rust formal verification with AI-assisted specification | 3 | Specific to Rust + formal spec generation. Not general math, but interesting for verified software. |
| SkillFortify | [qualixar/skillfortify](https://github.com/qualixar/skillfortify) | Security scanning for AI skills (22 frameworks) | 2 | Meta-tool: formal scanning of MCP/LangChain/CrewAI agent definitions. Not math per se. |

## Gaps

- **TLA+**: no standalone MCP server. The Chimera-Protocol roadmap mentions it but it is not yet implemented.
- **Alloy**: no MCP server (Alloy Analyzer is useful for relational/structural reasoning).
- **Why3**: no MCP server (Why3 sits between SMT and interactive provers, useful for verified algorithms).
- **Lean4 ↔ Z3 bridge**: Lean4 has `Std.Tactic.BVDecide` and the `polyrith` tactic which call external solvers internally, but no MCP tool exposes this interface directly.

## Notes

- **Z3 is the most immediately useful** formal verification tool in a theorem proving workflow. It handles: linear arithmetic over ℤ and ℚ, polynomial arithmetic (nonlinear with limitations), propositional logic, first-order logic in decidable fragments, bit-vector arithmetic.
- For goals that look like they might be in a decidable fragment, try `z3_check` before spending time on a manual Lean4 proof. If Z3 confirms it, you can use `native_decide` or `omega` in Lean4.
- The `math-compute` server in this repo includes a `z3_check` tool wrapping `z3-solver` (the Python bindings).
