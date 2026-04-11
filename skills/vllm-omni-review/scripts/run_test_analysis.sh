#!/usr/bin/env bash
# run_test_analysis.sh — Run affected tests with hardware-aware filtering.
#
# Usage:
#   ./scripts/run_test_analysis.sh --base <ref> --head <ref> [--run-level core_model]
#
# Requirements:
#   - Local clone of vllm-project/vllm-omni
#   - pytest installed
#   - Git worktree support

set -euo pipefail

BASE_REF=""
HEAD_REF=""
RUN_LEVEL="core_model"
TEST_TIMEOUT=60

while [[ $# -gt 0 ]]; do
    case "$1" in
        --base) BASE_REF="$2"; shift 2 ;;
        --head) HEAD_REF="$2"; shift 2 ;;
        --run-level) RUN_LEVEL="$2"; shift 2 ;;
        --timeout) TEST_TIMEOUT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -z "$BASE_REF" || -z "$HEAD_REF" ]]; then
    echo "Usage: $0 --base <ref> --head <ref> [--run-level core_model]"
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
            VRAM_PER_GPU_GB=$(python3 -c "print(f'{$VRAM_MB/1024:.1f}')" 2>/dev/null || echo "unknown")
            PLATFORM="CUDA"
            return
        fi
    fi

    if [[ "$PLATFORM" == "CPU" ]] && command -v rocm-smi &>/dev/null; then
        PLATFORM="ROCm"; GPU_COUNT=1; GPU_MODEL="ROCm GPU"
    fi
    if [[ "$PLATFORM" == "CPU" ]]; then
        python3 -c "import torch_npu" 2>/dev/null && PLATFORM="NPU" || true
    fi
    if [[ "$PLATFORM" == "CPU" ]]; then
        python3 -c "import torch; torch.xpu.device_count()" 2>/dev/null && PLATFORM="XPU" || true
    fi
}

# --- Find affected test files ---
find_affected_tests() {
    local base="$1" head="$2"
    local changed_tests changed_src

    # Directly changed test files
    changed_tests=$(git diff --name-only "$base...$head" -- 'tests/' 2>/dev/null | grep '\.py$' || true)

    # Source files that changed — map to tests via grep
    changed_src=$(git diff --name-only "$base...$head" -- 'vllm_omni/' 2>/dev/null | grep '\.py$' | grep -v __pycache__ || true)

    local grep_tests=""
    if [[ -n "$changed_src" ]]; then
        while IFS= read -r src_file; do
            # Convert file path to module: vllm_omni/engine/scheduler.py → engine.scheduler
            local module
            module=$(echo "$src_file" | sed 's|^vllm_omni/||; s|\.py$||; s|/|.|g')
            # Find test files that import this module
            local matches
            matches=$(grep -rl "from vllm_omni\.\{0,1\}${module}\|import vllm_omni\.\{0,1\}${module}" tests/ 2>/dev/null || true)
            grep_tests+="$matches"$'\n'
        done <<< "$changed_src"
    fi

    # Deduplicate and combine
    {
        echo "$changed_tests"
        echo "$grep_tests"
    } | grep '\.py$' | sort -u
}

# --- Filter tests by hardware compatibility ---
filter_by_hardware() {
    local test_files="$1"
    local skipped_reasons=()

    echo "$test_files" | while IFS= read -r test_file; do
        [[ -z "$test_file" ]] && continue

        # Check for multi-GPU requirements
        if grep -q 'num_cards=[4-9]\|tensor_parallel_size=[4-9]\|world_size=[4-9]' "$test_file" 2>/dev/null; then
            if [[ "$GPU_COUNT" -lt 4 ]]; then
                echo "SKIP: $test_file (requires 4+ GPUs, have $GPU_COUNT)"
                continue
            fi
        fi
        if grep -q 'num_cards=2\|tensor_parallel_size=2\|world_size=2' "$test_file" 2>/dev/null; then
            if [[ "$GPU_COUNT" -lt 2 ]]; then
                echo "SKIP: $test_file (requires 2+ GPUs, have $GPU_COUNT)"
                continue
            fi
        fi

        # Check for huge model markers
        if grep -q 'huge_model\|HUGE_MODEL' "$test_file" 2>/dev/null; then
            local vram_num
            vram_num=$(echo "$VRAM_PER_GPU_GB" | grep -oE '[0-9.]+' | head -1 || echo "0")
            if (( $(echo "$vram_num < 80" | bc -l 2>/dev/null || echo 0) )); then
                echo "SKIP: $test_file (huge_model, need 80GB+ GPU, have ${VRAM_PER_GPU_GB}GB)"
                continue
            fi
        fi

        # Check for platform-specific markers
        if grep -q 'skipif.*npu\|mark.npu' "$test_file" 2>/dev/null && [[ "$PLATFORM" != "NPU" ]]; then
            echo "SKIP: $test_file (NPU-only test, platform is $PLATFORM)"
            continue
        fi

        echo "RUN: $test_file"
    done
}

