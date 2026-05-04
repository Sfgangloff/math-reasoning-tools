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


def _resolve_save_dir() -> Path:
    """Resolve the directory where generated images should be written.

    Order: MATH_TOOLS_IMAGE_DIR > CLAUDE_PROJECT_DIR/images > $PWD/images > cwd/images.

    PWD is preferred over Path.cwd() because `uv run --directory` calls os.chdir,
    which moves cwd into the server's own package dir; PWD still reflects the
    project Claude Code was launched from.
    """
    if override := os.environ.get("MATH_TOOLS_IMAGE_DIR"):
        return Path(override).expanduser().resolve()
    if claude_root := os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(claude_root).resolve() / "images"
    if pwd := os.environ.get("PWD"):
        return Path(pwd).resolve() / "images"
    return Path.cwd().resolve() / "images"


def _save_png(raw: bytes, description: str) -> str:
    save_dir = _resolve_save_dir()
    save_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", description)[:60].strip("_")
    path = save_dir / f"{int(time.time() * 1000)}_{slug}.png"
    path.write_bytes(raw)
    return str(path)


def _image(fig: plt.Figure, description: str) -> dict:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    path = _save_png(buf.getvalue(), description)
    return {"type": "text", "text": path}


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
    """Plot one or more real functions on an interval. Saves a PNG to <project>/images/ and returns the file path.
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
    """Plot a parametric curve in 2D or 3D. Saves a PNG to <project>/images/ and returns the file path.
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
    """Plot a 3D surface z = f(x, y). Saves a PNG to <project>/images/ and returns the file path.
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
    """Draw a graph from a list of [source, target] edges. Saves a PNG to <project>/images/ and returns the file path.
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
    """Draw a Hasse diagram of a finite poset from its cover relations. Saves a PNG to <project>/images/ and returns the file path.
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
    """Draw a 2D simplicial complex from its maximal faces (facets). Saves a PNG to <project>/images/ and returns the file path.
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
    """Render a LaTeX math formula to a PNG image. Saves a PNG to <project>/images/ and returns the file path.
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
    """Render a matrix as a formatted image. Saves a PNG to <project>/images/ and returns the file path.
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


@mcp.tool()
def plot_cobweb(
    f_expr: str,
    x0: float,
    n_iter: int = 30,
    x_min: float = -2.0,
    x_max: float = 2.0,
    variable: str = "x",
) -> dict:
    """Cobweb plot of the iterated 1D map x_(n+1) = f(x_n). Saves a PNG to <project>/images/ and returns the file path.
    Plots y=f(x) and y=x on [x_min, x_max], then draws the staircase orbit starting at x0.
    Useful for visualizing fixed points, attractors, and periodic cycles of an iteration.
    Example: f_expr='cos(x)', x0=0.5, n_iter=40 (Dottie number ~0.739)"""
    f = _lambdify_expr(f_expr, variable)
    xs = np.linspace(x_min, x_max, 800)
    ys = f(xs)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot(xs, ys, color="#3498db", linewidth=2, label=f"y = {f_expr}")
    ax.plot([x_min, x_max], [x_min, x_max], color="#7f8c8d", linewidth=1.2, linestyle="--", label="y = x")

    x = float(x0)
    orbit_x = [x]
    orbit_y = [0.0]
    for _ in range(int(n_iter)):
        try:
            y = float(f(x))
        except Exception:
            break
        if not np.isfinite(y):
            break
        orbit_x.extend([x, y])
        orbit_y.extend([y, y])
        x = y

    ax.plot(orbit_x, orbit_y, color="#e74c3c", linewidth=1.4, alpha=0.85)
    ax.scatter([x0], [0.0], color="#e74c3c", zorder=5, s=30, label=f"{variable}_0 = {x0}")

    ax.set_xlabel(variable)
    ax.set_ylabel(f"f({variable})")
    ax.set_title(f"Cobweb of {variable}_(n+1) = {f_expr}")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(x_min, x_max)
    return _image(fig, f"Cobweb of {f_expr}")


