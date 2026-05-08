# math-reasoning-tools

MCP tools for theorem proving and mathematical reasoning with Claude Code.

<p align="center">
  <img src="logo.png" width="300"/>
</p>

**Two layers:**
- **Tools** — MCP servers exposing primitive operations (evaluate this expression, plot this function, look up this lemma).
- **Skills** — markdown procedures that orchestrate several tools into common multi-step workflows (build intuition for a function, test a conjecture, audit a Lean proof). See [`skills/`](skills/).

**Three roles:**
1. **Curated catalog** — assessed references to every existing MCP tool relevant to formal proof and mathematical reasoning.
2. **Original servers** — new MCP servers filling the gaps: human-style intuition tools (visualization, example computation, diagram rendering, search) that pair with Lean4.
3. **Workflow skills** — multi-tool procedures captured as Claude Code skills.

## Philosophy

A human mathematician proves theorems by: drawing diagrams, computing small examples, searching the literature, and consulting a proof assistant. This repo gives Claude Code the same toolkit.

- Lean4 is the formal layer (via [lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp), included as a submodule)
- The original servers here are the intuition layer: compute, visualize, search, draw diagrams
- Everything speaks MCP so it integrates into any Claude Code workflow

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`brew install uv` or `pip install uv`)
- Clone with submodules: `git clone --recurse-submodules https://github.com/Sfgangloff/math-reasoning-tools`

### Install all servers

```bash
uv sync
```

### Register the servers globally

Run once after cloning. This discovers every server under `servers/` (and `external/`)
and writes them into the top-level `mcpServers` block of `~/.claude.json`, so they're
available in every Claude Code session — no per-project config needed:

```bash
python3 scripts/setup-mcp.py
```

The script then checks for the system-level binaries that some servers shell
out to (`ripgrep`, `poppler`, `pdflatex`, `elan`) and, for each one missing,
prints the exact install command for your OS and prompts before running it.
Use `--skip-deps` to skip the check, or `--yes` to auto-confirm every prompt.

| Binary | Used by | macOS (brew) | Debian/Ubuntu (apt) | Fedora (dnf) |
|--------|---------|--------------|---------------------|--------------|
| `rg` | `lean-lsp-mcp.lean_local_search` | `brew install ripgrep` | `apt-get install ripgrep` | `dnf install ripgrep` |
| `pdftoppm` | `commutative-diagrams` (PDF → PNG) | `brew install poppler` | `apt-get install poppler-utils` | `dnf install poppler-utils` |
| `pdflatex` | `commutative-diagrams.render_tikzcd` | `brew install --cask mactex-no-gui` | `apt-get install texlive-latex-base texlive-latex-extra texlive-pictures` | `dnf install texlive-scheme-medium texlive-collection-pictures` |
| `elan` | `lean-lsp-mcp.loogle` (local index) | official `elan-init.sh` | official `elan-init.sh` | official `elan-init.sh` |

To verify the servers boot correctly:

```bash
python3 scripts/check-mcp.py
```

**Re-run `setup-mcp.py` whenever:**
- You add a new server under `servers/` or `external/`.
- You **move or rename the repo** — the entries in `~/.claude.json` use absolute paths, so they break if the repo's location changes. Re-running rewrites them.

### Reload after editing a server

After editing a server's source, the running MCP process still holds the old code
until it's restarted. To force a reload of every server under `servers/`:

```bash
python3 scripts/reload-mcp.py
```

This terminates the live stdio process for each server (Claude Code respawns
them on the next tool call) and runs a quick boot/`tools/list` check against
the new code. Servers under `external/` (e.g. `lean-lsp-mcp`) are left alone —
they rarely change locally and reloading them costs LSP startup time. Pass
`--no-check` to skip the smoke test.

### Where generated images go

Tools that produce images (`plot_function`, `draw_graph`, `render_tikzcd`, …) write
the PNG to **`<your project root>/images/`** — i.e. the directory Claude Code was
launched from. The directory is created if it doesn't exist. Resolution order:

