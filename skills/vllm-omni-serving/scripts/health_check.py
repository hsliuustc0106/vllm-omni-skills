#!/usr/bin/env python3
"""Health check script for vLLM-Omni server instances.

Usage:
    python health_check.py [--url http://localhost:8091] [--timeout 5]
"""

import argparse
import json
import sys
import urllib.request
import urllib.error


def check(url: str, timeout: int) -> dict:
    result = {"url": url, "healthy": False, "models": [], "error": None}

    try:
        req = urllib.request.Request(f"{url}/health")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["healthy"] = resp.status == 200
    except (urllib.error.URLError, OSError) as e:
        result["error"] = str(e)
        return result

    try:
        req = urllib.request.Request(f"{url}/v1/models")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            result["models"] = [m["id"] for m in data.get("data", [])]
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        pass

    return result


def main():
    parser = argparse.ArgumentParser(description="vLLM-Omni health check")
    parser.add_argument("--url", default="http://localhost:8091")
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = check(args.url, args.timeout)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "HEALTHY" if result["healthy"] else "UNHEALTHY"
        print(f"{args.url}: {status}")
        if result["models"]:
            print(f"  Models: {', '.join(result['models'])}")
        if result["error"]:
            print(f"  Error: {result['error']}")

    sys.exit(0 if result["healthy"] else 1)


if __name__ == "__main__":
    main()
