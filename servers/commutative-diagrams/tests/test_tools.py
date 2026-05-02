import base64
import pytest
from math_commutative_diagrams.server import diagram_from_description, render_quiver


def _is_png(result: dict) -> bool:
    return (
        isinstance(result, dict)
        and result.get("type") == "image"
        and result.get("mimeType") == "image/png"
        and len(base64.b64decode(result["data"])) > 1000
    )


def test_square_diagram():
    desc = "objects: A B C D\narrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D"
    assert _is_png(diagram_from_description(desc))


def test_triangle_diagram():
    desc = "objects: X Y Z\narrows: f: X -> Y, g: Y -> Z, h: X -> Z"
    assert _is_png(diagram_from_description(desc))


def test_two_object_diagram():
    desc = "objects: A B\narrows: f: A -> B"
    assert _is_png(diagram_from_description(desc))


def test_arrows_only_no_objects_line():
    # Objects should be inferred from arrows
    desc = "arrows: f: G -> H, g: H -> K"
    assert _is_png(diagram_from_description(desc))


def test_diagram_with_commutes():
    desc = (
        "objects: A B C D\n"
        "arrows: f: A -> B, g: B -> D, h: A -> C, k: C -> D\n"
        "commutes: g ∘ f = k ∘ h"
    )
    result = diagram_from_description(desc)
    assert _is_png(result)
