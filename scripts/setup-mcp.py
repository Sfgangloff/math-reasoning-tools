#!/usr/bin/env python3
"""Discover all MCP servers in this repo and merge them into ~/.claude.json.

Scans servers/ and external/ for directories containing a pyproject.toml with
[project.scripts]. Works for any servers present at run time — including newly
added servers and submodules.

Uses the user scope (top-level mcpServers key) so servers are available
globally in all Claude Code sessions.

Also detects missing system-level dependencies (pdflatex, poppler, ripgrep,
elan) and prompts before installing them via the platform's package manager.
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_JSON = Path.home() / ".claude.json"
CLAUDE_MD = Path.home() / ".claude" / "CLAUDE.md"
ROUTING_MD = REPO_ROOT / "docs" / "tool-routing.md"
ROUTING_BEGIN = "<!-- BEGIN math-reasoning-tools (managed by setup-mcp.py) -->"
ROUTING_END = "<!-- END math-reasoning-tools -->"
SCAN_DIRS = [REPO_ROOT / "servers", REPO_ROOT / "external"]

# binary name -> human label, what needs it, install commands per package manager
SYSTEM_DEPS = [
    {
        "binary": "rg",
        "label": "ripgrep",
        "needed_by": "lean-lsp-mcp (lean_local_search)",
        "install": {
            "brew": ["brew install ripgrep"],
            "apt": ["sudo apt-get update", "sudo apt-get install -y ripgrep"],
            "dnf": ["sudo dnf install -y ripgrep"],
            "pacman": ["sudo pacman -S --noconfirm ripgrep"],
        },
    },
    {
        "binary": "pdftoppm",
        "label": "poppler",
        "needed_by": "commutative-diagrams (PDF → PNG)",
        "install": {
            "brew": ["brew install poppler"],
            "apt": ["sudo apt-get install -y poppler-utils"],
            "dnf": ["sudo dnf install -y poppler-utils"],
            "pacman": ["sudo pacman -S --noconfirm poppler"],
        },
    },
    {
        "binary": "pdflatex",
        "label": "pdflatex (LaTeX with tikz-cd)",
        "needed_by": "commutative-diagrams (render_tikzcd)",
        "install": {
            # mactex-no-gui is ~4 GB but bundles tikz-cd; one command, no
            # post-install tlmgr step.
            "brew": ["brew install --cask mactex-no-gui"],
            "apt": [
                "sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-pictures",
            ],
            "dnf": ["sudo dnf install -y texlive-scheme-medium texlive-collection-pictures"],
            "pacman": ["sudo pacman -S --noconfirm texlive-basic texlive-latexextra texlive-pictures"],
        },
    },
    {
        "binary": "elan",
        "label": "elan (Lean toolchain manager)",
        "needed_by": "lean-lsp-mcp (loogle local index)",
        "install": {
            # Same official installer for every platform — adds elan to PATH
            # via shell rc files; takes effect after shell restart.
            "brew": [
                "curl --proto '=https' --tlsv1.2 -sSf "
                "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh "
                "| sh -s -- -y --default-toolchain none",
            ],
            "apt": [
                "curl --proto '=https' --tlsv1.2 -sSf "
                "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh "
                "| sh -s -- -y --default-toolchain none",
            ],
            "dnf": [
                "curl --proto '=https' --tlsv1.2 -sSf "
                "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh "
                "| sh -s -- -y --default-toolchain none",
            ],
            "pacman": [
                "curl --proto '=https' --tlsv1.2 -sSf "
                "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh "
                "| sh -s -- -y --default-toolchain none",
            ],
        },
    },
]


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


def detect_pkg_manager() -> str | None:
    """Return one of: 'brew', 'apt', 'dnf', 'pacman', or None if unsupported."""
    system = platform.system()
    if system == "Darwin":
        return "brew" if shutil.which("brew") else None
    if system == "Linux":
        for mgr in ("apt-get", "dnf", "pacman"):
            if shutil.which(mgr):
                return "apt" if mgr == "apt-get" else mgr
    return None


def check_system_deps(*, assume_yes: bool) -> None:
    """Detect missing system deps; show install commands and prompt before running."""
    missing = [d for d in SYSTEM_DEPS if not shutil.which(d["binary"])]

    if not missing:
        print("\nSystem dependencies: all present.")
        return

    print(f"\nSystem dependencies — {len(missing)} missing:")
    for d in missing:
        print(f"  - {d['label']:32}  needed by {d['needed_by']}")

    pkg_mgr = detect_pkg_manager()
    if pkg_mgr is None:
        system = platform.system()
        if system == "Darwin":
            print("\nHomebrew not found. Install from https://brew.sh, then re-run this script.")
        elif system == "Windows":
            print("\nWindows is not auto-supported. Install the deps manually with winget/choco.")
        else:
            print(f"\nNo supported package manager detected on {system}. Install the deps manually.")
        return

    interactive = sys.stdin.isatty() and not assume_yes
    if not interactive and not assume_yes:
        print("\n(non-interactive shell — pass --yes to auto-install, or run interactively)")
        return

    print(f"\nDetected package manager: {pkg_mgr}")
    for d in missing:
        cmds = d["install"].get(pkg_mgr)
        if not cmds:
            print(f"\n  Skipping {d['label']}: no install recipe for {pkg_mgr}.")
            continue

        print(f"\nInstall {d['label']}? Will run:")
        for c in cmds:
            print(f"    $ {c}")

        if assume_yes:
            ans = "y"
        else:
            try:
                ans = input("[Y/n] ").strip().lower()
            except EOFError:
                ans = "n"
        if ans not in ("", "y", "yes"):
            print(f"  Skipped {d['label']}.")
            continue

        for c in cmds:
            print(f"  $ {c}")
            r = subprocess.run(c, shell=True)
            if r.returncode != 0:
                print(f"  Command failed (exit {r.returncode}). Stopping {d['label']}.")
                break
        else:
            if shutil.which(d["binary"]):
                print(f"  {d['label']}: installed.")
            else:
                print(f"  {d['label']}: install ran but '{d['binary']}' not on PATH yet — restart your shell.")


def install_global_routing() -> None:
    """Inject (or update) a managed @-import of docs/tool-routing.md into ~/.claude/CLAUDE.md.

    The block is delimited by BEGIN/END markers so re-running setup-mcp.py replaces
    the existing block in place (handy if the repo moves) without disturbing any
    other content the user keeps in their global CLAUDE.md.
    """
    if not ROUTING_MD.exists():
        print(f"\nGlobal routing: {ROUTING_MD} not found — skipping.")
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
        # also consume a single trailing newline if present
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
        print(f"\nGlobal routing: {action} import in {CLAUDE_MD}")
    else:
        print(f"\nGlobal routing: already up to date in {CLAUDE_MD}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-deps", action="store_true", help="don't check system dependencies")
    parser.add_argument("--skip-routing", action="store_true", help="don't update ~/.claude/CLAUDE.md routing import")
    parser.add_argument("--yes", "-y", action="store_true", help="auto-confirm dependency install prompts")
    args = parser.parse_args()

    discovered = discover_servers()
    if not discovered:
        print("No servers found.", file=sys.stderr)
        sys.exit(1)

    config = {}
    if CLAUDE_JSON.exists():
        with open(CLAUDE_JSON) as f:
            config = json.load(f)

    existing_servers: dict = config.get("mcpServers", {})
    # Servers the user disabled via scripts/toggle.py. We must not re-enable them
    # here, but we do keep their stashed config in sync so re-enabling later
    # picks up any changes to args / command from this repo.
    disabled_servers: dict = config.get("disabledMcpServers", {})

    added, updated, refreshed_disabled = [], [], []
    for key, new_cfg in discovered.items():
        if key in disabled_servers:
            merged = {**new_cfg}
            if disabled_servers[key].get("env"):
                merged["env"] = disabled_servers[key]["env"]
            if disabled_servers[key] != merged:
                disabled_servers[key] = merged
                refreshed_disabled.append(key)
            continue
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
    if disabled_servers:
        config["disabledMcpServers"] = disabled_servers
    with open(CLAUDE_JSON, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"Updated {CLAUDE_JSON}")
    for key in added:
        print(f"  + added:   {key}")
    for key in updated:
        print(f"  ~ updated: {key}")
    for key in refreshed_disabled:
        print(f"  ~ refreshed (disabled): {key}")
    if not added and not updated and not refreshed_disabled:
        print("  (no changes — all servers already present)")

    print(f"\nAll configured servers ({len(existing_servers) + len(disabled_servers)}):")
    for key in existing_servers:
        tag = "[new]" if key in added else "[updated]" if key in updated else "[existing]"
        print(f"  {tag:12} {key}")
    for key in disabled_servers:
        tag = "[disabled*]" if key in refreshed_disabled else "[disabled]"
        print(f"  {tag:12} {key}")

    if not args.skip_routing:
        install_global_routing()

    if not args.skip_deps:
        check_system_deps(assume_yes=args.yes)


if __name__ == "__main__":
    main()
