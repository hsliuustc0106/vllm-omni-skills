#!/usr/bin/env bash
# run_perf_comparison.sh — Before/after benchmark comparison for PR review.
#
# Usage:
#   ./scripts/run_perf_comparison.sh --base <ref> --head <ref> --model <model> --benchmark <type>
#
# Benchmark types: omni_offline, omni_online, diffusion, accuracy
#
# Requirements:
#   - Local clone of vllm-project/vllm-omni
#   - Python environment with vllm-omni installed
#   - Git worktree support

set -euo pipefail

TIMEOUT_SECONDS=1200  # 20 minutes hard limit per run
WORKTREE_BASE=".claude/perf-worktrees/base"
WORKTREE_PR=".claude/perf-worktrees/pr"
REPORT_FILE=""

cleanup() {
    echo "--- Cleaning up worktrees ---"
    git worktree remove "$WORKTREE_BASE" --force 2>/dev/null || true
    git worktree remove "$WORKTREE_PR" --force 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# --- Argument parsing ---
BASE_REF=""
HEAD_REF=""
MODEL=""
BENCHMARK_TYPE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --base) BASE_REF="$2"; shift 2 ;;
        --head) HEAD_REF="$2"; shift 2 ;;
        --model) MODEL="$2"; shift 2 ;;
        --benchmark) BENCHMARK_TYPE="$2"; shift 2 ;;
        --report) REPORT_FILE="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -z "$BASE_REF" || -z "$HEAD_REF" || -z "$MODEL" || -z "$BENCHMARK_TYPE" ]]; then
    echo "Usage: $0 --base <ref> --head <ref> --model <model> --benchmark <type>"
    exit 1
fi

# --- Hardware detection ---
detect_hardware() {
    PLATFORM="CPU"
    GPU_COUNT=0
    GPU_MODEL="N/A"
    VRAM_PER_GPU_GB=0

    if command -v nvidia-smi &>/dev/null; then
        local gpu_info
        gpu_info=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true)
        if [[ -n "$gpu_info" ]]; then
            GPU_COUNT=$(echo "$gpu_info" | wc -l | tr -d ' ')
            GPU_MODEL=$(echo "$gpu_info" | head -1 | cut -d',' -f1 | xargs)
            VRAM_MB=$(echo "$gpu_info" | head -1 | cut -d',' -f2 | tr -d ' MiB' | xargs)
            VRAM_PER_GPU_GB=$(python3 -c "print(f'{$VRAM_MB/1024:.1f}')")
            PLATFORM="CUDA"
            return
        fi
    fi

    if [[ "$PLATFORM" == "CPU" ]] && command -v rocm-smi &>/dev/null; then
        PLATFORM="ROCm"
        GPU_MODEL="ROCm GPU"
        VRAM_PER_GPU_GB="unknown"
        GPU_COUNT=1
    fi

    if [[ "$PLATFORM" == "CPU" ]]; then
        python3 -c "import torch_npu" 2>/dev/null && PLATFORM="NPU" || true
    fi
    if [[ "$PLATFORM" == "CPU" ]]; then
        python3 -c "import torch; torch.xpu.device_count()" 2>/dev/null && PLATFORM="XPU" || true
    fi
}

# --- Feasibility check ---
estimate_model_size_gb() {
    # Rough estimate: assume BF16 (2 bytes/param), add 50% overhead for KV cache + activations
    # Caller can override with more specific estimates
    local param_count="${1:-7000000000}"  # default 7B
    python3 -c "print(f'{$param_count * 2 / 1e9 * 1.5:.1f}')"
}

