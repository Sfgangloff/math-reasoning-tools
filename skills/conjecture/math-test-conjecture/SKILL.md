---
name: math-test-conjecture
description: Stress-test a mathematical conjecture by cascading from cheap to expensive checks — small examples, random sampling, structured counterexample search, and (when applicable) SMT verification. Use when the user states a "for all" claim, asks "is it true that...", or wants evidence before attempting a proof.
---

# math-test-conjecture

Given a conjecture, run a cascade of increasingly thorough checks. Stop at the first failure (counterexample) or summarize the strength of evidence if all checks pass.

## When to use

- The user says "is it true that ∀x, P(x)?", "I conjecture that…", "does this always hold?"
- Before attempting a proof, the user wants confidence the statement is even true.
- The user asks for a counterexample to a claim.
- **Skip** if the user already knows the claim is true and just wants a proof — go to a Lean skill instead.

## Procedure

Run steps in order. **Stop and report immediately** if any step finds a counterexample.

### 1. Small examples

Call `batch_examples` for the first ~20 inputs in the natural domain (n=1..20 for naturals, ±5 for integers, etc.).

This catches obvious base-case failures and also clarifies what the conjecture means.

### 2. Random sampling

Call `conjecture_test` with a sampling spec appropriate to the domain:

- `naturals`, `integers`, `rationals`, `polynomials_1var`, etc.
- Sample size 1000 by default; bump to 10000 if step 1 passed cleanly and the claim is suspicious.

A pass at this step doesn't prove anything — it just says "no counterexample within random N samples".

### 3. Structured counterexample search

Call `find_counterexample` with a structured enumeration over the domain. This is more thorough than random sampling at small sizes — it covers every input up to some size bound systematically.

If steps 1–2 passed and step 3 also passes for size ≤ N, the claim has substantial evidence (but is not proven).

### 4. SMT check (only if applicable)

If the conjecture is in a decidable fragment — quantifier-free, linear arithmetic over integers/reals, bit-vectors, etc. — call `z3_check` to ask the SMT solver to verify or refute.

`z3_check` returning **unsat** = proven. Returning **sat** = counterexample found. Returning **unknown** = SMT couldn't decide; rely on previous steps.

Skip this step if the conjecture involves transcendental functions, unbounded quantifiers, or constructs Z3 doesn't natively handle.

### 5. Synthesize

If a counterexample was found at any step:

- Report the smallest counterexample.
- State which step found it and at what size/sample.
- (Optional) Walk through why the conjecture fails on that input.

If all applicable steps passed:

- Report: "No counterexample in [examples / N random samples / structured search up to size K / SMT verification (if z3 was unsat)]".
- Be honest about what is and isn't proof. Random + structured + SMT-unsat = proof. Random + structured but no SMT = strong evidence, not proof.

## Examples of triggers

- "Is it true that for all primes p > 2, p² ≡ 1 mod 8?"
- "Conjecture: every even integer > 2 is a sum of two primes."
- "Test whether `n³ - n` is divisible by 6 for all integers n."
- "Find a counterexample to: every triangle inequality holds in ℤ_n addition."

## Notes

- If the conjecture has a parameter the user didn't fix, ask before sampling — random parameter choice can hide failures.
- For statements involving an existential ("there exists x such that…"), this skill flips: search for an example via `find_counterexample` on the negation, or directly with `batch_examples`.
- Goldbach-style conjectures: even with billions of confirming cases, not proof. Be explicit.
