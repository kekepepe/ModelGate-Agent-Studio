#!/usr/bin/env python3
"""MCP stdio server that accepts initialize but never answers tools/list.

Used to pin the client's timeout contract: a hung server must surface as
a client timeout, never an infinite block.
"""
import json
import sys
import time


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if request.get("method") == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "silent", "version": "1.0"}},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        # tools/list: intentionally never answered
    time.sleep(5)


if __name__ == "__main__":
    main()
