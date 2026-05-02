# Symbolic Computation

MCP servers for computer algebra systems, numerical computation, and formal solvers.

## SymPy-based

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| sympy-mcp | [sdiehl/sympy-mcp](https://github.com/sdiehl/sympy-mcp) | Symbolic manipulation tools | 1 | **Recommended.** Clean API, actively maintained (v0.1.1 May 2025). Good baseline for symbolic math. |
| fermat-mcp | [abhiphile/fermat-mcp](https://github.com/abhiphile/fermat-mcp) | SymPy + NumPy + Matplotlib unified | 1 | Broader scope than sympy-mcp. Includes plotting. FastMCP-based. |
| math-mcp (codeprimate) | [codeprimate/math-mcp](https://github.com/codeprimate/math-mcp) | SymPy + SciPy + data viz | 1 | Good coverage of equation solving, calculus, statistics. |

## Wolfram Language / Mathematica

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| mathematica-mcp | [lars20070/mathematica-mcp](https://github.com/lars20070/mathematica-mcp) | Wolfram Language evaluation via `wolframscript` | 4 (requires Wolfram Engine license) | Clean wrapping of `wolframscript` CLI. Only useful if you already have a license. |
| mcp-server-mathematica | [texra-ai/mcp-server-mathematica](https://github.com/texra-ai/mcp-server-mathematica) | Mathematica code execution + derivation verification | 4 | Adds verification step on top of evaluation. Interesting for checking algebraic manipulations. |
| mathematica_mcp | [aac6fef/mathematica_mcp](https://github.com/aac6fef/mathematica_mcp) | Mathematica kernel evaluation | 4 | Manages a persistent kernel session. |
| Wolfram-MCP | [paraporoco/Wolfram-MCP](https://github.com/paraporoco/Wolfram-MCP) | Wolfram Language computation | 4 | FastMCP-based Wolfram Language server. |
| MCPServer (Wolfram) | [rhennigan/MCPServer](https://github.com/rhennigan/MCPServer) | MCP server written in Wolfram Language | 5 | Meta: MCP server implemented inside Mathematica itself. Niche. |

## Wolfram Alpha (API)

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| mcp-wolframalpha | [akalaric/mcp-wolframalpha](https://github.com/akalaric/mcp-wolframalpha) | Wolfram Alpha query | 1 (API key required) | Simple and reliable. Best when you want a quick answer without full Mathematica. |
| mcp-wolfram-alpha | [cnosuke/mcp-wolfram-alpha](https://github.com/cnosuke/mcp-wolfram-alpha) | Wolfram Alpha query | 1 (API key required) | Similar to above. |
| wolframalpha-mcp-server | [StoneDot/wolframalpha-mcp-server](https://github.com/StoneDot/wolframalpha-mcp-server) | Wolfram Alpha LLM API | 1 (API key required) | Uses the LLM-optimized API endpoint — better structured output for Claude. |

## SMT Solvers / Formal Logic

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| Chiasmus | [yogthos/chiasmus](https://github.com/yogthos/chiasmus) | Z3 satisfiability check, Tau Prolog, tree-sitter analysis | 2 | **Recommended for decidable fragments.** Z3 via MCP is powerful for arithmetic, linear algebra, bit-vectors. |
| Chimera-Protocol | [mcp-research/Chimera-Protocol__csl-core](https://github.com/mcp-research/Chimera-Protocol__csl-core) | Z3 + TLA+ (roadmap) | 3 | Neuro-symbolic safety layer. Heavier than Chiasmus; aimed at agent safety. |

## General Mathematical Computation

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| MCP-Mathematics | [SHSharkar/MCP-Mathematics](https://github.com/SHSharkar/MCP-Mathematics) | 52 built-in math functions, 158 unit conversions, financial calculations | 1 | Production-ready, safe AST evaluation. Zero heavy dependencies. Good for quick arithmetic. |
| calculator-mcp-server | [huhabla/calculator-mcp-server](https://github.com/huhabla/calculator-mcp-server) | Symbolic math, statistics, matrix operations | 1 | Broader than a calculator. Covers most basic CAS use cases. |
| math-mcp-learning-server | [clouatre-labs/math-mcp-learning-server](https://github.com/clouatre-labs/math-mcp-learning-server) | Matrix algebra, data viz, persistent workspace | 2 | FastMCP 2.0, educational focus. Persistent workspace is unusual and useful. |

## Notes

- For pure symbolic manipulation in a theorem-proving workflow, **sympy-mcp** is the recommended starting point — then supplement with **Chiasmus** (Z3) for decidable goals.
- Wolfram tools require a license; the **Wolfram Alpha API tools** are free-tier accessible and sufficient for most quick lookups.
- **SageMath** is conspicuously absent from existing MCP tools despite being the most powerful open-source CAS (covers number theory, algebraic geometry, group theory, etc.). This is a gap filled by the `math-compute` server in this repo.
