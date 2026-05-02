# Visualization

MCP servers for producing visual output of mathematical objects.

## General plotting and charting

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| visualization-mcp-server | [xlisp/visualization-mcp-server](https://github.com/xlisp/visualization-mcp-server) | Matplotlib: line, scatter, bar, 3D, histograms | 1 | Direct Matplotlib wrapping. Produces images. Closest to what `math-viz` in this repo aims to do. |
| fermat-mcp | [abhiphile/fermat-mcp](https://github.com/abhiphile/fermat-mcp) | SymPy + Matplotlib unified (see symbolic-computation.md) | 1 | Includes plotting as part of a broader math server. |
| mcp-server-chart | [antvis/mcp-server-chart](https://github.com/antvis/mcp-server-chart) | 26+ chart types via AntV | 2 | Excellent for data visualization and statistics. Less suited to pure math objects (no function plots, no graph drawing). |
| mcp-plots | [MR901/mcp-plots](https://github.com/MR901/mcp-plots) | Mermaid: line, bar, pie, scatter, heatmap | 1 | Lightweight, no local Python needed. Output is Mermaid markup rendered by Claude Code. Limited to chart types Mermaid supports. |
| Quickchart-MCP-Server | [GongRzhe/Quickchart-MCP-Server](https://github.com/GongRzhe/Quickchart-MCP-Server) | Chart.js charts via QuickChart.io | 1 (HTTP API) | No local deps. Sends data to an external service — consider privacy implications. |
| math-mcp-learning-server | [clouatre-labs/math-mcp-learning-server](https://github.com/clouatre-labs/math-mcp-learning-server) | Line, scatter, box plots, financial trends | 2 | Education-focused. Good variety of plot types. |
| plotting-mcp | [StacklokLabs/plotting-mcp](https://github.com/StacklokLabs/plotting-mcp) | CSV → visualization | 1 | Data-centric. Not suited to mathematical function plots. |

## Geometry and 3D

| Tool | URL | Tools exposed | Install difficulty | Assessment |
|------|-----|--------------|-------------------|------------|
| rhinomcp-mod | [johanesmikhael/rhinomcp-mod](https://github.com/johanesmikhael/rhinomcp-mod) | Rhino3D geometry and topology | 5 (requires Rhino) | Powerful but requires a commercial Rhino license. Useful for geometric constructions. |
| blender-mcp-Geometry_Nodes | [MScanter/blender-mcp-Geometry_Nodes](https://github.com/MScanter/blender-mcp-Geometry_Nodes) | Blender geometry nodes | 3 (requires Blender) | Blender is free; good for 3D mathematical surfaces. |
| MCP-Drawing | [theosorus/MCP-Drawing](https://github.com/theosorus/MCP-Drawing) | Canvas-based geometric shape rendering | 1 | TypeScript/React based. 2D geometric shapes. Simple but fast. |

## Gaps (what does not yet exist as MCP tools)

These are mathematical visualization needs not covered by any existing tool:

- **Commutative diagrams** (tikz-cd, Quiver): essential for category theory and homological algebra → filled by `commutative-diagrams` server in this repo
- **Hasse diagrams / posets**: no dedicated tool → filled by `math-viz` in this repo
- **Simplicial complexes**: no tool → filled by `math-viz`
- **Knot diagrams**: no tool
- **LaTeX formula → PNG**: no standalone tool → filled by `math-viz`
- **Graph drawing with mathematical layout** (e.g., Cayley graphs, dependency graphs of Lean4 lemmas): no tool → filled by `math-viz`

## Notes

- Most existing tools produce charts from data. Mathematical visualization (objects defined by formulas or combinatorial structure) is largely unserved.
- `visualization-mcp-server` is the closest existing tool to what a mathematician needs, but it requires passing Matplotlib code rather than structured inputs.
- The `math-viz` server in this repo is designed to fill this gap with structured, safe, Lean4-friendly visual tools.
