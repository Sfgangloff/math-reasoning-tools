import base64
import pytest
from math_viz.server import (
    draw_graph,
    draw_matrix,
    draw_poset,
    draw_simplicial_complex,
    plot_function,
    plot_parametric,
    plot_surface,
    render_latex,
)


def _is_png(result: dict) -> bool:
    return (
        isinstance(result, dict)
        and result.get("type") == "image"
        and result.get("mimeType") == "image/png"
        and len(base64.b64decode(result["data"])) > 1000
    )


def test_plot_function_single():
    assert _is_png(plot_function(["sin(x)"], x_min=-3.14, x_max=3.14))


def test_plot_function_multi():
    assert _is_png(plot_function(["sin(x)", "cos(x)", "x**2"], labels=["sin", "cos", "x²"]))


def test_plot_parametric_circle():
    assert _is_png(plot_parametric("cos(t)", "sin(t)"))


def test_plot_surface():
    assert _is_png(plot_surface("x**2 + y**2"))


def test_draw_graph_undirected():
    assert _is_png(draw_graph([["A", "B"], ["B", "C"], ["C", "A"]]))


def test_draw_graph_directed():
    assert _is_png(draw_graph([["A", "B"], ["B", "C"]], directed=True))


def test_draw_poset_divisibility():
    assert _is_png(draw_poset([["1", "2"], ["1", "3"], ["2", "6"], ["3", "6"]]))


def test_draw_simplicial_complex():
    assert _is_png(draw_simplicial_complex([["a", "b", "c"], ["b", "c", "d"], ["d", "e"]]))


def test_render_latex_fraction():
    result = render_latex(r"\frac{1}{2}")
    assert _is_png(result)


def test_render_latex_integral():
    result = render_latex(r"\int_0^\infty e^{-x^2} dx")
    assert _is_png(result)


def test_draw_matrix_identity():
    assert _is_png(draw_matrix([["1", "0"], ["0", "1"]]))


def test_draw_matrix_with_labels():
    assert _is_png(
        draw_matrix(
            [["a", "b"], ["c", "d"]],
            row_labels=["r1", "r2"],
            col_labels=["c1", "c2"],
            highlight_cells=[[0, 0], [1, 1]],
        )
    )
