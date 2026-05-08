---
name: math-function-intuition
description: Build intuition for a one-variable function by plotting it, sampling key values, finding critical points, and characterizing asymptotic behavior. Use when the user asks to "understand", "explore", "get a feel for", or "investigate" a single-variable function f(x), or when a function shows up in a problem and a quick mental model would help before going deeper.
---

# math-function-intuition

Build a quick mental model of a one-variable function `f(x)`. Output is a short synthesis the user can use to decide what's interesting before going deeper.

## When to use

- The user gives a function `f(x)` and asks to understand, explore, visualize, or get intuition for it.
- A function appears in a larger problem and a one-screen overview would clarify the next step.
- **Skip this skill** if the user only wants a plot (call `plot_function` directly) or only wants a derivative (call `sympy_diff` directly). The value of this skill is the *combination*; for a single primitive, go straight to the tool.

## Procedure

Follow these steps in order. Skip a step only if its output is obvious from a previous one.

### 1. Plot the function

Call `plot_function` over a sensible range.

- Default x-range: `-5..5`. Override when the function's natural domain is different:
  - `(0, ∞)` for `log`, `sqrt`, `1/x`-like → use `0.01..10`.
  - integers / discrete → tabulate via `batch_examples` instead of plotting.
  - oscillatory (`sin`, `cos`) → use enough range to show 2–3 periods.
- If the plot is hard to read because of large vertical range, plot again on a log scale or a narrower window.

### 2. Sample at notable points

Call `sympy_eval` to compute `f(0)`, `f(1)`, `f(-1)`, and any value the user mentioned. Numerical values anchor the plot.

Skip if `f` is obviously a polynomial in lowest-degree form (the values are immediate).

### 3. Find critical points

- Compute `f'(x)` with `sympy_diff(expression="<f>", variable="x", order=1)`.
- Solve `f'(x) = 0` with `sympy_solve(equations="<f_prime>", variables="x")`.
- For each real critical point `x₀`:
  - Evaluate `f(x₀)` with `sympy_eval`.
  - Evaluate `f''(x₀)` to classify (positive → local min, negative → local max, zero → inflection or higher-order; mention but don't over-investigate).

If `sympy_solve` returns symbolic expressions you can't easily read, evaluate numerically with `sympy_eval(expression="N(<expr>)")`.

### 4. Characterize asymptotic behavior

- `sympy_eval(expression="limit(<f>, x, oo)")` and `limit(<f>, x, -oo)` for behavior at infinity.
- Vertical asymptotes: any singularities in the domain. If the plot showed a spike or the function has `1/<expr>`, identify where `<expr> = 0` via `sympy_solve`.
- Skip step 4 if `f` is a polynomial: limits are obviously `±∞` and there are no vertical asymptotes.

### 5. Synthesize

Report 4–6 bullets:

- **Domain** (informal: where is `f` defined).
- **Critical points**, with classification (max / min / inflection).
- **Asymptotic behavior** (limits at `±∞`, vertical asymptotes).
- **Visual character** (one phrase: "monotone increasing", "single bump centered at 0", "oscillates with growing amplitude", etc.).
- **Anything surprising** the plot revealed (kinks, jumps, periodicity not obvious from the formula).

End with: "Want to dig into <X>?" pointing at the most interesting feature, so the user can steer next.

## Examples of triggers

The user says any of:

- "What does `x sin(1/x)` look like near 0?"
- "Help me understand `e^(-x²) cos(πx)`."
- "Get a feel for `(x³ - 3x) / (x² + 1)`."
- "I'm working with the function `<…>` and want to know its key features."

## Notes

- For piecewise functions, plot each branch separately or assemble via `Piecewise` in SymPy.
- Don't over-interpret numerical artifacts in the plot — confirm by symbolic evaluation if a feature looks suspicious.
- If the function depends on a parameter, fix the parameter to a plausible value first and mention that you did.
