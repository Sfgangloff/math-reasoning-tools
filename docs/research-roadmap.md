# Research-action roadmap

A growing list of research actions we plan to expose as tools. Each
entry pins down: action type, what it consumes
from the reasoning state, what it returns, and why it is worth
implementing. New entries get appended at the bottom.

The theoretical framing — what a "research action" is, how it relates
to the reasoning state, and why a tool earns a slot — lives in
`docs/research-model.md`. This file is the engineering-facing list of
actions still to build.

## 1. `search_natural_deductions` — proof-oriented / exploratory

**Goal.** Given a target theorem with hypotheses `H₁, …, Hₙ` and goal
`G`, return the immediate non-trivial consequences obtainable from the
`Hᵢ` by one or two steps of forward reasoning.

**Inputs.**
- The hypotheses (as a list of Lean4 propositions or informal
  statements with types).
- Optionally, the goal `G` (used only for ranking — see below).
- A search depth (default: 1; bounded small).

**Outputs.** A ranked list of derived propositions, each with:
- the lemma / inference rule that produced it,
- the hypotheses it used,
- a relevance score against `G` if `G` was supplied.

**What it does.** For each `Hᵢ`:
1. Apply elimination rules of its top-level connective
   (destructure conjunctions, instantiate existentials with fresh
   metavariables, project out fields of structures).
2. Search Mathlib (via `lean_loogle` / `lean_hammer_premise`) for
   lemmas whose premises match `Hᵢ` (or a tuple of `Hⱼ`) up to
   unification.
3. Apply each matching lemma to obtain a new proposition.

The output is meant to be browsable: the agent reads it the way a human
mathematician reads "what do the hypotheses give us?" at the start of a
proof. It is not a tactic — it does not change the proof state — but it
sharply concentrates the policy on candidate next moves.

**Status.** Not implemented. Likely fits in `proof-explorer` (it leans
on Lean LSP for unification) and would compose `lean_hammer_premise`
with a small forward-chaining loop. Worth scoping as a separate
sub-server if the search infrastructure grows.

## 2. — *(reserved for the next entry)*

Append new actions here. Each entry should follow the schema of §1:
*goal, inputs, outputs, what it does, why it earns a slot, status*.
