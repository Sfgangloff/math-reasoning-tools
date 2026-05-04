import gzip
import io
import re
import tarfile
import textwrap
import threading
import time
from typing import Optional

import feedparser
import httpx
from bs4 import BeautifulSoup
from fastmcp import FastMCP

mcp = FastMCP("math-search")

_HEADERS = {"User-Agent": "math-reasoning-tools/0.1 (educational; https://github.com/Sfgangloff/math-reasoning-tools)"}
_TIMEOUT = 15

# arXiv asks for at most one request per 3 seconds. Shared throttle for all
# arXiv-touching tools in this server.
_ARXIV_LOCK = threading.Lock()
_ARXIV_LAST_REQUEST = 0.0
_ARXIV_MIN_INTERVAL = 3.0


def _arxiv_throttle() -> None:
    global _ARXIV_LAST_REQUEST
    with _ARXIV_LOCK:
        wait = _ARXIV_MIN_INTERVAL - (time.time() - _ARXIV_LAST_REQUEST)
        if wait > 0:
            time.sleep(wait)
        _ARXIV_LAST_REQUEST = time.time()


def _arxiv_clean_id(arxiv_id: str) -> str:
    s = arxiv_id.strip()
    for prefix in (
        "https://arxiv.org/abs/", "http://arxiv.org/abs/",
        "https://arxiv.org/pdf/", "http://arxiv.org/pdf/",
        "arXiv:", "arxiv:",
    ):
        s = s.removeprefix(prefix)
    return s.removesuffix(".pdf")


def _arxiv_get_source_archive(arxiv_id: str) -> bytes:
    _arxiv_throttle()
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(f"https://arxiv.org/src/{arxiv_id}", headers=_HEADERS)
    r.raise_for_status()
    return r.content


def _extract_tex_files(raw: bytes) -> dict[str, str]:
    """Decode an arXiv source payload into a mapping of filename → tex content.

    arXiv hands back any of: a gzipped tar of project files, a gzip-of-a-single-tex,
    or (rarely) a bare .tex. Try each in turn.
    """
    files: dict[str, str] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            for m in tar.getmembers():
                if m.isfile() and m.name.endswith(".tex"):
                    f = tar.extractfile(m)
                    if f:
                        files[m.name] = f.read().decode("utf-8", errors="replace")
        if files:
            return files
    except (tarfile.ReadError, OSError):
        pass
    try:
        text = gzip.decompress(raw).decode("utf-8", errors="replace")
        if "\\documentclass" in text or "\\begin{document}" in text:
            files["main.tex"] = text
            return files
    except (OSError, gzip.BadGzipFile):
        pass
    try:
        text = raw.decode("utf-8", errors="replace")
        if "\\documentclass" in text or "\\begin{document}" in text:
            files["main.tex"] = text
    except UnicodeDecodeError:
        pass
    return files


_MATH_ENV_ALL = [
    "theorem", "lemma", "proposition", "corollary",
    "definition", "remark", "example", "proof",
]
_MATH_ENV_DEFAULTS = ["theorem", "lemma", "proposition", "definition"]


@mcp.tool()
def arxiv_search(query: str, max_results: int = 5, categories: str = "math") -> str:
    """Search ArXiv for papers. Returns titles, authors, abstracts, and URLs.
    categories: 'math' (all), or a specific subcategory like 'math.AG', 'math.NT', 'math.AT'.
    Example: query='étale cohomology motivic', categories='math.AG'"""
    if "." in categories:
        search_q = f"cat:{categories} AND all:{query}"
    elif categories == "math":
        # ArXiv doesn't support cat:math.* wildcard — use all math subcategories via ti/abs search
        search_q = f"all:{query}"
    else:
        search_q = f"cat:{categories} AND all:{query}"

    _arxiv_throttle()
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        r = client.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": search_q, "max_results": max_results, "sortBy": "relevance"},
            headers=_HEADERS,
        )
    r.raise_for_status()

    feed = feedparser.parse(r.text)
    if not feed.entries:
        return f"No ArXiv results for '{query}' in category '{categories}'."

    parts = []
    for e in feed.entries:
        title = re.sub(r"\s+", " ", e.title).strip()
        authors = [a.name for a in e.get("authors", [])]
        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
        arxiv_id = e.id.split("/abs/")[-1]
        abstract = textwrap.shorten(re.sub(r"\s+", " ", e.summary), width=250, placeholder="...")
        parts.append(f"**{title}**\n{author_str}\nhttps://arxiv.org/abs/{arxiv_id}\n{abstract}")

    return "\n\n---\n\n".join(parts)


