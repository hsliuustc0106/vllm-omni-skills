#!/usr/bin/env bash
# Benchmark a running vLLM-Omni server.
#
# Usage:
#   ./run_benchmark.sh [--url http://localhost:8091] [--num-prompts 50] [--prompt "a red circle"]
#
# Prerequisites:
#   - A running vLLM-Omni server
#   - curl and jq installed

set -euo pipefail

URL="${1:-http://localhost:8091}"
NUM_PROMPTS="${2:-10}"
PROMPT="${3:-a simple red circle on white background}"

echo "=== vLLM-Omni Benchmark ==="
echo "Server:  $URL"
echo "Prompts: $NUM_PROMPTS"
echo "Prompt:  $PROMPT"
echo ""

# Health check
if ! curl -sf "$URL/health" > /dev/null 2>&1; then
    echo "ERROR: Server at $URL is not healthy"
    exit 1
fi

echo "Server is healthy."
echo ""

# Warmup
echo "Warmup request..."
curl -sf "$URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}], \"max_tokens\": 16}" \
    > /dev/null 2>&1 || true
echo "Warmup done."
echo ""

# Benchmark
echo "Running $NUM_PROMPTS requests..."
TOTAL_TIME=0
SUCCESS=0
FAIL=0

for i in $(seq 1 "$NUM_PROMPTS"); do
    START=$(date +%s%N)
    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}], \"max_tokens\": 32}" \
        2>/dev/null || echo "000")
    END=$(date +%s%N)

    ELAPSED=$(( (END - START) / 1000000 ))
    TOTAL_TIME=$((TOTAL_TIME + ELAPSED))

    if [ "$HTTP_CODE" = "200" ]; then
        SUCCESS=$((SUCCESS + 1))
        echo "  [$i/$NUM_PROMPTS] ${ELAPSED}ms (HTTP $HTTP_CODE)"
    else
        FAIL=$((FAIL + 1))
        echo "  [$i/$NUM_PROMPTS] ${ELAPSED}ms (HTTP $HTTP_CODE) FAILED"
    fi
done

echo ""
echo "=== Results ==="
echo "Total requests: $NUM_PROMPTS"
echo "Successful:     $SUCCESS"
echo "Failed:         $FAIL"
if [ "$SUCCESS" -gt 0 ]; then
    AVG=$((TOTAL_TIME / NUM_PROMPTS))
    echo "Total time:     ${TOTAL_TIME}ms"
    echo "Avg latency:    ${AVG}ms"
fi
