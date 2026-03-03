#!/usr/bin/env python3
"""Smoke test for a running vLLM-Omni API server.

Usage:
    python test_api.py [--base-url http://localhost:8091]
"""

import argparse
import json
import sys
import urllib.request
import urllib.error


def check_health(base_url: str) -> bool:
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def list_models(base_url: str) -> list:
    try:
        req = urllib.request.Request(f"{base_url}/v1/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [m["id"] for m in data.get("data", [])]
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return []


def test_chat_completion(base_url: str, prompt: str = "hello") -> dict:
    payload = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 32,
    }).encode()
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Test vLLM-Omni API server")
    parser.add_argument("--base-url", default="http://localhost:8091")
    args = parser.parse_args()

    results = {}

    print(f"Testing server at {args.base_url}")
    print()

    healthy = check_health(args.base_url)
    results["health"] = "PASS" if healthy else "FAIL"
    print(f"  Health check: {results['health']}")

    if not healthy:
        print("\nServer is not healthy. Aborting.")
        sys.exit(1)

    models = list_models(args.base_url)
    results["models"] = "PASS" if models else "FAIL"
    print(f"  List models:  {results['models']} ({len(models)} model(s))")
    for m in models:
        print(f"    - {m}")

    try:
        resp = test_chat_completion(args.base_url)
        has_choices = len(resp.get("choices", [])) > 0
        results["chat"] = "PASS" if has_choices else "FAIL"
    except Exception as e:
        results["chat"] = f"FAIL ({e})"
    print(f"  Chat request: {results['chat']}")

    print()
    all_pass = all(v == "PASS" for v in results.values())
    if all_pass:
        print("All tests passed.")
    else:
        print("Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