@mcp.tool()
def arxiv_get(arxiv_id: str) -> str:
    """Retrieve metadata and abstract of an ArXiv paper by ID or URL.
    Example: arxiv_id='2401.12345' or 'https://arxiv.org/abs/2401.12345'"""
    arxiv_id = _arxiv_clean_id(arxiv_id)

    _arxiv_throttle()
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        r = client.get(
            "https://export.arxiv.org/api/query",
            params={"id_list": arxiv_id},
            headers=_HEADERS,
        )
    r.raise_for_status()

    feed = feedparser.parse(r.text)
    if not feed.entries:
        return f"Paper '{arxiv_id}' not found on ArXiv."

    e = feed.entries[0]
    title = re.sub(r"\s+", " ", e.title).strip()
    authors = [a.name for a in e.get("authors", [])]
    abstract = re.sub(r"\s+", " ", e.summary).strip()
    published = e.get("published", "")[:10]
    categories = ", ".join(t.get("term", "") for t in e.get("tags", []))

    return (
        f"**{title}**\n"
        f"Authors: {', '.join(authors)}\n"
        f"Published: {published}\n"
        f"Categories: {categories}\n"
        f"https://arxiv.org/abs/{arxiv_id}\n\n"
        f"{abstract}"
    )


@mcp.tool()
def arxiv_fetch_source(arxiv_id: str, filename: str = "") -> str:
    """Fetch the LaTeX source of an arXiv paper. Highest fidelity for theorem statements
    — environments like \\begin{theorem}...\\end{theorem} are intact (unlike PDF text).
    filename: path inside the source archive (e.g. 'main.tex'). If empty, picks the
    largest .tex file heuristically.
    Some older papers are PDF-only; falls back with a clear error in that case.
    Example: arxiv_id='2401.12345', filename=''"""
    arxiv_id = _arxiv_clean_id(arxiv_id)
    try:
        raw = _arxiv_get_source_archive(arxiv_id)
    except httpx.HTTPStatusError as e:
        return (
            f"arXiv source fetch for '{arxiv_id}' failed (status {e.response.status_code}). "
            "Some older papers are PDF-only — try arxiv_fetch_text instead."
        )
    files = _extract_tex_files(raw)
    if not files:
        return (
            f"No .tex files found in arXiv source for '{arxiv_id}'. "
            "The paper may be PDF-only — try arxiv_fetch_text."
        )
    if filename:
        if filename in files:
            return files[filename]
        for k, v in files.items():
            if k.endswith("/" + filename) or k == filename:
                return v
        return f"File '{filename}' not in source. Available: {', '.join(sorted(files))}"
    main_name, main_content = max(files.items(), key=lambda kv: len(kv[1]))
    others = sorted(k for k in files if k != main_name)
    suffix = f"\n\n[selected '{main_name}' (largest .tex). Other files: {', '.join(others)}]" if others else ""
    return main_content + suffix


