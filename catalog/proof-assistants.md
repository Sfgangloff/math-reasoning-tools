# Proof Assistants

MCP servers and tools for interacting with formal proof assistants.

## Lean4

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| lean-lsp-mcp | [oOo0oOo/lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp) | `check_file`, `get_goal`, `lean_search`, `loogle`, `lean_hammer`, `lean_state_search` | 3 (requires Lean4 + Mathlib) | **Primary recommendation.** Best Lean4 MCP tool available. LSP integration + semantic search. Actively maintained. Also mirrored at [project-numina/lean-lsp-mcp](https://github.com/project-numina/lean-lsp-mcp). |
| lean-aristotle-mcp | [septract/lean-aristotle-mcp](https://github.com/septract/lean-aristotle-mcp) | `aristotle_prove` | 4 (requires Harmonic Aristotle) | Wraps Harmonic's ATP for Lean4. Good for auto-closing goals that `aesop`/`decide` cannot handle. Requires separate Aristotle install. |
| lean4-skills | [cameronfreer/lean4-skills](https://github.com/cameronfreer/lean4-skills) | Claude Code skill pack (not MCP tools) | 2 | Prove/review/golf loop as Claude Code skills rather than MCP tools. Complements lean-lsp-mcp. |
| lean-agentic | [agenticsorg/lean-agentic](https://github.com/agenticsorg/lean-agentic) | Hybrid Lean4/agent orchestration | 4 | Experimental. Interesting architecture but low activity. |

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
