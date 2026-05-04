import gzip
import io
import tarfile

import pytest
from math_search.server import (
    _arxiv_clean_id,
    _extract_bibitems,
    _extract_tex_files,
    _first_sentence,
    _infer_defined_term,
    _walk_with_sections,
    arxiv_extract_citations,
    arxiv_extract_math,
    arxiv_extract_definitions,
    arxiv_get,
    arxiv_outline,
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


def test_infer_defined_term_prefers_optional_arg():
    assert _infer_defined_term("Banach space", "body") == "Banach space"


def test_infer_defined_term_falls_back_to_textbf():
    body = "Let $X$ be a \\textbf{topological group}, that is, ..."
    assert _infer_defined_term("", body) == "topological group"


def test_arxiv_extract_definitions_finds_term(monkeypatch):
    src = (
        b"\\begin{definition}[Banach space]\\label{def:banach}\n"
        b"A complete normed vector space.\n"
        b"\\end{definition}\n"
        b"\\begin{definition}\n"
        b"A \\textbf{filter} on a set is a non-empty family ...\n"
        b"\\end{definition}\n"
    )
    monkeypatch.setattr(
        "math_search.server._arxiv_get_source_archive",
        lambda _id: _make_targz({"paper.tex": src}),
    )
    out = arxiv_extract_definitions("0000.0000")
    assert "Banach space" in out
    assert "def:banach" in out
    assert "filter" in out


def test_walk_with_sections_attaches_citations_to_section():
    tex = (
        "\\section{Introduction}\n"
        "We discuss \\cite{smith2020}.\n"
        "\\subsection{Background}\n"
        "Per \\citep{jones1995}, the result follows.\n"
        "\\section{Main}\n"
        "Recall \\cite{smith2020,brown2010}.\n"
    )
    out = list(_walk_with_sections(tex))
    keys = [k for k, _ in out]
    assert keys == ["smith2020", "jones1995", "smith2020", "brown2010"]
    sections = [s for _, s in out]
    assert sections[0] == "Introduction"
    assert sections[1] == "Introduction / Background"
    assert sections[2] == "Main"
    assert sections[3] == "Main"


def test_extract_bibitems_basic():
    bbl = (
        "\\begin{thebibliography}{99}\n"
        "\\bibitem{smith2020} Smith, J. \\emph{On Foo}. Annals 2020.\n"
        "\\bibitem[Jones95]{jones1995} Jones, A. \\emph{On Bar}. JAMS 1995.\n"
        "\\end{thebibliography}\n"
    )
    out = _extract_bibitems(bbl)
    assert set(out) == {"smith2020", "jones1995"}
    assert "On Foo" in out["smith2020"]
    assert "On Bar" in out["jones1995"]


def test_arxiv_extract_citations_links_section_and_bib(monkeypatch):
    tex = (
        "\\section{Intro}\nUsing \\cite{smith2020}, we ...\n"
        "\\section{Main}\nNow \\citep{jones1995}.\n"
    )
    bbl = (
        "\\begin{thebibliography}{99}\n"
        "\\bibitem{smith2020} Smith. On Foo. 2020.\n"
        "\\bibitem{jones1995} Jones. On Bar. 1995.\n"
        "\\end{thebibliography}\n"
    )
    monkeypatch.setattr(
        "math_search.server._arxiv_get_source_archive",
        lambda _id: _make_targz({"paper.tex": tex.encode(), "paper.bbl": bbl.encode()}),
    )
    out = arxiv_extract_citations("0000.0000")
    assert "smith2020" in out
    assert "On Foo" in out
    assert "Intro" in out
    assert "Main" in out


def test_first_sentence_strips_label_and_commands():
    body = (
        "\\label{sec:intro}\n"
        "We prove that $f \\circ g = \\mathrm{id}$ in this section. "
        "Then more text follows."
    )
    s = _first_sentence(body)
    assert s.startswith("We prove that")
    assert s.endswith(".")


def test_arxiv_outline_renders_section_tree(monkeypatch):
    tex = (
        "\\documentclass{article}\\begin{document}\n"
        "\\section{Introduction}\n"
        "We study cohomology of toric varieties.\n"
        "\\subsection{Notation}\n"
        "Throughout, $X$ denotes a smooth projective variety.\n"
        "\\section{Main results}\n"
        "Our main theorem is the following.\n"
        "\\end{document}"
    )
    monkeypatch.setattr(
        "math_search.server._arxiv_get_source_archive",
        lambda _id: _make_targz({"main.tex": tex.encode()}),
    )
    out = arxiv_outline("0000.0000", depth=2)
    assert "Introduction" in out
    assert "Notation" in out
    assert "Main results" in out
    assert "We study cohomology" in out
    # subsection should be indented deeper
    assert out.find("    Notation") != -1


def test_arxiv_outline_rejects_bad_depth():
    assert "depth must" in arxiv_outline("0000.0000", depth=4)


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
