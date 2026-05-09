#!/usr/bin/env python3
"""Disable or re-enable MCP servers and skills by name.

Servers: moved between `mcpServers` and `disabledMcpServers` in ~/.claude.json
(the file `setup-mcp.py` writes to). The disabled block is restored verbatim
on re-enable, preserving any custom `env` overrides.

Skills: the symlink under ~/.claude/skills/<name>/ is unlinked on disable and
recreated on enable. The skill source is rediscovered from this repo's
skills/ tree, and the disabled set is tracked in the same registry that
setup-skills.py uses.

Usage:
    python3 scripts/toggle.py list
    python3 scripts/toggle.py disable <name> [<name> ...]
    python3 scripts/toggle.py enable  <name> [<name> ...]

Names that exist as both a server and a skill must be disambiguated with
`server:<name>` or `skill:<name>`.
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "skills"
CLAUDE_JSON = Path.home() / ".claude.json"
SKILLS_DST = Path.home() / ".claude" / "skills"
SKILLS_REGISTRY = SKILLS_DST / ".math-reasoning-tools-managed.json"

DISABLED_KEY = "disabledMcpServers"
ENABLED_KEY = "mcpServers"


# ---------- shared I/O ----------

def load_claude_json() -> dict:
    if not CLAUDE_JSON.exists():
        return {}
    with open(CLAUDE_JSON) as f:
        return json.load(f)


def save_claude_json(data: dict) -> None:
    with open(CLAUDE_JSON, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def load_skills_registry() -> dict:
    if not SKILLS_REGISTRY.exists():
        return {"managed": [], "disabled": []}
    try:
        with open(SKILLS_REGISTRY) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {"managed": [], "disabled": []}
    data.setdefault("managed", [])
    data.setdefault("disabled", [])
    return data


def save_skills_registry(data: dict) -> None:
    SKILLS_DST.mkdir(parents=True, exist_ok=True)
    with open(SKILLS_REGISTRY, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


# ---------- discovery ----------

def discover_skill_sources() -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not SKILLS_SRC.exists():
        return found
    for skill_md in SKILLS_SRC.rglob("SKILL.md"):
        found[skill_md.parent.name] = skill_md.parent
    return found


def server_state(claude: dict) -> tuple[set[str], set[str]]:
    enabled = set(claude.get(ENABLED_KEY, {}).keys())
    disabled = set(claude.get(DISABLED_KEY, {}).keys())
    return enabled, disabled


def skill_state(registry: dict, sources: dict[str, Path]) -> tuple[set[str], set[str]]:
    """Return (enabled, disabled) skill names this script knows about."""
    managed = set(registry.get("managed", []))
    disabled = set(registry.get("disabled", []))
    # Anything we've ever managed and is still in the source tree is in scope.
    in_scope = (managed | disabled) & set(sources.keys())
    return in_scope - disabled, in_scope & disabled


# ---------- name resolution ----------

def resolve(name: str, claude: dict, skill_sources: dict[str, Path]) -> tuple[str, str]:
    """Return ('server'|'skill', bare_name) or raise ValueError."""
    if name.startswith("server:"):
        return "server", name.split(":", 1)[1]
    if name.startswith("skill:"):
        return "skill", name.split(":", 1)[1]

    enabled_servers, disabled_servers = server_state(claude)
    is_server = name in enabled_servers or name in disabled_servers
    is_skill = name in skill_sources

    if is_server and is_skill:
        raise ValueError(
            f"{name!r} matches both a server and a skill — "
            f"use server:{name} or skill:{name} to disambiguate."
        )
    if is_server:
        return "server", name
    if is_skill:
        return "skill", name
    raise ValueError(f"{name!r} is not a known server or skill.")


# ---------- server toggle ----------

def disable_server(claude: dict, name: str) -> tuple[str, bool]:
    enabled = claude.setdefault(ENABLED_KEY, {})
    disabled = claude.setdefault(DISABLED_KEY, {})
    if name in disabled and name not in enabled:
        return f"server {name}: already disabled", False
    if name not in enabled:
        return f"server {name}: not present in {ENABLED_KEY}; nothing to do", False
    disabled[name] = enabled.pop(name)
    return f"server {name}: disabled", True


def enable_server(claude: dict, name: str) -> tuple[str, bool]:
    enabled = claude.setdefault(ENABLED_KEY, {})
    disabled = claude.setdefault(DISABLED_KEY, {})
    if name in enabled and name not in disabled:
        return f"server {name}: already enabled", False
    if name not in disabled:
        return f"server {name}: no entry in {DISABLED_KEY}; nothing to restore", False
    enabled[name] = disabled.pop(name)
    return f"server {name}: enabled", True


# ---------- skill toggle ----------

def disable_skill(registry: dict, sources: dict[str, Path], name: str) -> tuple[str, bool]:
    if name not in sources:
        return f"skill {name}: no source under {SKILLS_SRC} — cannot manage", False
    disabled = set(registry["disabled"])
    if name in disabled:
        return f"skill {name}: already disabled", False
    dst = SKILLS_DST / name
    if dst.is_symlink():
        dst.unlink()
    elif dst.exists():
        return f"skill {name}: {dst} is not a symlink; refusing to touch it", False
    disabled.add(name)
    registry["disabled"] = sorted(disabled)
    return f"skill {name}: disabled", True


def enable_skill(registry: dict, sources: dict[str, Path], name: str) -> tuple[str, bool]:
    if name not in sources:
        return f"skill {name}: no source under {SKILLS_SRC} — cannot restore", False
    disabled = set(registry["disabled"])
    managed = set(registry["managed"])
    dst = SKILLS_DST / name
    if dst.is_symlink() and dst.resolve() == sources[name].resolve():
        changed = name in disabled
        disabled.discard(name)
        registry["disabled"] = sorted(disabled)
        return f"skill {name}: already enabled", changed
    if dst.exists() and not dst.is_symlink():
        return f"skill {name}: {dst} is not a symlink; refusing to overwrite", False
    SKILLS_DST.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink():
        dst.unlink()
    dst.symlink_to(sources[name], target_is_directory=True)
    disabled.discard(name)
    managed.add(name)
    registry["disabled"] = sorted(disabled)
    registry["managed"] = sorted(managed)
    return f"skill {name}: enabled", True


# ---------- commands ----------

def cmd_list() -> None:
    claude = load_claude_json()
    registry = load_skills_registry()
    sources = discover_skill_sources()

    enabled_s, disabled_s = server_state(claude)
    enabled_k, disabled_k = skill_state(registry, sources)

    print("Servers (~/.claude.json):")
    for name in sorted(enabled_s):
        print(f"  [enabled]  {name}")
    for name in sorted(disabled_s):
        print(f"  [disabled] {name}")
    if not enabled_s and not disabled_s:
        print("  (none)")

    print(f"\nSkills ({SKILLS_DST}):")
    for name in sorted(enabled_k):
        print(f"  [enabled]  {name}")
    for name in sorted(disabled_k):
        print(f"  [disabled] {name}")
    untracked = sorted(set(sources.keys()) - enabled_k - disabled_k)
    if untracked:
        print("\n  Source-only (not installed by setup-skills.py):")
        for name in untracked:
            print(f"    {name}")


def cmd_toggle(action: str, names: list[str]) -> int:
    claude = load_claude_json()
    registry = load_skills_registry()
    sources = discover_skill_sources()

    claude_dirty = False
    registry_dirty = False
    rc = 0

    for raw in names:
        try:
            kind, name = resolve(raw, claude, sources)
        except ValueError as e:
            print(f"  ! {e}", file=sys.stderr)
            rc = 1
            continue

        if kind == "server":
            msg, changed = (
                disable_server(claude, name) if action == "disable" else enable_server(claude, name)
            )
            claude_dirty = claude_dirty or changed
        else:
            msg, changed = (disable_skill if action == "disable" else enable_skill)(
                registry, sources, name
            )
            registry_dirty = registry_dirty or changed
        print(f"  {msg}")

    if claude_dirty:
        save_claude_json(claude)
    if registry_dirty:
        save_skills_registry(registry)

    if claude_dirty or registry_dirty:
        print(
            "\nNote: restart Claude Code (or run scripts/reload-mcp.py for servers) "
            "for the change to take effect."
        )
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="show enabled/disabled status of all servers and skills")
    p_dis = sub.add_parser("disable", help="disable one or more servers/skills by name")
    p_dis.add_argument("names", nargs="+")
    p_en = sub.add_parser("enable", help="re-enable one or more servers/skills by name")
    p_en.add_argument("names", nargs="+")
    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list()
        return 0
    return cmd_toggle(args.cmd, args.names)


if __name__ == "__main__":
    sys.exit(main())
