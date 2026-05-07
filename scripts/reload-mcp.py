#!/usr/bin/env python3
"""Reload running MCP server processes for this repo's servers/.

After editing a server's source, the running process still holds the old code.
This script terminates the running stdio process(es) for each server under
``servers/`` so Claude Code respawns them on the next tool call (or after
``/mcp`` reconnect) — picking up the edited source.

Servers under ``external/`` (e.g. lean-lsp-mcp) are intentionally left alone:
they rarely change here and reloading them costs LSP startup time. To restart
those too, run ``/mcp`` from inside Claude Code instead.

By default also runs a smoke test on each reloaded server (initialize + tools/list)
to confirm the new code boots cleanly. Pass ``--no-check`` to skip.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVERS_DIR = REPO_ROOT / "servers"
SMOKE_TIMEOUT = 15  # seconds per server for the boot check
TERM_GRACE = 1.5  # seconds between SIGTERM and SIGKILL


def discover_servers() -> dict[str, dict]:
    """Same pattern as setup-mcp.py, but scoped to servers/ only."""
    servers: dict[str, dict] = {}
    if not SERVERS_DIR.exists():
        return servers
    for child in sorted(SERVERS_DIR.iterdir()):
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
            "directory": str(child.resolve()),
            "script": script_name,
            "command": ["uv", "run", "--directory", str(child.resolve()), script_name],
        }
    return servers


def list_processes() -> list[tuple[int, str]]:
    """Return [(pid, command_line)] for all processes visible to this user.

    Uses POSIX ``ps`` — works on macOS and Linux. Skips this script's own pid.
    """
    out = subprocess.run(
        ["ps", "-eo", "pid=,command="],
        capture_output=True, text=True, check=True,
    ).stdout
    own_pid = os.getpid()
    procs: list[tuple[int, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        pid_str, _, cmd = line.partition(" ")
        try:
            pid = int(pid_str)
        except ValueError:
            continue
        if pid == own_pid:
            continue
        procs.append((pid, cmd.strip()))
    return procs


def find_matching_pids(server_dir: str, script_name: str, procs: list[tuple[int, str]]) -> list[int]:
    """Match by absolute server dir (the --directory arg of `uv run`).

    The script_name is also a strong signal but `uv run --directory <dir> <name>`
    always carries the dir, and matching on the directory alone is precise enough
    that we avoid false positives from grep-style name collisions.
    """
    return [pid for pid, cmd in procs if server_dir in cmd]


def terminate_pids(pids: list[int]) -> tuple[list[int], list[int]]:
    """SIGTERM each pid; after a grace period, SIGKILL any survivors.

    Returns (terminated_cleanly, force_killed).
    """
    if not pids:
        return [], []

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    time.sleep(TERM_GRACE)

    survivors = []
    for pid in pids:
        try:
            os.kill(pid, 0)  # signal 0 = existence check
            survivors.append(pid)
        except ProcessLookupError:
            pass

    for pid in survivors:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    cleanly = [p for p in pids if p not in survivors]
    return cleanly, survivors


# ─── smoke test (mirrors check-mcp.py, scoped to one server) ──────────────────

def _send(proc, msg: dict) -> None:
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()


def _recv(proc) -> dict:
    return json.loads(proc.stdout.readline())


def smoke_test(name: str, command: list[str]) -> tuple[bool, str, list[str]]:
    """Boot the server, run initialize + tools/list, then kill it."""
    result = {"ok": False, "info": "no response", "tools": []}

    def run():
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=os.environ.copy(),
        )
        try:
            _send(proc, {
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "reload-mcp", "version": "1.0"},
                },
            })
            resp = _recv(proc)
            if "error" in resp:
                result["info"] = str(resp["error"])
                return
            _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            tools_resp = _recv(proc)
            result["ok"] = True
            result["info"] = "ok"
            result["tools"] = [t["name"] for t in tools_resp.get("result", {}).get("tools", [])]
        except Exception as e:
            result["info"] = f"{type(e).__name__}: {e}"
        finally:
            proc.kill()
            proc.wait()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(SMOKE_TIMEOUT)

    if t.is_alive():
        return False, "timeout", []
    return result["ok"], result["info"], result["tools"]


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-check", action="store_true",
        help="skip the post-reload boot/tools-list smoke test",
    )
    args = parser.parse_args()

    servers = discover_servers()
    if not servers:
        print(f"No servers found under {SERVERS_DIR}.", file=sys.stderr)
        return 1

    procs = list_processes()

    print(f"Reloading {len(servers)} server(s) under {SERVERS_DIR.relative_to(REPO_ROOT)}/:\n")

    reloaded: list[str] = []
    skipped: list[str] = []
    for name, info in servers.items():
        pids = find_matching_pids(info["directory"], info["script"], procs)
        if not pids:
            print(f"  {name:<32}  not running — skipped")
            skipped.append(name)
            continue

        cleanly, killed = terminate_pids(pids)
        parts = []
        if cleanly:
            parts.append(f"{len(cleanly)} terminated")
        if killed:
            parts.append(f"{len(killed)} force-killed")
        print(f"  {name:<32}  {', '.join(parts)} (pids: {pids})")
        reloaded.append(name)

    if args.no_check or not reloaded:
        print()
        if reloaded:
            print(f"Reloaded {len(reloaded)} server(s). Skipped boot check.")
        else:
            print("Nothing to reload.")
        _print_followup(reloaded)
        return 0

    print(f"\nBoot check ({len(reloaded)} server{'s' if len(reloaded) != 1 else ''}):\n")
    all_ok = True
    for name in reloaded:
        info = servers[name]
        sys.stdout.write(f"  {name:<32}  ")
        sys.stdout.flush()
        ok, msg, tools = smoke_test(name, info["command"])
        if ok:
            print(f"OK   ({len(tools)} tools)")
        else:
            print(f"FAIL  {msg}")
            all_ok = False

    _print_followup(reloaded)
    return 0 if all_ok else 1


def _print_followup(reloaded: list[str]) -> None:
    if not reloaded:
        return
    print()
    print("Next: run `/mcp` in Claude Code and reconnect the affected server(s),")
    print("or just trigger a tool call — the client will respawn them on demand.")


if __name__ == "__main__":
    sys.exit(main())
