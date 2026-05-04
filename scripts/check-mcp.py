#!/usr/bin/env python3
"""Health-check all MCP servers in ~/.claude/mcp.json.

Starts each server, performs the MCP initialize handshake, then calls
tools/list to confirm it's fully operational. Reports pass/fail and the
list of exposed tools.
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

MCP_CONFIG = Path.home() / ".claude" / "mcp.json"
TIMEOUT = 15  # seconds per server


def send(proc, msg: dict):
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()


def recv(proc) -> dict:
    return json.loads(proc.stdout.readline())


def check_server(name: str, config: dict) -> tuple[bool, object, list[str]]:
    cmd = [config["command"]] + config.get("args", [])
    env = {**os.environ, **config.get("env", {})}
    result: dict = {"ok": False, "info": "no response", "tools": []}

    def run():
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env,
        )
        try:
            send(proc, {
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "health-check", "version": "1.0"},
                },
            })
            resp = recv(proc)
            if "error" in resp:
                result["info"] = resp["error"]
                return
            send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            tools_resp = recv(proc)
            result["ok"] = True
            result["info"] = resp.get("result", {}).get("serverInfo", {})
            result["tools"] = [t["name"] for t in tools_resp.get("result", {}).get("tools", [])]
        finally:
            proc.kill()
            proc.wait()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(TIMEOUT)

    if t.is_alive():
        return False, "timeout", []
    return result["ok"], result["info"], result["tools"]


def main():
    if not MCP_CONFIG.exists():
        print(f"No config at {MCP_CONFIG}. Run scripts/setup-mcp.py first.")
        sys.exit(1)

    with open(MCP_CONFIG) as f:
        config = json.load(f)

    servers = config.get("mcpServers", {})
    if not servers:
        print("No servers configured.")
        sys.exit(1)

    print(f"Checking {len(servers)} MCP servers...\n")
    all_ok = True

    for name, server_config in servers.items():
        sys.stdout.write(f"  {name:<32}")
        sys.stdout.flush()
        ok, info, tools = check_server(name, server_config)
        if ok:
            tool_list = ", ".join(tools) if tools else "(none)"
            print(f"OK   {len(tools)} tools: {tool_list}")
        else:
            print(f"FAIL  {info}")
            all_ok = False

    print()
    if all_ok:
        print("All servers OK.")
    else:
        print("Some servers failed — check the entries above.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
