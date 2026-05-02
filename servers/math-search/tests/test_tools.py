import pytest
from math_search.server import arxiv_search, arxiv_get, oeis_search, wikipedia_math, zbmath_search


@pytest.mark.network
def test_arxiv_search_returns_results():
    result = arxiv_search("spectral sequences", max_results=2)
    assert "arxiv.org" in result
    assert "---" in result or "**" in result


@pytest.mark.network
def test_arxiv_get_by_id():
    result = arxiv_get("math/9807080")  # classic Kontsevich paper
    assert "arxiv.org" in result


@pytest.mark.network
def test_oeis_search_fibonacci():
    result = oeis_search("1,1,2,3,5,8,13", max_results=1)
    assert "A000045" in result
    assert "Fibonacci" in result


@pytest.mark.network
def test_wikipedia_math_summary():
    result = wikipedia_math("Cauchy sequence")
    assert "Cauchy" in result
    assert "wikipedia.org" in result


@pytest.mark.network
def test_zbmath_search_returns_results():
    result = zbmath_search("cohomology sheaves", max_results=2)
    assert "zbmath.org" in result
