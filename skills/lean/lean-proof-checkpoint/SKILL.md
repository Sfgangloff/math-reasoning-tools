---
name: lean-proof-checkpoint
description: Pre-commit audit of a Lean4 project — build the project, list all sorries, audit axioms used by key theorems, and report what's safe to commit. Use when the user asks to "check before committing", "audit the proofs", "what's still incomplete", or before pushing a Lean PR.
paths: ["**/*.lean", "**/lakefile.lean", "**/lean-toolchain"]
---

# lean-proof-checkpoint

Run a structured audit of a Lean project's proof state before the user commits or pushes. Surfaces incomplete proofs (sorries), suspicious axioms, and build failures.

## When to use

- The user asks to audit, check, or verify the proof state of a Lean project before committing.
- The user is about to open a PR and wants confidence that nothing is half-finished.
- After a refactor, the user wants to confirm everything still goes through.
- **Skip** if the user just wants to know if a single theorem builds — call `lean_build` and read the output directly.

## Procedure

### 1. Build the project

Call `lean_build`. This rebuilds the project and restarts the LSP. Slow but necessary — without a clean build, the next steps may report stale state.

If the build fails:

- Read the error output.
- Stop the audit and report failures first. The user needs a green build before the rest of the audit means anything.

### 2. Inventory sorries

For each Lean file the user changed (or for the whole project if scope is unclear), call `sorry_map`. This returns:

- File path + line number of every `sorry` and `admit`.
- The surrounding theorem name.
- The local goal at the sorry.

Group by file and report counts.

### 3. Audit axioms on key theorems

For theorems the user marks as "the result" (or, if unmarked, the theorems mentioned in the recent git diff), call `lean_verify` with the fully qualified name.

`lean_verify` reports the axioms a theorem depends on. Flag:

- **`Classical.choice`** — present in many proofs, generally fine but worth noting.
- **`Quot.sound`**, **`propext`** — Lean's built-ins, expected.
- **Custom `axiom <name>`** declared in the project — these are real assumptions; verify they're intentional.
- **`sorryAx`** — means the proof transitively depends on a `sorry`. The theorem is *not* actually proved.

### 4. (Optional) Profile heavy proofs

If the build was slow or the user mentioned compile-time issues, call `lean_profile_proof` on the slowest theorems to identify tactic hotspots.

### 5. Synthesize

Report in this structure:

```
**Build**: <PASSED | FAILED with N errors>

**Sorries** (<N total>):
  - <file>:<line>  in `<theorem>` — goal: <one-line>
  ...

**Axioms used by key theorems**:
  - `<theorem>` depends on: [Classical.choice, …]
    ⚠ uses sorryAx — proof is incomplete via dependency.
  - `<theorem>` depends on: standard axioms only.
  ...

**Verdict**: <SAFE TO COMMIT | UNFINISHED — N sorries, M axiom issues>
```

End with concrete next-step pointers: "The two sorries in `Foo.lean` are in `lemma_X` and `theorem_Y` — want me to draft tactics for either?"

## Examples of triggers

- "Audit my Lean project before I commit."
- "Are all the proofs actually done?"
- "Check that nothing depends on sorry transitively."
- "Pre-PR review for the Lean changes."

## Notes

- Don't call `lean_verify` on every theorem in a large project — it's slow. Limit to theorems in the recent diff or those the user names.
- `sorry_map` catches `sorry` and `admit`; if the project uses custom incomplete-proof markers, grep for them separately.
- If `lean_build` reports unused imports or warnings, those are usually fine to ignore for the audit — focus on errors, sorries, and axioms.
- A theorem that depends on `sorryAx` is *not* proved. Be unambiguous about this in the report.