# --- Run tests ---
run_tests() {
    local test_list="$1"
    local runnable_tests
    runnable_tests=$(echo "$test_list" | grep "^RUN:" | cut -d: -f2- | tr '\n' ' ' || true)
    local skipped_tests
    skipped_tests=$(echo "$test_list" | grep "^SKIP:" || true)

    echo ""
    echo "========================================"
    echo "  TEST ANALYSIS REPORT"
    echo "========================================"
    echo "Hardware: $GPU_MODEL x$GPU_COUNT ($VRAM_PER_GPU_GB GB), $PLATFORM"
    echo "Run level: $RUN_LEVEL"
    echo "Base: $BASE_REF | Head: $HEAD_REF"
    echo "----------------------------------------"

    if [[ -n "$skipped_tests" ]]; then
        echo ""
        echo "Skipped tests (hardware constraints):"
        echo "$skipped_tests"
    fi

    if [[ -z "$runnable_tests" ]]; then
        echo ""
        echo "No runnable tests (all skipped due to hardware constraints)."
        echo "Proceed with static-only analysis."
        echo "See references/test-quality-evaluation.md Section 2."
        return 0
    fi

    echo ""
    echo "Running tests:"
    echo "$runnable_tests"
    echo ""

    # Run pytest with timeout per test
    pytest $runnable_tests \
        --run-level "$RUN_LEVEL" \
        -v \
        --tb=short \
        --timeout="$TEST_TIMEOUT" \
        2>&1 | tee test_analysis_output.log

    local exit_code=${PIPESTATUS[0]}

    echo ""
    echo "----------------------------------------"
    echo "Results summary:"
    # Parse pytest output
    local passed failed skipped errors warnings
    passed=$(grep -c ' PASSED ' test_analysis_output.log 2>/dev/null || echo "0")
    failed=$(grep -c ' FAILED ' test_analysis_output.log 2>/dev/null || echo "0")
    skipped=$(grep -c ' SKIPPED ' test_analysis_output.log 2>/dev/null || echo "0")
    errors=$(grep -c ' ERROR ' test_analysis_output.log 2>/dev/null || echo "0")

    echo "  Passed:  $passed"
    echo "  Failed:  $failed"
    echo "  Skipped: $skipped"
    echo "  Errors:  $errors"
    echo "  Exit code: $exit_code"

    if [[ "$failed" -gt 0 ]]; then
        echo ""
        echo "Failed tests:"
        grep ' FAILED ' test_analysis_output.log
    fi

    return $exit_code
}

# --- Main ---
main() {
    detect_hardware
    echo "Detected: $PLATFORM | $GPU_MODEL x$GPU_COUNT | ${VRAM_PER_GPU_GB}GB VRAM/GPU"

    local affected_tests
    affected_tests=$(find_affected_tests "$BASE_REF" "$HEAD_REF")

    if [[ -z "$affected_tests" ]]; then
        echo "No affected test files found in diff."
        exit 0
    fi

    echo ""
    echo "Affected test files:"
    echo "$affected_tests"

    local filtered
    filtered=$(filter_by_hardware "$affected_tests")

    run_tests "$filtered"
}

main "$@"
