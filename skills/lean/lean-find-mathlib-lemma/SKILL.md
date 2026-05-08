---
name: lean-find-mathlib-lemma
description: Find a Lean4/Mathlib lemma using a cascade of search tools — local project search, name search, type-pattern search, semantic search, and goal-directed search — stopping at the first useful match. Use when the user is in a Lean proof and asks "is there a lemma that says X" or "what's the name of the lemma about Y".
paths: ["**/*.lean", "**/lakefile.lean", "**/lean-toolchain"]
---

# lean-find-mathlib-lemma

When you need a Mathlib lemma but don't know its name, run a search cascade from cheap+local to expensive+semantic. Stop at the first match that fits the user's need.

## When to use

- The user is editing a Lean file and asks for a lemma by description ("is there one for `a * b = b * a`?", "find me the cancellation lemma for `Nat.sub`").
- The user is stuck on a Lean goal and needs a Mathlib lemma that applies.
- **Skip** if the user already named a candidate lemma — they want `lean_hover_info` directly, not a search.
- **Skip** if the user just wants generic Mathlib navigation — point them at `loogle` or `leansearch` directly.

## Procedure

Run these in order. Stop at the first step that returns a useful result.

### 1. Local search (free, project-aware)

Call `lean_local_search` with keywords or the lemma's statement fragment. This searches the user's current project and Mathlib snapshot via `rg`. Hits are usually exact name matches or short signature substrings.

Useful when:
- The user gave a partial name ("Nat.add_…").
- A specific token in the goal (an operator, a constructor) is searchable as text.

### 2. Natural-language search (Mathlib only)

Call `lean_leansearch` with a plain-English description of the lemma.

Useful when:
- The user described the lemma's *content* without naming structures ("the lemma that says continuous functions on a compact set are bounded").

Rate-limited (3/30s); avoid hammering.

### 3. Type-pattern search

Call `lean_loogle` with a type pattern using Mathlib's syntax. Examples:

- `?a * ?b = ?b * ?a` → commutativity lemmas
- `Continuous ?f → IsCompact ?s → IsCompact (?f '' ?s)` → image of compact under continuous
- `List.length _ = _ + 1` → length-suc lemmas

Useful when:
- The user can sketch the *shape* of the lemma even without knowing names.

This is the most precise search when you can express the pattern.

### 4. Semantic / conceptual search

Call `lean_leanfinder` for concept-driven search ("the spectral theorem", "Cauchy's integral formula", "fundamental theorem of arithmetic").

Useful when:
- The lemma is famous enough to have a recognizable name in math literature.
- Type-pattern search is hard because the lemma involves multiple structures.

### 5. Goal-directed search (when in a proof)

If the user is at a Lean position with an open goal, call `lean_state_search`. This sends the actual goal to Mathlib's premise selection and returns lemmas that *apply* to close (or simplify) the goal.

Useful as a last resort, or as a first resort when the user is stuck and not sure what they need.

### 6. Verify the candidate

Once you have a candidate name:

- Call `lean_hover_info` at the user's cursor (or pick a Lean position that imports Mathlib) on the candidate name to read its full signature.
- Confirm the universe levels, implicit/explicit arguments, and any side conditions match what the user needs.

## Synthesize

Report 1–3 candidate lemmas (more is noise) with:

- Fully qualified name (e.g. `Nat.add_comm`, `MeasureTheory.integral_add`).
- Signature, in compact form.
- One-line "this matches because…" explanation.
- The exact `apply <name>` or `rw [<name>]` snippet for the user to try.

## Examples of triggers

- "Find me the Mathlib lemma that says `(a + b)^2 = a^2 + 2*a*b + b^2`."
- "What's the lemma for taking the derivative of a sum?"
- "I need something like `IsCompact s → IsClosed s` — does that exist?"
- "Help, my goal is `f x = f y` and I have `x = y`."

## Notes

- Don't bypass the cascade. Local search is fastest and often hits — running `leansearch` first wastes a rate-limited slot.
- If the user is in a `Mathlib.Foo.Bar` file, biases toward lemmas in adjacent namespaces — name them first.
- When `loogle` returns hundreds of hits, the type pattern was too loose; refine with more constraints rather than scrolling.
- If the user's lemma genuinely doesn't exist in Mathlib, say so and offer to draft a `theorem` statement.
