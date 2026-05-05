# Research model

This document grounds the repository in the state-machine framework
described in `article.txt` ("Beyond Proof Artifacts: Mathematical
Research as Exploration Compression"). It pins down the *simplified*
(non-hierarchical) version of the model that this repo currently
implements — agent + typed research actions — and shows how the
existing tools project onto that model.

The running list of research actions we plan to expose as tools lives
in `docs/research-roadmap.md` (split out so this document stays the
theoretical reference).

The full framework adds a second layer on top: macro-action discovery,
concept formation as MDP homomorphism, and the resulting hierarchy of
actions. That layer is **out of scope here** and is treated as a future
extension once typed-trajectory data becomes available.

## 1. The simplified model

```
        ┌────────────────────────┐
        │     reasoning state    │
        │  - target              │
        │  - commitments         │
        │  - hypotheses          │
        │  - evidence            │
        │  - representations     │
        │  - history             │
        └───────────┬────────────┘
                    │   selects
                    ▼
        ┌────────────────────────┐         ┌──────────────┐
        │   research action a    │ ──────▶ │     tool     │
        │   (typed transition)   │         │  (MCP call)  │
        └───────────┬────────────┘         └──────┬───────┘
                    │                             │
                    └─────────── updates ─────────┘
                                  ▼
                       new reasoning state S'
```

In the agent paradigm:
- **Agent** = the Claude Code session.
- **Reasoning state** = the agent's belief state (notes, scratchpad, open
  goals, prior failures — both in the conversation and in the working tree).
- **Research action** = a typed transition `T_a : S → S'` (article §2.2,
  seven types: exploratory, representational, conceptual, conjectural,
  proof-oriented, validation, retrieval).
- **Tool** = the executable that performs `T_a` on demand.
- **Policy** = how the agent picks the next action given `S`.
  This is the object the framework asks AI systems to learn; it is *not*
  what the tools provide. The tools provide the action *space*.

The simplification (relative to the full article) is that we treat the
action set `A` as flat: no macro-actions, no learned compressions, no
concept formation. Each tool corresponds to a primitive action or a
sub-action (article §2.2, "subaction decomposition") that the agent can
freely interleave within a deliberate action.

## 2. How the current tools map to action types

This is the projection of the existing repo onto the article's
taxonomy. Empty cells flag where the action space is under-served.

| Action type        | Existing tools (this repo + lean-lsp-mcp)                                                                          |
|--------------------|--------------------------------------------------------------------------------------------------------------------|
| Exploratory        | `batch_examples`, `sympy_eval`, `oeis_lookup`, plot/draw family                                                    |
| Representational   | `sympy_factor`, `sympy_expand`, `render_latex`, `render_tikzcd`, `render_quiver`, `diagram_from_description`       |
| Conceptual         | — (no tool helps the agent *decide what to define*)                                                                |
| Conjectural        | `conjecture_test`, `find_counterexample` (these *test* a conjecture; nothing yet *formulates* one)                 |
| Proof-oriented     | `lean_*` (lean-lsp-mcp), `proof_tree`, `tactic_history`, `sorry_map`                                               |
| Validation         | `z3_check`, `find_counterexample`, `lean_verify`, `lean_minimal_hypotheses`                                        |
| Retrieval          | `arxiv_search`, `arxiv_fetch_*`, `arxiv_extract_*`, `arxiv_outline`, `mathworld_lookup`, `wikipedia_math`, `zbmath_search`, `loogle_search`, `lean_leansearch`, `lean_loogle`, `lean_state_search`, `lean_hammer_premise`, `lean_leanfinder` |

Two visible gaps: conjecture *formulation* (not just testing) and the
conceptual action type as a whole. The retrieval column is well-covered.

## 3. What a "good" tool looks like in this model

A tool earns its place by being an executor for a typed action — i.e.
it consumes a (sub-)slice of the reasoning state and returns a typed
output that fits cleanly into one of the six state components. The tool
design principles in `docs/tool-design-principles.md` are the operational
constraints (Lean-friendly output, statelessness, fail loudly, etc.);
this document is the *theoretical* constraint: every tool should be
nameable as an action type.

A consequence is that pure utility helpers (e.g. "format this as
markdown") do not belong in this catalog: they are not transitions on
the reasoning state.

## 4. Relation to existing repo documents

- `docs/architecture.md` — how the servers fit together at the systems
  level. Orthogonal to this document.
- `docs/tool-design-principles.md` — operational constraints on any
  tool (return shape, statelessness, security). This document is the
  *theoretical* sibling: which actions deserve a tool at all.
- `docs/research-roadmap.md` — the running list of research actions
  we plan to expose as tools. Sibling to this document: this one says
  *what counts* as an action; the roadmap says *which ones* we plan
  to build.
