---
name: lean-understand-goal
description: Decode a Lean4 proof goal — explain the goal in plain English, map hypothesis dependencies, identify which hypotheses are actually load-bearing, and review tactic history. Use when the user is stuck on a Lean goal and asks "what is this goal saying?", "why am I stuck?", or "which of these hypotheses do I actually need?".
paths: ["**/*.lean", "**/lakefile.lean"]
---

# lean-understand-goal

When the user is staring at a Lean goal that isn't obvious, build a structured picture: what the goal says in English, which hypotheses contribute, and how the proof has evolved so far.

## When to use

- The user is in a Lean proof, has a complex goal up, and asks for help understanding it.
- The user has many hypotheses and isn't sure which ones matter.
- The user says "I'm stuck" or "what is this goal even saying?"
- **Skip** if the user just wants the goal printed — call `lean_goal` directly. The value of this skill is the *interpretation*, not the read.

## Procedure

You need a Lean file path and a line number (and optionally a column). Ask for them if not provided.

### 1. Read the goal

Call `lean_goal` at the position. Capture:

- The goal type.
- All hypotheses currently in scope (names + types).
- Any local definitions (`let` / `have`).

If the cursor is on an expression rather than between tactics, prefer `lean_term_goal`.

### 2. Explain the goal in English

Call `goal_explain` (from `proof-explorer`) for a plain-English rendering of what the goal is asking. This is most valuable when:

- The goal involves multiple universe-polymorphic structures.
- Implicit arguments are hiding the actual content.
- The goal is the negation or contrapositive of something more natural.

If `goal_explain` is unavailable or returns too little, paraphrase manually: "Show that for any `x : α` satisfying `P x`, we have `Q x`."

### 3. Map hypothesis dependencies

Call `hypothesis_graph` (proof-explorer) to see which hypotheses depend on which. This surfaces:

- Hypotheses that are unused so far (candidates to ignore).
- Hypotheses whose types reference each other (often need to be used together).
- The "trunk" of the local context — the few hypotheses everything else hangs on.

### 4. Identify load-bearing hypotheses

Call `lean_minimal_hypotheses` (lean-lsp-mcp version, not proof-explorer's) on the surrounding theorem. This tells you which named arguments of the theorem are actually used by the proof body.

Useful for:
- Cleaning up the theorem statement after a successful proof.
- Diagnosing which hypothesis is missing when a tactic fails (if the proof never used hypothesis `h`, it's probably not what the goal needs).

### 5. Review tactic history

Call `tactic_history` for the surrounding theorem. Read the recent edits to understand:

- What the user already tried.
- Which tactics narrowed the goal vs. branched it.
- Whether a previous step might be discarded for a cleaner path.

### 6. Synthesize

Report in this structure:

```
**Goal in English**: <one sentence>

**Hypotheses that matter** (1-3):
  - h₁ : <type> — provides <what>
  - h₂ : <type> — needed because <why>

**Hypotheses you can ignore for now** (the rest)

**What's been tried**: <one line summary from tactic_history>

**Suggested next move**: <one tactic + brief justification>
```

End with the one-line offer: "Want me to try `<tactic>` via `lean_multi_attempt`?"

## Examples of triggers

- "I'm stuck on this goal at line 47 of `Foo.lean`."
- "What is this goal even saying?"
- "Which of these 12 hypotheses do I actually need?"
- "Help me understand why the rewrite failed at line 23."

## Notes

- Don't run `goal_explain` and `hypothesis_graph` if the goal is trivially short (like `n + 0 = n` with no hypotheses) — diagnostic overhead, no payoff. Just read the goal and recommend a tactic.
- `lean_minimal_hypotheses` is slow; skip it if the surrounding theorem has only 1–2 arguments.
- If the user's proof has many `sorry`s nearby, also call `sorry_map` to see the broader proof structure.
