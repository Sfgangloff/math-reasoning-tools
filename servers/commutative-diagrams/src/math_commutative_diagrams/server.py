import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

mcp = FastMCP("commutative-diagrams")

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


def _fig_to_image(fig: plt.Figure, description: str) -> list[Image | str]:
    """Render `fig` to PNG, save a copy, and return [inline image, "Saved to <path>"]."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    raw = buf.getvalue()
    path = _save_png(raw, description)
    return [Image(data=raw, format="png"), f"Saved to {path}"]


def _png_bytes_to_image(raw: bytes, description: str) -> list[Image | str]:
    """Same as _fig_to_image but for already-rendered PNG bytes."""
    path = _save_png(raw, description)
    return [Image(data=raw, format="png"), f"Saved to {path}"]


@mcp.tool()
def render_tikzcd(tikzcd_source: str) -> list[Image | str]:
    """Render a tikz-cd commutative diagram via pdflatex. Reach for this whenever discussing
    diagram chases, exact sequences, pullback/pushout squares, natural transformations, or any
    categorical statement where a tikz-cd diagram is the standard way to communicate — bent arrows,
    double arrows, two-cells, and labeled morphisms all render properly. Returns the rendered PNG
    inline. Pass only the tikzcd environment body (without \\begin{tikzcd}...\\end{tikzcd}).
    Requires: pdflatex and the tikz-cd LaTeX package installed on the system.
    Example: tikzcd_source='A \\\\arrow[r, \"f\"] \\\\arrow[d, \"h\"] & B \\\\arrow[d, \"g\"] \\\\\\\\ C \\\\arrow[r, \"k\"] & D'"""
    if not shutil.which("pdflatex"):
        return [
            "pdflatex not found. Install TeX Live or MacTeX to use render_tikzcd.\n"
            "Alternatively, use diagram_from_description for a matplotlib-rendered fallback."
        ]

    latex_doc = rf"""
\documentclass[preview]{{standalone}}
\usepackage{{tikz-cd}}
\begin{{document}}
\begin{{tikzcd}}
{tikzcd_source}
\end{{tikzcd}}
\end{{document}}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "diagram.tex"
        tex_path.write_text(latex_doc)

        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_path)],
                capture_output=True, text=True, timeout=30,
            )
        except subprocess.TimeoutExpired:
            return ["pdflatex timed out after 30s."]

        pdf_path = Path(tmpdir) / "diagram.pdf"
        if not pdf_path.exists():
            log = result.stdout[-1000:] if result.stdout else result.stderr[-1000:]
            return [f"pdflatex failed:\n{log}"]

        try:
            from pdf2image import convert_from_path
            images = convert_from_path(str(pdf_path), dpi=200)
            if images:
                buf = BytesIO()
                images[0].save(buf, format="PNG")
                return _png_bytes_to_image(buf.getvalue(), "Commutative diagram (tikzcd)")
        except ImportError:
            pass

        # Fallback: pdf2image not available
        return [
            f"PDF generated at {pdf_path} but pdf2image not installed for PNG conversion.\n"
            "Install: pip install pdf2image (also needs poppler)."
        ]


@mcp.tool()
def render_quiver(quiver_json: str) -> list[Image | str]:
    """Render a commutative diagram from a Quiver (q.uiver.app) JSON export. Reach for this when
    the user has a diagram already laid out in Quiver, or when q.uiver.app's manual positioning is
    preferable to the auto-layout in `diagram_from_description`. Returns the rendered PNG inline.
    Export from https://q.uiver.app via Export → JSON, then paste here.
    Quiver JSON format: [0, {"nodes": [...], "edges": [...]}]"""
    import json

    try:
        data = json.loads(quiver_json)
        # Quiver JSON: [version, {"nodes": [...], "edges": [...]}]
        if isinstance(data, list) and len(data) >= 2:
            payload = data[1]
        elif isinstance(data, dict):
            payload = data
        else:
            return ["Unrecognized Quiver JSON format."]

        nodes = payload.get("nodes", [])
        edges = payload.get("edges", [])
    except json.JSONDecodeError as e:
        return [f"JSON parse error: {e}"]

    if not nodes:
        return ["No nodes found in Quiver JSON."]

    # Quiver positions are grid coords (x, y); invert y for matplotlib (y axis up)
    positions = {}
    for i, node in enumerate(nodes):
        qx = node.get("x", i)
        qy = -node.get("y", 0)  # invert y
        positions[i] = (float(qx), float(qy))

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect("equal")
    ax.axis("off")

    # Draw edges
    for edge in edges:
        src = edge.get("source", 0)
        tgt = edge.get("target", 0)
        label = edge.get("label", {}).get("value", "") if isinstance(edge.get("label"), dict) else edge.get("label", "")

        if src not in positions or tgt not in positions:
            continue

        x0, y0 = positions[src]
        x1, y1 = positions[tgt]

        _draw_arrow(ax, x0, y0, x1, y1, label)

    # Draw nodes
    for i, node in enumerate(nodes):
        x, y = positions[i]
        lbl = node.get("label", {}).get("value", str(i)) if isinstance(node.get("label"), dict) else str(node.get("label", i))
        ax.text(x, y, f"${lbl}$" if lbl else str(i),
                fontsize=16, ha="center", va="center",
                bbox=dict(facecolor="white", edgecolor="none", pad=3))

    _autoscale(ax, positions)
    fig.tight_layout()

    return _fig_to_image(fig, "Commutative diagram from Quiver")


