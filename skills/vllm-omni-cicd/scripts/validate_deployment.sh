#!/usr/bin/env bash
# Validate a vLLM-Omni deployment.
#
# Usage:
#   ./validate_deployment.sh [base_url]
#
# Checks:
#   1. Health endpoint returns 200
#   2. Model list is non-empty
#   3. Basic inference request succeeds
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed

set -euo pipefail

BASE_URL="${1:-http://localhost:8091}"
TIMEOUT=10
PASS=0
FAIL=0

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "PASS" ]; then
        PASS=$((PASS + 1))
        echo "  PASS  $name"
    else
        FAIL=$((FAIL + 1))
        echo "  FAIL  $name ($result)"
    fi
}

echo "=== Deployment Validation ==="
echo "Target: $BASE_URL"
echo ""

# Check 1: Health
HEALTH=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/health" --max-time $TIMEOUT 2>/dev/null || echo "000")
if [ "$HEALTH" = "200" ]; then
    check "Health check" "PASS"
else
    check "Health check" "HTTP $HEALTH"
fi

# Check 2: Models
MODELS=$(curl -sf "$BASE_URL/v1/models" --max-time $TIMEOUT 2>/dev/null || echo "{}")
MODEL_COUNT=$(echo "$MODELS" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null || echo "0")
if [ "$MODEL_COUNT" -gt 0 ]; then
    check "Model list ($MODEL_COUNT model(s))" "PASS"
else
    check "Model list" "No models loaded"
fi

# Check 3: Inference
INFER_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/v1/chat/completions" \
    --max-time 120 \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"test"}],"max_tokens":8}' \
    2>/dev/null || echo "000")
if [ "$INFER_CODE" = "200" ]; then
    check "Inference request" "PASS"
else
    check "Inference request" "HTTP $INFER_CODE"
fi

echo ""
echo "=== Summary ==="
echo "Passed: $PASS"
echo "Failed: $FAIL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "Deployment validated successfully."