@mcp.tool()
def arxiv_fetch_text(arxiv_id: str, pages: str = "") -> str:
    """Download an arXiv paper's PDF and return its extracted text via pymupdf.
    Math symbols are partially recoverable but lossy; prefer arxiv_fetch_source
    when LaTeX fidelity matters.
    pages: optional range like '3-7' or '5' to limit output size. Default: all pages.
    Example: arxiv_id='2401.12345', pages='1-3'"""
    arxiv_id = _arxiv_clean_id(arxiv_id)
    try:
        import fitz  # pymupdf
    except ImportError:
        return "pymupdf not installed. Install with: pip install pymupdf"

    _arxiv_throttle()
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        r = client.get(f"https://arxiv.org/pdf/{arxiv_id}", headers=_HEADERS)
    if r.status_code != 200:
        return f"arXiv PDF fetch for '{arxiv_id}' failed (status {r.status_code})."

    page_range: tuple[int, int] | None = None
    if pages.strip():
        m = re.match(r"^\s*(\d+)\s*(?:-\s*(\d+))?\s*$", pages)
        if not m:
            return f"Invalid pages format: '{pages}'. Use '3' or '3-7'."
        start = int(m.group(1)) - 1
        end = int(m.group(2)) - 1 if m.group(2) else start
        if start < 0 or end < start:
            return f"Invalid pages range: '{pages}'."
        page_range = (start, end)

    try:
        doc = fitz.open(stream=r.content, filetype="pdf")
    except Exception as e:
        return f"Failed to open PDF: {e}"

    try:
        n_pages = len(doc)
        if page_range:
            start, end = page_range
            if start >= n_pages:
                return f"Page {start + 1} out of range; PDF has {n_pages} pages."
            end = min(end, n_pages - 1)
            page_iter = range(start, end + 1)
        else:
            page_iter = range(n_pages)

        parts = []
        for i in page_iter:
            text = re.sub(r"\n{3,}", "\n\n", doc[i].get_text())
            parts.append(f"[Page {i + 1}]\n{text.strip()}")
    finally:
        doc.close()

    return "\n\n".join(parts) if parts else f"No text extracted from {arxiv_id}."


@mcp.tool()
def arxiv_extract_math(arxiv_id: str, kinds: Optional[list[str]] = None) -> str:
    """Extract named math environments from an arXiv paper's LaTeX source.
    kinds: subset of theorem, lemma, proposition, corollary, definition, remark,
    example, proof. Defaults to theorem/lemma/proposition/definition.
    Returns a numbered list with the kind, optional [name], any \\label{...},
    source filename, and the raw LaTeX body. Useful as input to a Lean4
    formalization task.
    Example: arxiv_id='2401.12345', kinds=['theorem', 'definition']"""
    arxiv_id = _arxiv_clean_id(arxiv_id)
    kinds = kinds or _MATH_ENV_DEFAULTS
    invalid = [k for k in kinds if k not in _MATH_ENV_ALL]
    if invalid:
        return f"Unknown environment kinds: {invalid}. Allowed: {_MATH_ENV_ALL}"

    try:
        raw = _arxiv_get_source_archive(arxiv_id)
    except httpx.HTTPStatusError as e:
        return f"arXiv source fetch for '{arxiv_id}' failed (status {e.response.status_code})."
    files = _extract_tex_files(raw)
    if not files:
        return f"No .tex files in arXiv source for '{arxiv_id}'."

    results: list[str] = []
    for fname, content in files.items():
        for kind in kinds:
            pattern = rf"\\begin\{{{kind}\}}(\[[^\]]*\])?(.*?)\\end\{{{kind}\}}"
            for m in re.finditer(pattern, content, flags=re.DOTALL):
                opt = (m.group(1) or "").strip("[]").strip()
                body = m.group(2).strip()
                label_m = re.search(r"\\label\{([^}]+)\}", body)
                label = label_m.group(1) if label_m else None
                header = f"[{kind.title()}"
                if opt:
                    header += f" — {opt}"
                if label:
                    header += f"  \\label={label}"
                header += f"  ({fname})]"
                results.append(f"{header}\n\\begin{{{kind}}}{m.group(1) or ''}{body[:4000]}\n\\end{{{kind}}}")

    if not results:
        return f"No matching environments {kinds} found in '{arxiv_id}'."
    return f"{len(results)} environment(s) found in '{arxiv_id}':\n\n" + "\n\n---\n\n".join(results)


