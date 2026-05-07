import pytest
from fastmcp.utilities.types import Image
from math_commutative_diagrams.server import diagram_from_description, render_quiver


def _is_png(result) -> bool:
    """Each render tool returns [Image, "Saved to ..."]; verify the inline PNG."""
    if not isinstance(result, list) or not result:
        return False
    img = next((x for x in result if isinstance(x, Image)), None)
    path_block = next((x for x in result if isinstance(x, str)), None)
    return (
        img is not None
        and img.data is not None
        and len(img.data) > 1000
        and path_block is not None
        and path_block.startswith("Saved to ")
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
