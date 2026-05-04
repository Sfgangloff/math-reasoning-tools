#!/usr/bin/env python3
"""Discover all MCP servers in this repo and merge them into ~/.claude.json.

Scans servers/ and external/ for directories containing a pyproject.toml with
[project.scripts]. Works for any servers present at run time — including newly
added servers and submodules.

Uses the user scope (top-level mcpServers key) so servers are available
globally in all Claude Code sessions.
"""

import json
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_JSON = Path.home() / ".claude.json"
SCAN_DIRS = [REPO_ROOT / "servers", REPO_ROOT / "external"]


def discover_servers() -> dict:
    servers = {}
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            continue
        for child in sorted(scan_dir.iterdir()):
            pyproject = child / "pyproject.toml"
            if not pyproject.exists():
                continue
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            scripts = data.get("project", {}).get("scripts", {})
            if not scripts:
                continue
            script_name = next(iter(scripts))
            servers[child.name] = {
                "type": "stdio",
                "command": "uv",
                "args": ["run", "--directory", str(child), script_name],
                "env": {},
            }
    return servers


def main():
    discovered = discover_servers()
    if not discovered:
        print("No servers found.", file=sys.stderr)
        sys.exit(1)

    config = {}
    if CLAUDE_JSON.exists():
        with open(CLAUDE_JSON) as f:
            config = json.load(f)

    existing_servers: dict = config.get("mcpServers", {})

    added, updated = [], []
    for key, new_cfg in discovered.items():
        if key not in existing_servers:
            existing_servers[key] = new_cfg
            added.append(key)
        else:
            merged = {**new_cfg}
            # Preserve env vars set by the user (e.g. MATH_TOOLS_IMAGE_DIR)
            if existing_servers[key].get("env"):
                merged["env"] = existing_servers[key]["env"]
            if existing_servers[key] != merged:
                existing_servers[key] = merged
                updated.append(key)

    config["mcpServers"] = existing_servers
    with open(CLAUDE_JSON, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"Updated {CLAUDE_JSON}")
    for key in added:
        print(f"  + added:   {key}")
    for key in updated:
        print(f"  ~ updated: {key}")
    if not added and not updated:
        print("  (no changes — all servers already present)")

    print(f"\nAll configured servers ({len(existing_servers)}):")
    for key in existing_servers:
        tag = "[new]" if key in added else "[updated]" if key in updated else "[existing]"
        print(f"  {tag:12} {key}")


if __name__ == "__main__":
    main()