1. `MATH_TOOLS_IMAGE_DIR` env var (absolute path, overrides everything)
2. `CLAUDE_PROJECT_DIR/images` (set by Claude Code in some contexts)
3. `$PWD/images` (the launcher's working dir — works under `uv run --directory`)
4. `cwd/images` (last resort)

To override per-project, set `MATH_TOOLS_IMAGE_DIR` in your shell or in the
`env` block of the server entry in `~/.claude.json`.

### Manual config (alternative)

If you'd rather not use the auto-setup script, [`configs/`](configs/) contains
several pre-built profiles you can drop into a project's `.claude/mcp.json`:

| Profile | Use when |
|---------|----------|
| `minimal.json` | quick computations, no Lean, no plotting |
| `compute-session.json` | symbolic/numeric computation with plots |
| `search-session.json` | literature search, paper reading, formula rendering |
| `diagram-session.json` | diagram-heavy authoring (`render_tikzcd` etc.) |
| `lean-session.json` | active Lean4 work — proof + lemma discovery + paper reading |
| `lean4-only.json` | Lean4 only |
| `full-stack.json` | every server (largest tool surface) |

See [`docs/tools.md`](docs/tools.md) for the per-tool reference.

### Install the workflow skills

Skills are multi-tool procedures (e.g. "build intuition for a function", "audit a Lean
proof before commit"). They live in [`skills/`](skills/) and install via:

```bash
python3 scripts/setup-skills.py
```

This symlinks each skill into `~/.claude/skills/<name>/`. Idempotent.
Does **not** touch `~/.claude.json` — the MCP servers stay registered exactly as
`setup-mcp.py` left them. Tools and skills are independent layers; you can have
both, either, or neither.

```bash
python3 scripts/setup-skills.py --list      # show install status
python3 scripts/setup-skills.py --remove    # uninstall managed skills only
```

> If `~/.claude/skills/` did not previously exist, restart Claude Code once after
> the first install so the directory watcher picks it up. Subsequent edits to
> any `SKILL.md` propagate live.

See [`skills/README.md`](skills/README.md) for the full catalog.

## Original Servers

Five servers covering symbolic computation, visualization, search, diagram rendering, and proof navigation. See [docs/tools.md](docs/tools.md) for the full tool reference (47 tools total, all implemented):

- **math-compute** (11): SymPy + Z3 + OEIS + `conjecture_test` / `find_counterexample` for stress-testing claims
- **math-viz** (14): plots, graphs, posets, simplicial complexes, LaTeX rendering, phase portraits, implicit/region/integrand plots
- **math-search** (13): ArXiv search + paper-source/paper-text fetching, definition/citation/outline extraction, MathWorld/Wikipedia/zbMATH lookups, Loogle HTTP fallback
- **commutative-diagrams** (3): tikz-cd / Quiver / DSL → PNG
- **proof-explorer** (6): `sorry_map`, `tactic_history`, `lean_minimal_hypotheses`, plus `proof_tree`/`goal_explain`/`hypothesis_graph` (lean-lsp-mcp wrappers)

## Workflow Skills

Seven multi-tool procedures authored so far (more in `skills/README.md` under "Deferred"):

| Skill | What it does |
|---|---|
| `math-function-intuition` | Plot + key values + critical points + asymptotics for a 1-var function. |
| `math-explore-sequence` | OEIS lookup + further terms + growth plot for a sequence. |
| `math-test-conjecture` | Cascade examples → random sampling → structured search → SMT. |
| `math-explore-paper` | Outline + glossary + main results + citation graph for an arXiv paper. |
| `lean-find-mathlib-lemma` | Cascade local search → leansearch → loogle → leanfinder → state_search. |
| `lean-understand-goal` | Decode a stuck Lean goal: English explanation + hypothesis graph + minimal hypotheses + tactic history. |
| `lean-proof-checkpoint` | Pre-commit audit: build + sorry map + axiom audit. |

Authoring a new skill: see the "Adding a new skill" section of [`skills/README.md`](skills/README.md) and the design principles below it.

## Catalog

Assessed references to existing tools, organized by category:

- [Proof assistants](catalog/proof-assistants.md) — Lean4, Coq, Agda, Isabelle
- [Symbolic computation](catalog/symbolic-computation.md) — SymPy, SageMath, Wolfram, Z3
- [Visualization](catalog/visualization.md) — plotting, graphs, geometry
- [Formal verification](catalog/formal-verification.md) — SMT solvers, model checkers
- [Meta-lists](catalog/meta-lists.md) — curated indexes and academic surveys

## Running tests

```bash
uv run pytest servers/math-compute/tests/ servers/math-viz/tests/ \
              servers/commutative-diagrams/tests/ servers/proof-explorer/tests/ -v
```

Network-dependent tests (math-search) are marked `@pytest.mark.network` and skipped by default. Run them with:

```bash
uv run pytest servers/math-search/tests/ -v -m network
```

## Development

Each server has a FastMCP dev inspector:

```bash
cd servers/<name>
uv run fastmcp dev src/<package>/server.py
```

See [docs/architecture.md](docs/architecture.md), [docs/tool-design-principles.md](docs/tool-design-principles.md), and [docs/contributing.md](docs/contributing.md).

For the theoretical framing and the list of planned actions, see
[docs/research-model.md](docs/research-model.md) (state-machine model;
how current tools map onto typed research actions) and
[docs/research-roadmap.md](docs/research-roadmap.md) (running list of
research actions we plan to expose as tools).

## License

MIT
