import base64
import math
import os
import re
import time
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, must be set before importing pyplot
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from fastmcp import FastMCP
from sympy import Symbol, latex, sympify
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
from sympy.utilities.lambdify import lambdify

mcp = FastMCP("math-viz")

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)
_DPI = 150
_SAVE_DIR: Path | None = Path(d) if (d := os.environ.get("MATH_TOOLS_IMAGE_DIR")) else None


def _maybe_save_png(raw: bytes, description: str) -> None:
    if _SAVE_DIR is None:
        return
    _SAVE_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", description)[:60].strip("_")
    (_SAVE_DIR / f"{int(time.time() * 1000)}_{slug}.png").write_bytes(raw)


def _image(fig: plt.Figure, description: str) -> dict:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    raw = buf.getvalue()
    _maybe_save_png(raw, description)
    return {"type": "image", "data": base64.b64encode(raw).decode(), "mimeType": "image/png", "alt": description}


def _lambdify_expr(expr_str: str, var_name: str):
    """Parse a math expression string and return a numpy-backed callable."""
    import sympy
    ns = {name: getattr(sympy, name) for name in dir(sympy) if not name.startswith("_")}
    var = Symbol(var_name)
    ns[var_name] = var
    expr = parse_expr(expr_str, local_dict=ns, transformations=_TRANSFORMATIONS)
    return lambdify(var, expr, modules=["numpy"])


@mcp.tool()
def plot_function(
    expressions: list[str],
    variable: str = "x",
    x_min: float = -10.0,
    x_max: float = 10.0,
    labels: Optional[list[str]] = None,
) -> dict:
    """Plot one or more real functions on an interval. Returns an image.
    Example: expressions=['sin(x)', 'cos(x)'], x_min=-6.28, x_max=6.28"""
    x = np.linspace(x_min, x_max, 800)
    fig, ax = plt.subplots(figsize=(8, 5))

    for i, expr_str in enumerate(expressions):
        try:
            f = _lambdify_expr(expr_str, variable)
            y = f(x)
            y = np.where(np.abs(y) > 1e6, np.nan, y)  # clip discontinuities
            label = (labels[i] if labels and i < len(labels) else expr_str)
            ax.plot(x, y, label=label, linewidth=2)
        except Exception as e:
            ax.text(0.5, 0.5, f"Error in '{expr_str}': {e}", transform=ax.transAxes, ha="center")

    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel(variable)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title(", ".join(expressions[:3]) + ("..." if len(expressions) > 3 else ""))

    return _image(fig, f"Plot of {', '.join(expressions)}")


@mcp.tool()
def plot_parametric(
    x_expr: str,
    y_expr: str,
    parameter: str = "t",
    t_min: float = 0.0,
    t_max: float = 6.2832,
    z_expr: str = "",
) -> dict:
    """Plot a parametric curve in 2D or 3D. Returns an image.
    Example: x_expr='cos(t)', y_expr='sin(t)' draws a unit circle.
    For 3D: also set z_expr='t'"""
    t = np.linspace(t_min, t_max, 1000)
    fx = _lambdify_expr(x_expr, parameter)
    fy = _lambdify_expr(y_expr, parameter)

    xs = fx(t)
    ys = fy(t)

    if z_expr:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        fz = _lambdify_expr(z_expr, parameter)
        zs = fz(t)
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection="3d")
        ax.plot(xs, ys, zs, linewidth=2)
        ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
        title = f"({x_expr}, {y_expr}, {z_expr})"
    else:
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.plot(xs, ys, linewidth=2)
        ax.set_xlabel("x"); ax.set_ylabel("y")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, alpha=0.3)
        title = f"({x_expr}, {y_expr})"

    fig.suptitle(f"Parametric: {title}")
    return _image(fig, f"Parametric curve {title}")


@mcp.tool()
def plot_surface(
    expression: str,
    x_min: float = -5.0,
    x_max: float = 5.0,
    y_min: float = -5.0,
    y_max: float = 5.0,
) -> dict:
    """Plot a 3D surface z = f(x, y). Returns an image.
    Example: expression='sin(sqrt(x**2 + y**2))'"""
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    import sympy

    ns = {name: getattr(sympy, name) for name in dir(sympy) if not name.startswith("_")}
    sx, sy = Symbol("x"), Symbol("y")
    ns.update({"x": sx, "y": sy})
    expr = parse_expr(expression, local_dict=ns, transformations=_TRANSFORMATIONS)
    f = lambdify((sx, sy), expr, modules=["numpy"])

    xs = np.linspace(x_min, x_max, 80)
    ys = np.linspace(y_min, y_max, 80)
    X, Y = np.meshgrid(xs, ys)
    try:
        Z = f(X, Y).astype(float)
        Z = np.where(np.abs(Z) > 1e6, np.nan, Z)
    except Exception as e:
        return {"type": "text", "text": f"Error evaluating surface: {e}"}

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.9, linewidth=0)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.set_title(f"z = {expression}")

    return _image(fig, f"Surface plot of {expression}")


