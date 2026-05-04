# Formal Verification

MCP servers for SMT solvers, model checkers, and formal methods tools beyond interactive proof assistants.

## SMT Solvers

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| Chiasmus | [yogthos/chiasmus](https://github.com/yogthos/chiasmus) | `z3_check`, Tau Prolog queries, tree-sitter code analysis | 2 | **Recommended.** Z3 via MCP is the most useful formal verification addition to a Lean4 workflow. Handles arithmetic, linear algebra, bit-vectors, array theories. |
| Chimera-Protocol | [mcp-research/Chimera-Protocol__csl-core](https://github.com/mcp-research/Chimera-Protocol__csl-core) | Z3 + TLA+ verification (TLA+ on roadmap) | 3 | Neuro-symbolic safety layer for AI agents. Z3 core is useful; TLA+ integration would add model checking. Heavier than Chiasmus. |

### Tool inventory: Chiasmus

11 tools spanning solver invocation, code analysis, and a template/skill library.

**Solver core:**
- `chiasmus_verify(solver, input, query?, format?, explain?)` — submit raw SMT-LIB or Prolog; returns sat/unsat/success, model or answers, unsat-core or derivation trace.
- `chiasmus_lint(spec, solver_type)` — fast structural validation of a spec without running the solver.

**Template / skill library:**
- `chiasmus_skills(query)` — search the template library for verification problem patterns.
- `chiasmus_formalize(problem)` — pick the best template for a problem, return slot-filling instructions.
- `chiasmus_solve(problem, context?)` — end-to-end: select template, fill slots, run verification with error-correction loops.
- `chiasmus_craft(name, domain, solver, signature, skeleton, slots, normalizations)` — author a new template.
- `chiasmus_learn(solution_context)` — promote reusable templates from verified solutions (after 3+ reuses).

**Code analysis (tree-sitter + Prolog):**
- `chiasmus_graph(files, analysis, target?, from?, to?, cache?, include_insights?)` — call-graph analyses: summary / callers / dead-code / cycles, etc.
- `chiasmus_map(files, mode?, format?, path?, name?, cache?)` — codebase outline (markdown or JSON: exports, imports, signatures, token estimates).
- `chiasmus_search(query, files, top_k)` — semantic code search; returns ranked function hits with file/line/signature/docs.
- `chiasmus_review(files, focus?, delta_against?)` — phased code-review recipe (no solver execution).

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
