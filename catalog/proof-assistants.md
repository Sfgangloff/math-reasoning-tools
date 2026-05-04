# Proof Assistants

MCP servers and tools for interacting with formal proof assistants.

## Lean4

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| lean-lsp-mcp | [oOo0oOo/lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp) | `check_file`, `get_goal`, `lean_search`, `loogle`, `lean_hammer`, `lean_state_search` | 3 (requires Lean4 + Mathlib) | **Primary recommendation.** Best Lean4 MCP tool available. LSP integration + semantic search. Actively maintained. Also mirrored at [project-numina/lean-lsp-mcp](https://github.com/project-numina/lean-lsp-mcp). |
| lean-aristotle-mcp | [septract/lean-aristotle-mcp](https://github.com/septract/lean-aristotle-mcp) | `aristotle_prove` | 4 (requires Harmonic Aristotle) | Wraps Harmonic's ATP for Lean4. Good for auto-closing goals that `aesop`/`decide` cannot handle. Requires separate Aristotle install. |
| lean4-skills | [cameronfreer/lean4-skills](https://github.com/cameronfreer/lean4-skills) | Claude Code skill pack (not MCP tools) | 2 | Prove/review/golf loop as Claude Code skills rather than MCP tools. Complements lean-lsp-mcp. |
| lean-agentic | [agenticsorg/lean-agentic](https://github.com/agenticsorg/lean-agentic) | Hybrid Lean4/agent orchestration | 4 | Experimental. Interesting architecture but low activity. |

### Tool inventory: lean-lsp-mcp

22 tools, grouped by role.

**File interactions (LSP-driven, position-based):**
- `lean_file_outline(file_path)` — imports + declarations with type signatures.
- `lean_diagnostic_messages(file_path, severity?, interactive)` — errors, warnings, infos, hints.
- `lean_goal(file_path, line, column?)` — proof goal before/after a position.
- `lean_term_goal(file_path, line, column)` — term-mode goal at a position.
- `lean_hover_info(file_path, line, column)` — symbol docs + type.
- `lean_declaration_file(file_path, line, column)` — file contents where a symbol is declared.
- `lean_references(file_path, line, column)` — all reference sites of a symbol.
- `lean_completions(file_path, line, column)` — autocomplete + import suggestions.
- `lean_run_code(code)` — compile/execute a standalone snippet.
- `lean_multi_attempt(file_path, line, column?, tactics)` — try multiple tactics, return goal+diagnostics for each.
- `lean_code_actions(file_path, line)` — LSP code actions, including "Try This" suggestions.
- `lean_get_widgets(file_path, line, column)` — raw widget data for proof visualizations.
- `lean_get_widget_source(javascript_hash)` — JS source of a widget by hash.
- `lean_profile_proof(file_path, line)` — per-line tactic timing.
- `lean_verify(file_path, line)` — axiom audit + unsafe-pattern scan.

**Search:**
- `lean_local_search(query)` — definitions/theorems in local project + stdlib (requires ripgrep).
- `lean_leansearch(query)` — natural-language Mathlib search via leansearch.net.
- `lean_loogle(query)` — search by constant, type, or expression pattern.
- `lean_leanfinder(query)` — semantic Mathlib search from informal descriptions.
- `lean_state_search(file_path, line, column)` — theorems applicable to the current goal.
- `lean_hammer_premise(file_path, line, column)` — premises relevant to the proof state.

**Project:**
- `lean_build()` — rebuild project + restart LSP.

## Coq / Rocq

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| mcp-coq-lsp | [scidonia/mcp-coq-lsp](https://github.com/scidonia/mcp-coq-lsp) | Coq LSP tools | 3 | Nascent but the right approach. Plans to extend to Lean and Isabelle. Worth watching. |

## Agda

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| agda-mcp | [faezs/agda-mcp](https://github.com/faezs/agda-mcp) | `load_file`, `type_check` | 3 (requires Agda) | Basic but functional. Covers the essential load + check loop. |

## Isabelle / HOL

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| AutoCorrode | [awslabs/AutoCorrode](https://github.com/awslabs/AutoCorrode) | Isabelle/HOL proof editing | 4 (requires Isabelle) | AWS Labs experimental project. Most serious Isabelle MCP effort. |
| qisabelle | [marcinwrochna/qisabelle](https://github.com/marcinwrochna/qisabelle) | Python client (not MCP) | 3 | TCP client for Isabelle server with Sledgehammer integration. Not an MCP server but wrappable. |
| isabelle-client | [inpefess/isabelle-client](https://github.com/inpefess/isabelle-client) | Python TCP client (not MCP) | 3 | Low-level Isabelle server client per the system manual. Wrappable as MCP. |

## Metamath

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| metamath/set.mm | [metamath/set.mm](https://github.com/metamath/set.mm) | Database only (no MCP) | 1 | The Metamath Proof Explorer database (ZFC). No MCP wrapper exists yet — opportunity. |
| mm0 | [digama0/mm0](https://github.com/digama0/mm0) | Specification language (no MCP) | 2 | Metamath Zero: fast checking, interpretable as HOL subset. No MCP wrapper. |

## Notes

- **Primary workflow**: lean-lsp-mcp + the original servers in this repo (proof-explorer, math-compute, math-viz, math-search)
- **Lean4 setup prerequisite**: [elan](https://github.com/leanprover/elan) (Lean version manager) + a Mathlib project initialized with `lake new myproject math`
- Coq and Isabelle tools are less mature in the MCP ecosystem; contributions welcome