@mcp.tool()
def draw_graph(
    edges: list[list[str]],
    directed: bool = False,
    node_labels: Optional[dict[str, str]] = None,
    highlight_nodes: Optional[list[str]] = None,
    highlight_edges: Optional[list[list[str]]] = None,
    layout: str = "spring",
) -> dict:
    """Draw a graph from a list of [source, target] edges. Returns an image.
    layout: 'spring' (default), 'circular', 'shell', 'spectral', 'kamada_kawai'.
    Example: edges=[['A','B'],['B','C'],['A','C']], directed=False"""
    G = nx.DiGraph() if directed else nx.Graph()
    for e in edges:
        if len(e) >= 2:
            G.add_edge(str(e[0]), str(e[1]))

    layouts = {
        "spring": nx.spring_layout,
        "circular": nx.circular_layout,
        "shell": nx.shell_layout,
        "spectral": nx.spectral_layout,
        "kamada_kawai": nx.kamada_kawai_layout,
    }
    layout_fn = layouts.get(layout, nx.spring_layout)
    try:
        pos = layout_fn(G, seed=42)
    except Exception:
        pos = nx.spring_layout(G, seed=42)

    hl_nodes = set(highlight_nodes or [])
    hl_edges = {(str(e[0]), str(e[1])) for e in (highlight_edges or [])}

    node_colors = ["#e74c3c" if n in hl_nodes else "#3498db" for n in G.nodes()]
    edge_colors = ["#e74c3c" if (u, v) in hl_edges or (v, u) in hl_edges else "#555555"
                   for u, v in G.edges()]

    labels = node_labels or {n: n for n in G.nodes()}

    fig, ax = plt.subplots(figsize=(8, 6))
    draw_kwargs: dict = dict(
        labels=labels,
        node_color=node_colors,
        edge_color=edge_colors,
        node_size=800,
        font_size=11,
        font_color="white",
        width=2,
    )
    if directed:
        draw_kwargs.update(arrows=True, arrowsize=20)
    nx.draw_networkx(G, pos=pos, ax=ax, **draw_kwargs)
    ax.axis("off")
    fig.tight_layout()

    desc = f"{'Directed' if directed else 'Undirected'} graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges"
    return _image(fig, desc)


@mcp.tool()
def draw_poset(
    relations: list[list[str]],
    labels: Optional[dict[str, str]] = None,
) -> dict:
    """Draw a Hasse diagram of a finite poset from its cover relations. Returns an image.
    relations: list of [smaller, larger] cover pairs (not all comparable pairs, just covers).
    Example: relations=[['1','2'],['1','3'],['2','6'],['3','6']] (divisibility on {1,2,3,6})"""
    G = nx.DiGraph()
    for rel in relations:
        if len(rel) >= 2:
            G.add_edge(str(rel[0]), str(rel[1]))  # edge goes upward: smaller -> larger

    # Assign layer = length of longest path from any source
    layers: dict[str, int] = {}
    for node in nx.topological_sort(G):
        preds = list(G.predecessors(node))
        layers[node] = 0 if not preds else max(layers[p] for p in preds) + 1

    layer_groups: dict[int, list[str]] = defaultdict(list)
    for node, layer in layers.items():
        layer_groups[layer].append(node)

    pos: dict[str, tuple[float, float]] = {}
    for layer, nodes in layer_groups.items():
        nodes_sorted = sorted(nodes)
        for i, node in enumerate(nodes_sorted):
            pos[node] = (i - (len(nodes_sorted) - 1) / 2, layer)

    node_labels = labels or {n: n for n in G.nodes()}

    fig, ax = plt.subplots(figsize=(max(6, len(G.nodes()) * 0.8), max(5, max(layers.values()) + 1) * 1.5))
    nx.draw_networkx(
        G, pos=pos, ax=ax,
        labels=node_labels,
        node_color="#2ecc71",
        edge_color="#2c3e50",
        node_size=900,
        font_size=12,
        font_color="white",
        arrows=False,
        width=2,
    )
    ax.axis("off")
    fig.tight_layout()

    return _image(fig, f"Hasse diagram with {G.number_of_nodes()} elements")


