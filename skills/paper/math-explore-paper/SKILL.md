---
name: math-explore-paper
description: Build a structured map of an arXiv paper — outline, glossary of definitions, list of theorems, and citation graph — so the user can decide whether to read it in full and where to enter. Use when the user gives an arXiv ID or title and asks what's in the paper, what it says, or whether it's relevant.
---

# math-explore-paper

Given an arXiv paper, produce a structured overview the user can read in 60 seconds and decide whether (and where) to dive deeper.

## When to use

- The user gives an arXiv ID and asks "what's in this paper?", "is this relevant to X?", "summarize this paper".
- The user is doing a literature review and wants a quick orientation on a specific paper.
- **Skip** if the user just wants the abstract (call `arxiv_get` directly) or only the references (call `arxiv_extract_citations` directly). The value here is the *combination*.

## Procedure

### 0. Resolve the paper

If the user gave a title or topic (not an arXiv ID), first call `arxiv_search` to find candidates and confirm with the user before continuing.

If the user gave an arXiv ID, proceed.

### 1. Metadata + abstract

Call `arxiv_get` to get title, authors, abstract, categories, and submission date. This anchors everything that follows.

### 2. Outline

Call `arxiv_outline` (depth 2 by default) to extract section + subsection structure. This shows how the argument is organized — useful for deciding which section to read first.

### 3. Glossary

Call `arxiv_extract_definitions` to pull every `\begin{definition}...\end{definition}` (and similar environments). Returns a list of terms with their formal definitions.

This is where the paper's vocabulary lives. If a term in the user's question appears here, you've found the entry point.

### 4. Theorems & main results (optional)

If the user asked specifically about results, also call `arxiv_extract_math` (kinds: theorems, propositions, lemmas) to get the formal statements.

### 5. Citation graph

Call `arxiv_extract_citations` to get the bibliography. Skim it for:

- **Self-references**: prior work by the same authors → likely a series.
- **Foundational citations**: highly-cited classics → tells you the paper's intellectual lineage.
- **Recent arXiv citations**: show what the paper builds on.

Don't enumerate the whole bibliography — flag the 3–5 most informative entries.

### 6. Synthesize

Report in this structure:

```
**Paper**: <title>
**Authors / Date**: <…>
**Categories**: math.<…>

**One-line summary**: <distilled from abstract>

**Outline** (top-level only):
  1. <section>
  2. <section>
  ...

**Key definitions** (3-5, the load-bearing ones):
  - <term>: <one-line gloss>
  ...

**Main results** (if extracted):
  - Thm <n>: <one-line statement>
  ...

**Lineage** (3-5 cited works that anchor it):
  - <citation> — why it matters here
  ...

**Where to enter**: <recommend a section based on the user's question>
```

End with a one-line offer: "Want me to extract the full statement of Theorem N / formalize Definition M / find a Mathlib equivalent?" so the user can steer.

## Examples of triggers

- "What's in arXiv 2106.04015?"
- "Summarize https://arxiv.org/abs/2401.12345 — is this about formalizing measure theory?"
- "Explore arXiv 1812.01193, I'm looking for results about <topic>."

## Notes

- If `arxiv_fetch_source` is needed (LaTeX source for deeper extraction), only fetch when an extraction tool fails on the abstract/HTML alone — full source is heavy.
- Don't summarize the whole paper. The user can read the abstract themselves; your job is structure + entry points.
- If the paper has been superseded (e.g. a later version on arXiv), call this out — the user might be looking at an outdated version.