@mcp.tool()
def plot_partial_sums(
    term_expr: str,
    n_max: int = 200,
    index: str = "n",
    start_index: int = 1,
    log_y: bool = False,
) -> dict:
    """Plot partial sums S_N = sum_{n=start_index}^N a_n versus N. Saves a PNG to <project>/images/ and returns the file path.
    Useful for diagnosing series convergence/divergence and visualizing the rate of convergence
    (set log_y=True to read off the asymptotic rate).
    Example: term_expr='1/n**2', n_max=300 (converges to π²/6 ≈ 1.6449)"""
    a = _lambdify_expr(term_expr, index)
    Ns = np.arange(int(start_index), int(start_index) + int(n_max))
    try:
        terms = np.asarray(a(Ns), dtype=float)
    except Exception as e:
        return {"type": "text", "text": f"Error evaluating term: {e}"}
    sums = np.cumsum(terms)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(Ns, sums, color="#2980b9", linewidth=1.8)
    step = max(1, len(Ns) // 40)
    ax.scatter(Ns[::step], sums[::step], color="#2980b9", s=14, alpha=0.7)
    ax.set_xlabel("N")
    ax.set_ylabel("S_N")
    if log_y:
        ax.set_yscale("symlog")
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    final = sums[-1] if len(sums) else float("nan")
    ax.set_title(f"Partial sums of a_{index} = {term_expr}, S_{Ns[-1] if len(Ns) else 0} ≈ {final:.6g}")
    return _image(fig, f"Partial sums of {term_expr}")


@mcp.tool()
def plot_phase_portrait(
    dx_expr: str,
    dy_expr: str,
    x_min: float = -3.0,
    x_max: float = 3.0,
    y_min: float = -3.0,
    y_max: float = 3.0,
    trajectories: Optional[list[list[float]]] = None,
    t_max: float = 10.0,
    grid_density: int = 20,
) -> dict:
    """Phase portrait of an autonomous 2D ODE system dx/dt = F(x,y), dy/dt = G(x,y).
    Draws a normalized direction field (color = speed) and overlays trajectories from any
    initial points provided. Saves a PNG to <project>/images/ and returns the file path.
    Example: dx_expr='y', dy_expr='-sin(x) - 0.1*y', trajectories=[[0,1],[2,0]] (damped pendulum)"""
    import sympy
    from scipy.integrate import solve_ivp

    ns = {name: getattr(sympy, name) for name in dir(sympy) if not name.startswith("_")}
    sx, sy = Symbol("x"), Symbol("y")
    ns.update({"x": sx, "y": sy})
    try:
        dx_e = parse_expr(dx_expr, local_dict=ns, transformations=_TRANSFORMATIONS)
        dy_e = parse_expr(dy_expr, local_dict=ns, transformations=_TRANSFORMATIONS)
    except Exception as e:
        return {"type": "text", "text": f"Error parsing field: {e}"}
    F = lambdify((sx, sy), dx_e, modules=["numpy"])
    G = lambdify((sx, sy), dy_e, modules=["numpy"])

    xs = np.linspace(x_min, x_max, int(grid_density))
    ys = np.linspace(y_min, y_max, int(grid_density))
    X, Y = np.meshgrid(xs, ys)
    try:
        U = np.broadcast_to(np.asarray(F(X, Y), dtype=float), X.shape).copy()
        V = np.broadcast_to(np.asarray(G(X, Y), dtype=float), X.shape).copy()
    except Exception as e:
        return {"type": "text", "text": f"Error evaluating field: {e}"}
    M = np.hypot(U, V)
    Mn = np.where(M == 0, 1.0, M)
    Un, Vn = U / Mn, V / Mn

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.quiver(X, Y, Un, Vn, M, cmap="viridis", pivot="middle", scale=30, width=0.003, alpha=0.85)

    if trajectories:
        def rhs(_t, z):
            return [float(F(z[0], z[1])), float(G(z[0], z[1]))]
        for ic in trajectories:
            if len(ic) < 2:
                continue
            try:
                sol = solve_ivp(rhs, (0, float(t_max)), [float(ic[0]), float(ic[1])],
                                max_step=0.05, rtol=1e-6, atol=1e-9)
                ax.plot(sol.y[0], sol.y[1], color="#e74c3c", linewidth=1.6)
                ax.scatter([sol.y[0][0]], [sol.y[1][0]], color="#e74c3c", s=30, zorder=5)
            except Exception:
                pass

    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.set_xlim(x_min, x_max); ax.set_ylim(y_min, y_max)
    ax.set_title(f"dx/dt = {dx_expr},  dy/dt = {dy_expr}")
    ax.grid(True, alpha=0.3)
    return _image(fig, f"Phase portrait dx={dx_expr} dy={dy_expr}")


@mcp.tool()
def plot_implicit(
    expression: str,
    x_min: float = -3.0,
    x_max: float = 3.0,
    y_min: float = -3.0,
    y_max: float = 3.0,
    variable_x: str = "x",
    variable_y: str = "y",
) -> dict:
    """Plot the zero set {(x,y) : f(x,y) = 0} of a 2-variable expression. Saves a PNG to <project>/images/ and returns the file path.
    To plot f(x,y) = g(x,y), pass `f(x,y) - g(x,y)` as the expression.
    Example: expression='x**2 + y**2 - 1' (unit circle); expression='y**2 - x**3 - 1' (cubic)"""
    import sympy
    ns = {name: getattr(sympy, name) for name in dir(sympy) if not name.startswith("_")}
    sx, sy = Symbol(variable_x), Symbol(variable_y)
    ns.update({variable_x: sx, variable_y: sy})
    try:
        expr = parse_expr(expression, local_dict=ns, transformations=_TRANSFORMATIONS)
    except Exception as e:
        return {"type": "text", "text": f"Error parsing expression: {e}"}
    f = lambdify((sx, sy), expr, modules=["numpy"])

    xs = np.linspace(x_min, x_max, 400)
    ys = np.linspace(y_min, y_max, 400)
    X, Y = np.meshgrid(xs, ys)
    try:
        Z = np.broadcast_to(np.asarray(f(X, Y), dtype=float), X.shape).copy()
    except Exception as e:
        return {"type": "text", "text": f"Error evaluating expression: {e}"}

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.contour(X, Y, Z, levels=[0.0], colors=["#2980b9"], linewidths=2)
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel(variable_x); ax.set_ylabel(variable_y)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title(f"{expression} = 0")
    ax.grid(True, alpha=0.3)
    return _image(fig, f"Implicit curve {expression} = 0")


@mcp.tool()
def plot_region(
    condition: str,
    x_min: float = -3.0,
    x_max: float = 3.0,
    y_min: float = -3.0,
    y_max: float = 3.0,
    variable_x: str = "x",
    variable_y: str = "y",
) -> dict:
    """Shade the region {(x,y) : condition} where `condition` is a Boolean expression.
    Combine multiple inequalities with & (AND) or | (OR), wrapping each clause in parens.
    Saves a PNG to <project>/images/ and returns the file path.
    Example: condition='x**2 + y**2 < 1' (open disk);
             condition='(x**2 + y**2 < 1) & (y > x)' (half-disk above the diagonal)"""
    import sympy
    ns = {name: getattr(sympy, name) for name in dir(sympy) if not name.startswith("_")}
    sx, sy = Symbol(variable_x), Symbol(variable_y)
    ns.update({variable_x: sx, variable_y: sy})
    try:
        expr = parse_expr(condition, local_dict=ns, transformations=_TRANSFORMATIONS)
    except Exception as e:
        return {"type": "text", "text": f"Error parsing condition: {e}"}
    f = lambdify((sx, sy), expr, modules=["numpy"])

    xs = np.linspace(x_min, x_max, 400)
    ys = np.linspace(y_min, y_max, 400)
    X, Y = np.meshgrid(xs, ys)
    try:
        raw = f(X, Y)
        mask = np.broadcast_to(np.asarray(raw, dtype=float), X.shape).copy()
    except Exception as e:
        return {"type": "text", "text": f"Error evaluating condition: {e}"}

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.contourf(X, Y, mask, levels=[0.5, 1.5], colors=["#3498db"], alpha=0.5)
    ax.contour(X, Y, mask, levels=[0.5], colors=["#2c3e50"], linewidths=1.2)
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.5, linestyle="--")
    ax.set_xlabel(variable_x); ax.set_ylabel(variable_y)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlim(x_min, x_max); ax.set_ylim(y_min, y_max)
    ax.set_title(condition)
    ax.grid(True, alpha=0.3)
    return _image(fig, f"Region {condition}")


