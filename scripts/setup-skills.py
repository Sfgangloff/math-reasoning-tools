#!/usr/bin/env python3
"""Discover all skills in this repo and symlink them into ~/.claude/skills/.

Walks `skills/**/` for any directory containing a `SKILL.md`. Each such
directory is symlinked to `~/.claude/skills/<dir-name>/` so Claude Code
picks it up globally (and live edits in the repo propagate immediately).

A registry file at `~/.claude/skills/.math-reasoning-tools-managed.json`
tracks the skills we manage, so `--remove` only tears down what this script
installed — never user-installed or third-party skills sharing the directory.

Does NOT touch ~/.claude.json. MCP servers stay as the user configured them.
This script is independent of `setup-mcp.py`.
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "skills"
SKILLS_DST = Path.home() / ".claude" / "skills"
REGISTRY = SKILLS_DST / ".math-reasoning-tools-managed.json"
CLAUDE_MD = Path.home() / ".claude" / "CLAUDE.md"
ROUTING_MD = REPO_ROOT / "docs" / "skill-routing.md"
ROUTING_BEGIN = "<!-- BEGIN math-reasoning-tools-skills (managed by setup-skills.py) -->"
ROUTING_END = "<!-- END math-reasoning-tools-skills -->"


def discover_skills() -> dict[str, Path]:
    """Return {skill_name: source_dir} for every directory under skills/ that
    contains a SKILL.md. Skill name = directory name."""
    found: dict[str, Path] = {}
    if not SKILLS_SRC.exists():
        return found
    for skill_md in SKILLS_SRC.rglob("SKILL.md"):
        skill_dir = skill_md.parent
        name = skill_dir.name
        if name in found:
            print(
                f"warning: duplicate skill name {name!r} at {skill_dir} "
                f"(already seen at {found[name]}); skipping the duplicate.",
                file=sys.stderr,
            )
            continue
        found[name] = skill_dir
    return found


def load_registry() -> dict:
    if not REGISTRY.exists():
        return {"managed": []}
    try:
        with open(REGISTRY) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"warning: {REGISTRY} is not valid JSON; treating as empty.", file=sys.stderr)
        return {"managed": []}
    if "managed" not in data or not isinstance(data["managed"], list):
        data["managed"] = []
    return data


def save_registry(data: dict) -> None:
    SKILLS_DST.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def is_our_symlink(target: Path, expected_src: Path) -> bool:
    """True if `target` is a symlink whose resolved path equals `expected_src`."""
    if not target.is_symlink():
        return False
    try:
        return target.resolve() == expected_src.resolve()
    except OSError:
        return False


def install(skills: dict[str, Path], registry: dict) -> None:
    SKILLS_DST.mkdir(parents=True, exist_ok=True)
    managed: set[str] = set(registry["managed"])

    installed = 0
    repaired = 0
    skipped: list[str] = []

    for name, src in sorted(skills.items()):
        dst = SKILLS_DST / name

        if dst.is_symlink():
            if is_our_symlink(dst, src):
                # Already correct.
                managed.add(name)
                continue
            # Symlink to a different location — repair if we own it,
            # otherwise warn and skip.
            if name in managed:
                dst.unlink()
                dst.symlink_to(src, target_is_directory=True)
                repaired += 1
                continue
            skipped.append(
                f"{name}: existing symlink to {dst.resolve()} (not ours); skipping"
            )
            continue

        if dst.exists():
            # Real directory or file at that path — never overwrite something
            # the user (or another tool) put there.
            skipped.append(f"{name}: existing non-symlink at {dst}; skipping")
            continue

        dst.symlink_to(src, target_is_directory=True)
        managed.add(name)
        installed += 1

    registry["managed"] = sorted(managed)
    save_registry(registry)

    print(f"\nInstalled: {installed}  Repaired: {repaired}  Already present: "
          f"{len(skills) - installed - repaired - len(skipped)}")
    if skipped:
        print(f"\nSkipped {len(skipped)}:")
        for line in skipped:
            print(f"  - {line}")


def remove(registry: dict) -> None:
    managed = list(registry["managed"])
    removed = 0
    missing = 0
    foreign = 0

    for name in managed:
        dst = SKILLS_DST / name
        if not dst.exists() and not dst.is_symlink():
            missing += 1
            continue
        if not dst.is_symlink():
            # Something else replaced our symlink with real content; do not delete.
            foreign += 1
            print(f"  - {name}: not a symlink anymore at {dst}; leaving it alone.")
            continue
        dst.unlink()
        removed += 1

    registry["managed"] = []
    save_registry(registry)
    print(
        f"\nRemoved: {removed}  Already gone: {missing}  "
        f"Left in place (replaced by user): {foreign}"
    )


def list_status(skills: dict[str, Path], registry: dict) -> None:
    managed = set(registry["managed"])
    print(f"Repo skills source: {SKILLS_SRC}")
    print(f"Install destination: {SKILLS_DST}")
    print(f"Registry: {REGISTRY}\n")

    print(f"Skills found in repo ({len(skills)}):")
    for name, src in sorted(skills.items()):
        dst = SKILLS_DST / name
        if is_our_symlink(dst, src):
            status = "linked"
        elif dst.is_symlink():
            status = f"symlink to {dst.resolve()} (not ours)"
        elif dst.exists():
            status = "blocked (non-symlink at destination)"
        else:
            status = "not installed"
        rel = src.relative_to(REPO_ROOT)
        print(f"  {name:40}  {status:32}  ({rel})")

    orphans = sorted(managed - set(skills.keys()))
    if orphans:
        print(f"\nManaged but no longer in repo ({len(orphans)}) — `--remove` to clean up:")
        for name in orphans:
            print(f"  {name}")


def install_global_routing() -> None:
    """Inject (or update) a managed @-import of docs/skill-routing.md into ~/.claude/CLAUDE.md.

    Uses its own BEGIN/END markers — strictly additive to whatever setup-mcp.py
    has already injected. The two scripts never touch each other's blocks.
    """
    if not ROUTING_MD.exists():
        print(f"\nGlobal skill routing: {ROUTING_MD} not found — skipping.")
        return

    block = (
        f"{ROUTING_BEGIN}\n"
        f"@{ROUTING_MD}\n"
        f"{ROUTING_END}\n"
    )

    CLAUDE_MD.parent.mkdir(parents=True, exist_ok=True)
    existing = CLAUDE_MD.read_text() if CLAUDE_MD.exists() else ""

    if ROUTING_BEGIN in existing and ROUTING_END in existing:
        start = existing.index(ROUTING_BEGIN)
        end = existing.index(ROUTING_END) + len(ROUTING_END)
        if end < len(existing) and existing[end] == "\n":
            end += 1
        new_content = existing[:start] + block + existing[end:]
        action = "updated"
    else:
        sep = "" if existing == "" or existing.endswith("\n") else "\n"
        new_content = existing + sep + ("\n" if existing else "") + block
        action = "added"

    if new_content != existing:
        CLAUDE_MD.write_text(new_content)
        print(f"Global skill routing: {action} import in {CLAUDE_MD}")
    else:
        print(f"Global skill routing: already up to date in {CLAUDE_MD}")


def remove_global_routing() -> None:
    if not CLAUDE_MD.exists():
        return
    existing = CLAUDE_MD.read_text()
    if ROUTING_BEGIN not in existing or ROUTING_END not in existing:
        return
    start = existing.index(ROUTING_BEGIN)
    end = existing.index(ROUTING_END) + len(ROUTING_END)
    if end < len(existing) and existing[end] == "\n":
        end += 1
    # also strip a single leading blank line if present
    if start > 0 and existing[start - 1] == "\n" and (start < 2 or existing[start - 2] == "\n"):
        start -= 1
    new_content = existing[:start] + existing[end:]
    CLAUDE_MD.write_text(new_content)
    print(f"Global skill routing: removed import from {CLAUDE_MD}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--remove",
        action="store_true",
        help="Remove all skills previously installed by this script (uses registry).",
    )
    group.add_argument(
        "--list",
        action="store_true",
        help="Print install status of every skill found in the repo. No mutation.",
    )
    parser.add_argument(
        "--skip-routing",
        action="store_true",
        help="Don't add (or remove) the @-import of skill-routing.md to ~/.claude/CLAUDE.md.",
    )
    args = parser.parse_args()

    skills = discover_skills()
    registry = load_registry()

    if args.list:
        list_status(skills, registry)
        return

    if args.remove:
        remove(registry)
        if not args.skip_routing:
            remove_global_routing()
        return

    if not skills:
        print(f"No SKILL.md files found under {SKILLS_SRC}.")
        return

    install(skills, registry)
    if not args.skip_routing:
        install_global_routing()
    print("\nNote: this script does not touch ~/.claude.json — MCP servers untouched.")


if __name__ == "__main__":
    main()