@mcp.tool()
def loogle_search(query: str, max_results: int = 5) -> str:
    """Search Mathlib4 declarations via the Loogle HTTP service (loogle.lean-lang.org).
    No-Lean-install fallback — pure HTTP, no project context, no LSP.
    For project-aware Mathlib search inside an open Lean project, prefer the
    `loogle` tool from lean-lsp-mcp instead.
    Example: query='continuous linear map composition' or '#check Nat.add_comm'"""
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(
            "https://loogle.lean-lang.org/",
            params={"q": query},
            headers=_HEADERS,
            follow_redirects=True,
        )

    if r.status_code != 200:
        return (
            f"Loogle returned status {r.status_code}. "
            "Try installing lean-lsp-mcp for richer Mathlib search: https://github.com/oOo0oOo/lean-lsp-mcp"
        )

    soup = BeautifulSoup(r.text, "html.parser")

    # Loogle returns results in <li> elements inside a results container
    results = []
    for li in soup.select("li.result, li.hit, .results li")[:max_results]:
        text = li.get_text(separator=" ", strip=True)
        if text:
            results.append(text)

    # Fallback: grab any <code> blocks that look like Lean declarations
    if not results:
        for code in soup.find_all("code")[:max_results]:
            text = code.get_text(strip=True)
            if text and len(text) > 5:
                results.append(text)

    if not results:
        return (
            f"No Mathlib results found for '{query}'. "
            "The Loogle HTML format may have changed. "
            "Try lean-lsp-mcp for direct Mathlib search: https://github.com/oOo0oOo/lean-lsp-mcp"
        )

    return f"Mathlib4 results for '{query}':\n\n" + "\n\n".join(results)


@mcp.tool()
def mathworld_lookup(topic: str) -> str:
    """Look up a mathematical concept on Wolfram MathWorld.
    Example: topic='Riemann Zeta Function' or topic='Cayley Graph'"""
    slug = topic.strip().title().replace(" ", "")
    url = f"https://mathworld.wolfram.com/{slug}.html"

    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(url, headers=_HEADERS, follow_redirects=True)

    if r.status_code == 404:
        # Try lowercase slug
        slug_lower = topic.strip().replace(" ", "").lower()
        with httpx.Client(timeout=_TIMEOUT) as client:
            r = client.get(
                f"https://mathworld.wolfram.com/{slug_lower}.html",
                headers=_HEADERS,
                follow_redirects=True,
            )
        if r.status_code == 404:
            return (
                f"MathWorld article '{topic}' not found at {url}. "
                "Try a different capitalization or check https://mathworld.wolfram.com"
            )

    soup = BeautifulSoup(r.text, "html.parser")

    # Extract the main content div (MathWorld uses entry-content or similar)
    content_div = (
        soup.find("div", id="entry-content")
        or soup.find("div", class_="entry-content")
        or soup.find("div", id="main")
        or soup.find("article")
    )

    if content_div:
        # Remove script and style tags
        for tag in content_div.find_all(["script", "style", "img"]):
            tag.decompose()
        text = content_div.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Trim to first 1500 chars (MathWorld articles can be very long)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > 1500:
        text = text[:1500] + "\n\n[... truncated. Full article: " + r.url + "]"

    return f"**{topic}** — Wolfram MathWorld\n{r.url}\n\n{text}"