@mcp.tool()
def draw_simplicial_complex(facets: list[list[str]]) -> dict:
    """Draw a 2D simplicial complex from its maximal faces (facets). Returns an image.
    Supports 0-simplices (vertices), 1-simplices (edges), 2-simplices (triangles).
    Example: facets=[['a','b','c'],['b','c','d'],['d','e']]"""
    # Collect all sub-simplices
    vertices: set[str] = set()
    edges: set[tuple[str, str]] = set()
    triangles: list[tuple[str, str, str]] = []

    for facet in facets:
        facet = [str(v) for v in facet]
        if len(facet) == 1:
            vertices.add(facet[0])
        elif len(facet) == 2:
            vertices.update(facet)
            edges.add((facet[0], facet[1]))
        elif len(facet) == 3:
            vertices.update(facet)
            a, b, c = facet[0], facet[1], facet[2]
            edges.update([(a, b), (b, c), (a, c)])
            triangles.append((a, b, c))
        elif len(facet) > 3:
            # Decompose higher-dim facets into triangles for visualization
            vertices.update(facet)
            for i in range(len(facet)):
                for j in range(i + 1, len(facet)):
                    edges.add((facet[i], facet[j]))

    # Get vertex positions using spring layout on the 1-skeleton
    G = nx.Graph()
    G.add_nodes_from(vertices)
    G.add_edges_from(edges)
    pos = nx.spring_layout(G, seed=42, k=2.0)

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_aspect("equal")

    # Draw filled triangles first (background)
    for (a, b, c) in triangles:
        tri = plt.Polygon(
            [pos[a], pos[b], pos[c]],
            closed=True,
            facecolor="#3498db",
            edgecolor="#2980b9",
            alpha=0.3,
        )
        ax.add_patch(tri)

    # Draw edges
    for (u, v) in edges:
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                color="#2c3e50", linewidth=2, zorder=2)

    # Draw vertices
    for v in vertices:
        ax.scatter(*pos[v], s=200, color="#e74c3c", zorder=3)
        ax.annotate(
            v, pos[v], fontsize=12, ha="center", va="bottom",
            xytext=(0, 8), textcoords="offset points",
        )

    ax.axis("off")
    ax.set_title(f"Simplicial complex ({len(vertices)} vertices, {len(edges)} edges, {len(triangles)} triangles)")
    fig.tight_layout()

    return _image(fig, f"Simplicial complex with {len(vertices)} vertices")


@mcp.tool()
def render_latex(formula: str, fontsize: int = 24, dpi: int = 200) -> dict:
    """Render a LaTeX math formula to a PNG image. Returns an image.
    Uses matplotlib's mathtext renderer — supports most standard LaTeX math commands.
    Do NOT include $...$ delimiters; pass the formula directly.
    Example: formula=r'\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}'"""
    fig, ax = plt.subplots(figsize=(10, 1.5))
    ax.axis("off")
    try:
        ax.text(
            0.5, 0.5, f"${formula}$",
            transform=ax.transAxes,
            fontsize=fontsize,
            ha="center", va="center",
            usetex=False,  # use matplotlib mathtext, no LaTeX installation needed
        )
    except Exception as e:
        plt.close(fig)
        return {"type": "text", "text": f"Could not render formula: {e}\nFormula: {formula}"}

    fig.tight_layout(pad=0.1)
    return _image(fig, f"LaTeX formula: {formula[:80]}")


@mcp.tool()
def draw_matrix(
    rows: list[list[str]],
    row_labels: Optional[list[str]] = None,
    col_labels: Optional[list[str]] = None,
    highlight_cells: Optional[list[list[int]]] = None,
) -> dict:
    """Render a matrix as a formatted image. Returns an image.
    highlight_cells: list of [row_index, col_index] pairs (0-indexed) to highlight.
    Example: rows=[['1','0','0'],['0','1','0'],['0','0','1']] (3x3 identity)"""
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows) if rows else 0
    hl = {(r, c) for cell in (highlight_cells or []) for r, c in [cell[:2]]}

    fig, ax = plt.subplots(figsize=(max(3, n_cols * 1.0), max(2, n_rows * 0.6 + 1.0)))
    ax.axis("off")

    col_w = 1.0 / (n_cols + (1 if col_labels else 0) + 0.5)
    row_h = 1.0 / (n_rows + (1 if row_labels else 0) + 0.5)

    # Column labels
    if col_labels:
        for j, lbl in enumerate(col_labels[:n_cols]):
            x = (j + (1.5 if row_labels else 0.5)) * col_w
            ax.text(x, 1 - row_h * 0.5, lbl, ha="center", va="center",
                    fontsize=12, fontweight="bold", transform=ax.transAxes)

    for i, row in enumerate(rows):
        y = 1 - (i + (1.5 if col_labels else 0.5)) * row_h
        # Row label
        if row_labels and i < len(row_labels):
            ax.text(col_w * 0.5, y, row_labels[i], ha="center", va="center",
                    fontsize=12, fontweight="bold", transform=ax.transAxes)
        for j, cell in enumerate(row[:n_cols]):
            x = (j + (1.5 if row_labels else 0.5)) * col_w
            bg = "#f39c12" if (i, j) in hl else ("#ecf0f1" if (i + j) % 2 == 0 else "white")
            rect = mpatches.FancyBboxPatch(
                (x - col_w * 0.45, y - row_h * 0.45),
                col_w * 0.9, row_h * 0.9,
                boxstyle="round,pad=0.02",
                facecolor=bg, edgecolor="#bdc3c7", linewidth=1,
                transform=ax.transAxes,
            )
            ax.add_patch(rect)
            ax.text(x, y, cell, ha="center", va="center", fontsize=11, transform=ax.transAxes)

    ax.set_title(f"{n_rows}×{n_cols} matrix")
    return _image(fig, f"{n_rows}x{n_cols} matrix")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