@mcp.tool()
def diagram_from_description(description: str) -> list[Image | str]:
    """Render a commutative diagram from a simple text description (no LaTeX needed). Reach for
    this for quick categorical pictures — squares, triangles, universal-property diagrams, functor
    actions, factoring through an object — whenever you'd otherwise type out objects and arrows in
    chat. Faster than `render_tikzcd` and works even without a LaTeX install. Returns the rendered
    PNG inline.
    Format (one per line):
      objects: A B C D
      arrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D
      commutes: g ∘ f = k ∘ h   (optional, shown as label)
    Example:
      objects: A B C D
      arrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D"""
    parsed = _parse_diagram_dsl(description)
    if "error" in parsed:
        return [parsed["error"]]

    objects = parsed["objects"]
    arrows = parsed["arrows"]
    positions = _auto_layout(objects)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect("equal")
    ax.axis("off")

    for (src, tgt, label) in arrows:
        if src in positions and tgt in positions:
            x0, y0 = positions[src]
            x1, y1 = positions[tgt]
            _draw_arrow(ax, x0, y0, x1, y1, label)

    for obj, (x, y) in positions.items():
        ax.text(x, y, f"${obj}$",
                fontsize=18, ha="center", va="center", fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none", pad=4))

    if parsed.get("commutes"):
        ax.set_title("Commutes: " + ", ".join(parsed["commutes"]), fontsize=11, style="italic")

    _autoscale(ax, positions)
    fig.tight_layout()

    return _fig_to_image(fig, f"Commutative diagram: {', '.join(objects)}")


# ─── helpers ──────────────────────────────────────────────────────────────────

def _draw_arrow(
    ax: plt.Axes,
    x0: float, y0: float,
    x1: float, y1: float,
    label: str = "",
) -> None:
    """Draw a labeled arrow from (x0,y0) to (x1,y1), offset from node centers."""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return

    pad = 0.18  # offset from node center so arrows don't overlap labels
    ux, uy = dx / length, dy / length
    sx, sy = x0 + ux * pad, y0 + uy * pad
    ex, ey = x1 - ux * pad, y1 - uy * pad

    ax.annotate(
        "",
        xy=(ex, ey), xytext=(sx, sy),
        arrowprops=dict(
            arrowstyle="-|>",
            color="#2c3e50",
            lw=1.8,
            mutation_scale=18,
        ),
    )

    if label:
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        perp_x, perp_y = -uy * 0.12, ux * 0.12
        ax.text(
            mx + perp_x, my + perp_y,
            f"${label}$",
            fontsize=13, ha="center", va="center",
            color="#c0392b",
        )


def _auto_layout(objects: list[str]) -> dict[str, tuple[float, float]]:
    """Assign (x, y) positions to objects using simple geometric layouts."""
    n = len(objects)
    if n == 0:
        return {}
    if n == 1:
        return {objects[0]: (0.0, 0.0)}
    if n == 2:
        return {objects[0]: (0.0, 0.0), objects[1]: (2.0, 0.0)}
    if n == 3:
        # Equilateral triangle
        return {
            objects[0]: (0.0, 0.0),
            objects[1]: (2.0, 0.0),
            objects[2]: (1.0, math.sqrt(3)),
        }
    if n == 4:
        # Square (top-left, top-right, bottom-left, bottom-right)
        return {
            objects[0]: (0.0, 2.0),
            objects[1]: (2.0, 2.0),
            objects[2]: (0.0, 0.0),
            objects[3]: (2.0, 0.0),
        }
    if n <= 6:
        # 2 rows
        cols = math.ceil(n / 2)
        pos = {}
        for i, obj in enumerate(objects):
            row = i // cols
            col = i % cols
            pos[obj] = (float(col * 2), float(-(row * 2)))
        return pos
    # General: circle
    pos = {}
    for i, obj in enumerate(objects):
        angle = 2 * math.pi * i / n
        pos[obj] = (math.cos(angle) * 2, math.sin(angle) * 2)
    return pos


def _parse_diagram_dsl(description: str) -> dict:
    """Parse the diagram DSL into objects, arrows, and commutes assertions."""
    objects: list[str] = []
    arrows: list[tuple[str, str, str]] = []
    commutes: list[str] = []

    for line in description.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("objects:"):
            objects = line.split(":", 1)[1].split()
        elif line.lower().startswith("arrows:"):
            arrow_str = line.split(":", 1)[1]
            for part in arrow_str.split(","):
                part = part.strip()
                # Formats: "f: A -> B" or "A -> B" or "f:A->B"
                m = re.match(r"(?:(\w+)\s*:\s*)?(\S+)\s*->\s*(\S+)", part)
                if m:
                    label, src, tgt = m.group(1) or "", m.group(2), m.group(3)
                    arrows.append((src.strip(), tgt.strip(), label.strip()))
        elif line.lower().startswith("commutes:"):
            commutes = [c.strip() for c in line.split(":", 1)[1].split(",")]

    if not objects and not arrows:
        return {"error": "Could not parse description. Expected 'objects: ...' and 'arrows: ...' lines."}

    # Infer objects from arrows if not declared
    if not objects:
        seen: dict[str, None] = {}
        for src, tgt, _ in arrows:
            seen[src] = None
            seen[tgt] = None
        objects = list(seen.keys())

    return {"objects": objects, "arrows": arrows, "commutes": commutes}


def _autoscale(ax: plt.Axes, positions: dict) -> None:
    """Set axis limits with padding."""
    if not positions:
        return
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    pad = 0.8
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
