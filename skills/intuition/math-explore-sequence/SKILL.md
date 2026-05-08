---
name: math-explore-sequence
description: Investigate an integer or rational sequence — try to identify it via OEIS, generate further terms, and plot its growth. Use when the user gives a sequence by formula, recursive rule, generating function, or by listing the first few terms and asks what it is or what it does.
---

# math-explore-sequence

Given a sequence, build a quick picture: does it match a known sequence, how does it grow, what are the next terms?

## When to use

- The user gives an explicit list of terms ("1, 2, 5, 14, 42, ...") and asks what it is.
- The user gives a recurrence or formula and wants to see how it behaves.
- A sequence shows up in a problem and identifying it would unlock a closed form.
- **Skip** if the user just wants the next term computed (call `batch_examples` directly) or just an OEIS lookup with terms already in hand (call `oeis_lookup` directly).

## Procedure

### 1. Identify via OEIS

If the user gave numerical terms:

- Call `oeis_lookup` with at least 6 terms (more is better; OEIS matches on subsequence).

If the user gave only a description ("the sequence of … numbers"):

- Call `oeis_search` with the description.

Record the OEIS A-number, name, and any closed form / generating function OEIS reports.

### 2. Generate more terms

Whether or not OEIS matched:

- If the user gave a formula or recurrence, call `batch_examples` with that expression for `n=1..20` (or whatever range makes sense).
- Confirm the generated terms agree with the user-supplied initial terms — mismatch means the formula was misread or a sign convention differs.

### 3. Plot growth

Pick the right plot for the sequence's nature:

- Smooth growth (polynomial, exponential, factorial) → `plot_function` with a closed form if available, else plot the generated `(n, a_n)` pairs as a discrete scatter.
- Summable / cumulative behavior → `plot_partial_sums`.
- For exponential/factorial growth, plot on a log scale so the shape is visible.

### 4. Synthesize

Report 3–5 bullets:

- **Identification**: OEIS A-number and name (or "no OEIS match").
- **Closed form / recurrence** if known.
- **Growth class**: polynomial of degree ~k, exponential base ~b, factorial-like, etc. Use the plot to motivate the claim.
- **Next few terms** beyond what the user gave.
- **Pointer**: if OEIS gave a generating function or a famous formula, name it ("this is the Catalan numbers — closed form `C_n = (2n choose n) / (n+1)`").

## Examples of triggers

- "What's 1, 2, 5, 14, 42, 132, ...?"
- "I have `a_n = a_{n-1} + a_{n-2}` with `a_0 = 2, a_1 = 1`. What is this?"
- "Explore the sequence `n^2 - n + 41` for `n = 1..20`."
- "Help me identify this sequence."

## Notes

- If `oeis_lookup` returns multiple matches, check term-by-term agreement rather than picking the top hit blindly.
- For sequences over rationals or reals, OEIS is unlikely to help — skip step 1 and rely on `batch_examples` + plotting.
- If the sequence appears to satisfy a polynomial relation but OEIS misses it, try shifting the index (sometimes off-by-one matters).
