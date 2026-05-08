# Contributing

## Adding to the catalog

The catalog is the lowest-friction contribution. To add or update an entry:

1. Find the relevant file in `catalog/` (proof assistants, symbolic computation, visualization, formal verification, or meta-lists).
2. Add a row to the table with: URL, brief description, tools exposed, install difficulty (1–5), and a one-line honest assessment.
3. If the tool is a primary recommendation, add it to `configs/full-stack.json`.

Keep assessments honest. "Stars but no recent commits" is worth noting.

## Adding a new original server

1. Create `servers/<name>/` following the layout in [architecture.md](architecture.md).
2. Write `pyproject.toml` using the template below.
3. Implement tools in `src/<package>/server.py` using FastMCP.
4. Add tests in `tests/test_tools.py` — at minimum one test per tool.
5. Add the server to the table in `README.md`.
6. Add a config snippet to `configs/full-stack.json`.
7. Update `CLAUDE.md` with: when to use the new tool and its tool names.

### pyproject.toml template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "math-<name>-mcp"
version = "0.1.0"
description = "MCP server for <purpose>"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=0.1.0",
    # add your deps here
]

[project.scripts]
math-<name>-mcp = "math_<name>.server:main"

[dependency-groups]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]
```

### Server template

```python
from fastmcp import FastMCP

mcp = FastMCP("math-<name>")

@mcp.tool()
def my_tool(input: str) -> str:
    """One-sentence description. Example input: 'x**2 + 1'"""
    ...

def main():
    mcp.run()

if __name__ == "__main__":
    main()
```

## Testing a server locally

```bash
cd servers/<name>
uv run fastmcp dev src/math_<name>/server.py
```

This starts an interactive MCP inspector in the terminal where you can call tools manually.

## Adding a new skill

A skill is a markdown procedure that orchestrates several MCP tools into a recurring multi-step workflow. Skills are *not* wrappers around individual tools.

1. **Verify it's actually a skill.** If the workflow is one tool call, it doesn't need a skill — Claude can call the tool directly. The bar: at least 2 tools, with a procedure that's worth capturing (cascade, stop-condition, synthesis step).
2. Create `skills/<category>/<skill-name>/SKILL.md`. Categories: `intuition/`, `conjecture/`, `paper/`, `lean/`, `diagram/` (add a new one if needed).
3. Use the frontmatter template below. Front-load the `description` with words the user would actually say so auto-invocation triggers.
4. Write the procedure body: numbered steps, name each tool explicitly (`call lean_loogle with X`, not `search Mathlib`), include skip-if conditions where appropriate.
5. Run `python3 scripts/setup-skills.py` to symlink it into `~/.claude/skills/`.
6. Test by triggering the description naturally in a Claude Code session (and via `/<skill-name>` for forced invocation).
7. Update the catalog in `skills/README.md` and `docs/skill-routing.md`.

### SKILL.md template

```markdown
---
name: math-<workflow-name>
description: <one sentence stating the procedure + when to use it; front-load words the user would say>
paths: ["**/*.lean"]   # optional — restrict auto-invoke to specific file types
---

# math-<workflow-name>

<one-paragraph framing>

## When to use
- <natural-language trigger 1>
- <natural-language trigger 2>
- **Skip** if <condition where a single tool would do>.

## Procedure

### 1. <step name>
Call `<tool_name>` with <args>. <why this step matters>.

### 2. <step name>
Call `<tool_name>` …

### N. Synthesize
Report in this structure:
<output template>

## Examples of triggers
- "<phrase 1>"
- "<phrase 2>"

## Notes
- <edge case or known limitation>
```

### Skill design principles

- **Procedure, not primitive.** If it's one tool call, delete it.
- **Name tools explicitly.** Specificity makes Claude follow the steps.
- **Triggerable description.** Words the user would actually use.
- **Stop-conditions matter.** Cascades stop at first hit; checks stop at first failure.
- **No scripts unless necessary.** Tools already do the work.

## Updating the catalog vs. building original tools

Prefer cataloging over building when:
- An existing tool already does the job well
- The only missing piece is documentation or a config snippet

Build original tools when:
- The capability genuinely does not exist in any existing tool
- Existing tools exist but have design problems that make them unsuitable (no base64 image output, no Lean4-compatible output format, unsafe eval, etc.)

## Commit style

```
catalog: add lean-aristotle-mcp to proof-assistants
server(math-compute): add batch_examples tool
docs: clarify evaluation security model
config: add minimal.json
```

Prefix: `catalog`, `server(<name>)`, `skill(<name>)`, `docs`, `config`, `fix`, `chore`.