@mcp.tool()
def wikipedia_math(topic: str, section: str = "") -> str:
    """Retrieve a Wikipedia article on a mathematical topic.
    Example: topic='Spectral theorem', section='Finite-dimensional case'"""
    title = topic.replace(" ", "_")

    with httpx.Client(timeout=_TIMEOUT) as client:
        if section:
            # Use the full parse API to get a specific section
            r = client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "parse",
                    "page": title,
                    "prop": "sections|text",
                    "format": "json",
                },
                headers=_HEADERS,
            )
            data = r.json()
            if "error" in data:
                return f"Wikipedia article '{topic}' not found."

            # Find the section index
            sections = data.get("parse", {}).get("sections", [])
            section_idx = None
            for s in sections:
                if section.lower() in s.get("line", "").lower():
                    section_idx = s["index"]
                    break

            if section_idx is None:
                available = [s.get("line", "") for s in sections]
                return (
                    f"Section '{section}' not found in '{topic}'. "
                    f"Available sections: {', '.join(available[:10])}"
                )

            r2 = client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "parse",
                    "page": title,
                    "section": section_idx,
                    "prop": "text",
                    "format": "json",
                },
                headers=_HEADERS,
            )
            html = r2.json().get("parse", {}).get("text", {}).get("*", "")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all(["table", "sup", "span.mw-editsection"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        else:
            # Use the REST summary API for the intro
            r = client.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
                headers=_HEADERS,
            )
            if r.status_code == 404:
                return f"Wikipedia article '{topic}' not found."
            data = r.json()
            text = data.get("extract", "No content found.")

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > 2000:
        text = text[:2000] + "\n\n[... truncated]"

    url = f"https://en.wikipedia.org/wiki/{title}"
    return f"**{topic}** — Wikipedia\n{url}\n\n{text}"


@mcp.tool()
def oeis_search(query: str, max_results: int = 3) -> str:
    """Search OEIS by description or integer sequence terms.
    Example: query='1,1,2,3,5,8,13' (by terms) or query='number of spanning trees' (by description)"""
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(
            "https://oeis.org/search",
            params={"q": query, "fmt": "json"},
            headers=_HEADERS,
        )
    r.raise_for_status()

    data = r.json()
    # OEIS returns a plain list of sequences (no wrapper object)
    results: list = data if isinstance(data, list) else (data.get("results") or [])

    if not results:
        return f"No OEIS sequences found for '{query}'."

    parts = []
    for seq in results[:max_results]:
        a_num = f"A{seq.get('number', 0):06d}"
        name = seq.get("name", "(no name)")
        values = seq.get("data", "").split(",")[:15]
        formula = ""
        for entry in seq.get("formula", [])[:1]:
            formula = f"\nFormula: {entry[:200]}"
        parts.append(
            f"**{a_num}**: {name}\n"
            f"Terms: {', '.join(values)}{'...' if len(values) == 15 else ''}"
            f"{formula}\n"
            f"https://oeis.org/{a_num}"
        )

    return f"OEIS: {len(results)} result(s) for '{query}'\n\n" + "\n\n---\n\n".join(parts)


@mcp.tool()
def zbmath_search(query: str, max_results: int = 5) -> str:
    """Search zbMATH Open for papers and reviews.
    Supports field prefixes: ti: (title), au: (author), an: (ID), cc: (MSC class).
    Example: query='ti:étale cohomology cc:14F20' or query='au:Serre elliptic curves'"""
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(
            "https://api.zbmath.org/v1/document/_search",
            params={"search_string": query, "results_per_page": max_results},
            headers=_HEADERS,
        )

    if r.status_code != 200:
        return f"zbMATH API returned status {r.status_code}. Check https://zbmath.org for manual search."

    data = r.json()
    docs = data.get("result", [])
    if not docs:
        return f"No zbMATH results for '{query}'."

    parts = []
    for doc in docs[:max_results]:
        title = doc.get("title", {}).get("title", "(no title)")
        authors_list = doc.get("contributors", {}).get("authors", [])
        authors = ", ".join(a.get("name", "") for a in authors_list[:3])
        if len(authors_list) > 3:
            authors += " et al."
        year = doc.get("year", "")
        msc_codes = ", ".join(m.get("code", "") for m in doc.get("msc", [])[:3])
        url = doc.get("zbmath_url", "")
        parts.append(
            f"**{title}**\n"
            f"{authors} ({year})\n"
            f"MSC: {msc_codes}\n"
            f"{url}"
        )

    return "\n\n---\n\n".join(parts)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
