import gzip
import io
import tarfile

import pytest
from math_search.server import (
    _arxiv_clean_id,
    _extract_tex_files,
    arxiv_extract_math,
    arxiv_get,
    arxiv_search,
    oeis_search,
    wikipedia_math,
    zbmath_search,
)


def test_arxiv_clean_id_strips_prefixes():
    assert _arxiv_clean_id("2401.12345") == "2401.12345"
    assert _arxiv_clean_id("https://arxiv.org/abs/2401.12345") == "2401.12345"
    assert _arxiv_clean_id("arXiv:2401.12345") == "2401.12345"
    assert _arxiv_clean_id("https://arxiv.org/pdf/2401.12345.pdf") == "2401.12345"
    assert _arxiv_clean_id("math/0601234") == "math/0601234"


def _make_targz(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for name, data in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_extract_tex_files_from_targz():
    raw = _make_targz({
        "paper.tex": b"\\documentclass{article}\n\\begin{document}hello\\end{document}",
        "extra.bib": b"@article{x, title={y}}",
    })
    files = _extract_tex_files(raw)
    assert list(files) == ["paper.tex"]
    assert "documentclass" in files["paper.tex"]


def test_extract_tex_files_from_plain_gzip():
    payload = b"\\documentclass{article}\n\\begin{document}hi\\end{document}"
    raw = gzip.compress(payload)
    files = _extract_tex_files(raw)
    assert files == {"main.tex": payload.decode()}


def test_arxiv_extract_math_finds_theorems(monkeypatch):
    src = (
        b"\\begin{theorem}[Pythagoras]\\label{thm:pyth}\n"
        b"$a^2 + b^2 = c^2$.\n"
        b"\\end{theorem}\n\n"
        b"\\begin{lemma}\nA lemma body.\\end{lemma}\n"
        b"\\begin{remark}\nIgnored by default.\\end{remark}\n"
    )
    monkeypatch.setattr(
        "math_search.server._arxiv_get_source_archive",
        lambda _id: _make_targz({"paper.tex": src}),
    )
    out = arxiv_extract_math("0000.0000")
    assert "Theorem" in out
    assert "Pythagoras" in out
    assert "thm:pyth" in out
    assert "Lemma" in out
    # remark is not in defaults
    assert "Remark" not in out


def test_arxiv_extract_math_rejects_unknown_kinds():
    out = arxiv_extract_math("0000.0000", kinds=["bogus"])
    assert "Unknown environment kinds" in out


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
