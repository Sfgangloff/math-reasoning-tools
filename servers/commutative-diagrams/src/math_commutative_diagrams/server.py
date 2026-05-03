import base64
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

mcp = FastMCP("commutative-diagrams")

_DPI = 150
_SAVE_DIR: Path | None = Path(d) if (d := os.environ.get("MATH_TOOLS_IMAGE_DIR")) else None


def _maybe_save_png(raw: bytes, description: str) -> None:
    if _SAVE_DIR is None:
        return
    _SAVE_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", description)[:60].strip("_")
    (_SAVE_DIR / f"{int(time.time() * 1000)}_{slug}.png").write_bytes(raw)


def _fig_to_image(fig: plt.Figure, description: str) -> dict:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight")
    plt.close(fig)
    raw = buf.getvalue()
    _maybe_save_png(raw, description)
    return {"type": "image", "data": base64.b64encode(raw).decode(), "mimeType": "image/png", "alt": description}


@mcp.tool()
def render_tikzcd(tikzcd_source: str) -> dict:
    """Render a tikz-cd commutative diagram to PNG using pdflatex.
    Pass only the tikzcd environment body (without \\begin{tikzcd}...\\end{tikzcd}).
    Requires: pdflatex and the tikz-cd LaTeX package installed on the system.
    Example: tikzcd_source='A \\\\arrow[r, \"f\"] \\\\arrow[d, \"h\"] & B \\\\arrow[d, \"g\"] \\\\\\\\ C \\\\arrow[r, \"k\"] & D'"""
    if not shutil.which("pdflatex"):
        return {
            "type": "text",
            "text": (
                "pdflatex not found. Install TeX Live or MacTeX to use render_tikzcd.\n"
                "Alternatively, use diagram_from_description for a matplotlib-rendered fallback."
            ),
        }

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
            return {"type": "text", "text": "pdflatex timed out after 30s."}

        pdf_path = Path(tmpdir) / "diagram.pdf"
        if not pdf_path.exists():
            log = result.stdout[-1000:] if result.stdout else result.stderr[-1000:]
            return {"type": "text", "text": f"pdflatex failed:\n{log}"}

        try:
            from pdf2image import convert_from_path
            images = convert_from_path(str(pdf_path), dpi=200)
            if images:
                buf = BytesIO()
                images[0].save(buf, format="PNG")
                raw = buf.getvalue()
                _maybe_save_png(raw, "Commutative diagram (tikzcd)")
                return {"type": "image", "data": base64.b64encode(raw).decode(), "mimeType": "image/png", "alt": "Commutative diagram"}
        except ImportError:
            pass

        # Fallback: try to convert PDF with matplotlib
        return {
            "type": "text",
            "text": (
                f"PDF generated at {pdf_path} but pdf2image not installed for PNG conversion.\n"
                "Install: pip install pdf2image (also needs poppler)."
            ),
        }


@mcp.tool()
def render_quiver(quiver_json: str) -> dict:
    """Render a commutative diagram from Quiver (q.uiver.app) JSON export. Returns an image.
    Export from https://q.uiver.app by clicking Export → JSON, then paste here.
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
            return {"type": "text", "text": "Unrecognized Quiver JSON format."}

        nodes = payload.get("nodes", [])
        edges = payload.get("edges", [])
    except json.JSONDecodeError as e:
        return {"type": "text", "text": f"JSON parse error: {e}"}

    if not nodes:
        return {"type": "text", "text": "No nodes found in Quiver JSON."}

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
def diagram_from_description(description: str) -> dict:
    """Render a commutative diagram from a simple text description. Returns an image.
    Format (one per line):
      objects: A B C D
      arrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D
      commutes: g ∘ f = k ∘ h   (optional, shown as label)
    Example:
      objects: A B C D
      arrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D"""
    parsed = _parse_diagram_dsl(description)
    if "error" in parsed:
        return {"type": "text", "text": parsed["error"]}

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