@mcp.tool()
def plot_integrand_with_shading(
    expression: str,
    a: float,
    b: float,
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    variable: str = "x",
) -> dict:
    """Plot a function and shade the area under the curve between x=a and x=b.
    Computes the numerical value of int_a^b f(x) dx (via scipy.integrate.quad) and shows
    it in the title. Useful for visualizing integral problems and sanity-checking values.
    Saves a PNG to <project>/images/ and returns the file path.
    Example: expression='exp(-x**2)', a=-2, b=2 (truncated Gaussian)"""
    from scipy.integrate import quad

    span = abs(b - a) if b != a else 1.0
    if x_min is None:
        x_min = min(a, b) - 0.2 * span - 0.1
    if x_max is None:
        x_max = max(a, b) + 0.2 * span + 0.1

    f = _lambdify_expr(expression, variable)

    xs_full = np.linspace(x_min, x_max, 800)
    ys_full = f(xs_full)
    ys_full = np.where(np.abs(ys_full) > 1e6, np.nan, ys_full)

    xs_fill = np.linspace(min(a, b), max(a, b), 400)
    ys_fill = f(xs_fill)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(xs_full, ys_full, color="#2980b9", linewidth=2, label=f"y = {expression}")
    ax.fill_between(xs_fill, 0, ys_fill, color="#3498db", alpha=0.35)
    ax.axvline(a, color="#7f8c8d", linewidth=1, linestyle="--")
    ax.axvline(b, color="#7f8c8d", linewidth=1, linestyle="--")
    ax.axhline(0, color="black", linewidth=0.5)

    try:
        val, _err = quad(lambda t: float(f(t)), a, b, limit=200)
        title = f"∫ from {a} to {b} of {expression}  ≈  {val:.6g}"
    except Exception:
        title = f"Integral of {expression} from {a} to {b}"

    ax.set_xlabel(variable)
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_title(title)
    return _image(fig, f"Integrand {expression} on [{a},{b}]")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