check_feasibility() {
    local estimated_gb="$1"

    if [[ "$PLATFORM" == "CPU" ]]; then
        # CPU-only: can only verify very small models
        local sys_ram_gb
        sys_ram_gb=$(python3 -c "
import os
with open('/proc/meminfo' if os.path.exists('/proc/meminfo') else '/dev/null') as f:
    for line in f:
        if 'MemAvailable' in line:
            print(int(line.split()[1]) / 1048576)
            break
" 2>/dev/null || echo "16")
        if (( $(echo "$estimated_gb < $sys_ram_gb * 0.5" | bc -l 2>/dev/null || echo 0) )); then
            echo "VERIFIABLE (CPU-only, small model)"
            return 0
        else
            echo "CANNOT_VERIFY (CPU-only, model too large for RAM)"
            return 1
        fi
    fi

    local total_vram_gb
    total_vram_gb=$(python3 -c "print(f'{$VRAM_PER_GPU_GB * $GPU_COUNT:.1f}')")

    if (( $(echo "$estimated_gb <= $total_vram_gb" | bc -l 2>/dev/null || echo 0) )); then
        echo "VERIFIABLE"
        return 0
    elif (( $(echo "$estimated_gb <= $total_vram_gb * 1.5" | bc -l 2>/dev/null || echo 0) )); then
        echo "NEEDS_OFFLOAD"
        return 0
    else
        echo "CANNOT_VERIFY (model requires ~${estimated_gb}GB, available ${total_vram_gb}GB)"
        return 1
    fi
}

# --- Run benchmark with timeout ---
run_with_timeout() {
    local label="$1"
    shift
    local start end duration

    echo "--- Running benchmark: $label ---"
    start=$(date +%s)

    timeout "$TIMEOUT_SECONDS" "$@" 2>&1 | tee "${label}.benchmark.log" &
    local pid=$!
    wait "$pid" || local exit_code=$?

    end=$(date +%s)
    duration=$((end - start))

    if [[ ${exit_code:-0} -eq 124 ]]; then
        echo "TIMEOUT: $label exceeded ${TIMEOUT_SECONDS}s limit (ran ${duration}s)"
        echo '{"status": "TIMEOUT", "duration_s": '$duration'}' > "${label}.result.json"
        return 1
    fi

    echo "--- Completed $label in ${duration}s ---"
    echo "{\"status\": \"done\", \"duration_s\": $duration}" > "${label}.timing.json"
    return ${exit_code:-0}
}

# --- Setup worktrees ---
setup_worktrees() {
    echo "--- Setting up worktrees ---"
    mkdir -p .claude/perf-worktrees
    git worktree add "$WORKTREE_BASE" "$BASE_REF" 2>/dev/null || git worktree add "$WORKTREE_BASE" "origin/$BASE_REF"
    git worktree add "$WORKTREE_PR" "$HEAD_REF" 2>/dev/null || git worktree add "$WORKTREE_PR" "origin/$HEAD_REF"
}

# --- Compare results ---
compare_results() {
    local base_result="$1"
    local pr_result="$2"

    echo ""
    echo "========================================"
    echo "  PERF COMPARISON REPORT"
    echo "========================================"
    echo "Hardware: $GPU_MODEL x$GPU_COUNT ($VRAM_PER_GPU_GB GB each), $PLATFORM"
    echo "Model: $MODEL"
    echo "Base: $BASE_REF | Head: $HEAD_REF"
    echo "----------------------------------------"

    if [[ ! -f "$base_result" || ! -f "$pr_result" ]]; then
        echo "ERROR: Missing result files"
        echo "  Base result: $base_result ($( [[ -f "$base_result" ]] && echo EXISTS || echo MISSING ))"
        echo "  PR result: $pr_result ($( [[ -f "$pr_result" ]] && echo EXISTS || echo MISSING ))"
        return 1
    fi

    # Tolerance defaults
    LATENCY_TOL="${LATENCY_TOLERANCE:-10}"
    THROUGHPUT_TOL="${THROUGHPUT_TOLERANCE:-10}"
    VRAM_TOL="${VRAM_TOLERANCE:-5}"

    python3 - <<PYEOF
import json, sys

with open("$base_result") as f:
    base = json.load(f)
with open("$pr_result") as f:
    pr = json.load(f)

tolerances = {"latency": $LATENCY_TOL, "throughput": $THROUGHPUT_TOL, "vram": $VRAM_TOL}

def check_verdict(metric, base_val, pr_val):
    if base_val == 0:
        return "N/A"
    delta_pct = abs(pr_val - base_val) / base_val * 100
    tol = tolerances.get(metric, 10)
    return "CONFIRMED" if delta_pct <= tol else "NOT_CONFIRMED"

metrics_to_check = []
for key in base:
    if key in pr and isinstance(base[key], (int, float)) and isinstance(pr[key], (int, float)):
        metrics_to_check.append(key)

if not metrics_to_check:
    print("No comparable numeric metrics found in result files.")
    sys.exit(1)

print(f"| Metric         | Base       | PR         | Delta      | Verdict      |")
print(f"|----------------|------------|------------|------------|--------------|")
for m in metrics_to_check:
    bv, pv = base[m], pr[m]
    delta = pv - bv
    delta_pct = (delta / bv * 100) if bv != 0 else 0
    verdict = check_verdict(m, bv, pv)
    print(f"| {m:<14} | {bv:<10.2f} | {pv:<10.2f} | {delta_pct:>+9.1f}%  | {verdict:<12} |")

print(f"\nTolerances: latency ±{tolerances['latency']}%, throughput ±{tolerances['throughput']}%, VRAM ±{tolerances['vram']}%")
PYEOF
}

# --- Main ---
main() {
    detect_hardware
    echo "Detected: $PLATFORM | $GPU_MODEL x$GPU_COUNT | ${VRAM_PER_GPU_GB}GB VRAM/GPU"

    # Estimate model size (rough: use model name heuristics or default 7B)
    local estimated_gb
    estimated_gb=$(estimate_model_size_gb)
    echo "Estimated model VRAM: ~${estimated_gb}GB"

    local feasibility
    feasibility=$(check_feasibility "$estimated_gb")
    echo "Feasibility: $feasibility"

    if [[ "$feasibility" == CANNOT_VERIFY* ]]; then
        echo ""
        echo "Cannot execute benchmarks. Falling back to static-only analysis."
        echo "See references/perf-verification.md Section 8 for static analysis checklist."
        exit 0
    fi

    setup_worktrees

    local extra_args=()
    if [[ "$feasibility" == NEEDS_OFFLOAD* ]]; then
        extra_args+=(--cpu-offload-gb 10)
        echo "Running with CPU offload (feasibility: $feasibility)"
    fi

    # Run benchmarks (caller should replace these with actual benchmark commands)
    echo ""
    echo "NOTE: Edit this script or set BENCH_CMD to the actual benchmark command."
    echo "Example: BENCH_CMD='python3 -m vllm.entrypoints.openai.api_server' $0 ..."
    echo ""
    echo "Placeholder: running a basic timing check."

    # Placeholder — in practice, run the actual benchmark in each worktree
    # run_with_timeout "base" bash -c "cd $WORKTREE_BASE && python3 -c 'import time; print(json.dumps({\"latency_ms\": 100.0, \"throughput_tps\": 50.0, \"vram_gb\": 8.0}))'"
    # run_with_timeout "pr"   bash -c "cd $WORKTREE_PR   && python3 -c 'import time; print(json.dumps({\"latency_ms\": 95.0, \"throughput_tps\": 52.0, \"vram_gb\": 7.8}))'"

    echo "Worktrees ready at $WORKTREE_BASE and $WORKTREE_PR"
    echo "Run your benchmark commands manually, or set BENCH_CMD env var."
}

main "$@"
