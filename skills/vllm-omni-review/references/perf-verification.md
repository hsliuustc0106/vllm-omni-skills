# Performance & Accuracy Claim Verification

Reviewer-side verification of contributor perf/accuracy claims. This is **blocking**: must complete before issuing a verdict.

**Key distinction:** `tests-docs-checklist.md` Section 5 defines what the *contributor* must provide. This file defines how the *reviewer* can independently verify those claims.

**Requires a local clone** of `vllm-project/vllm-omni`. If no clone exists, skip to static-only analysis.

---

## 1. Claim Detection

Extract quantitative claims from PR body and comments.

### Regex patterns

| Claim type | Pattern | Captures |
|-----------|---------|----------|
| Latency | `(\d+(?:\.\d+)?)\s*(ms|s|sec)` | value, unit |
| Throughput | `(\d+(?:\.\d+)?)\s*(tok/s|tokens/s|req/s|iters/s|qps)` | value, unit |
| VRAM | `(\d+(?:\.\d+)?)\s*(GB|MB)\s*(?:VRAM|memory|GPU)` | value, unit |
| Speedup | `(\d+(?:\.\d+)?)\s*%?\s*(?:faster|slower|speedup|reduction|improvement)` | value, direction |
| Accuracy | `(?:FID|F1|BLEU|WER|CER|psnr|ssim|accuracy|pass@k)\s*[:=]?\s*([\d.]+)` | metric, value |

**When to activate:** PR has `[Performance]` prefix, or PR body contains 2+ matches from the patterns above, or Step 5 (Evidence) flagged missing benchmarks.

---

## 2. Hardware Detection (single source of truth)

This section is the canonical hardware detection logic. Cross-referenced by `test-quality-evaluation.md`.

### Detection sequence

```bash
# CUDA
if command -v nvidia-smi &>/dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null)
    if [ -n "$GPU_INFO" ]; then
        GPU_COUNT=$(echo "$GPU_INFO" | wc -l | tr -d ' ')
        GPU_MODEL=$(echo "$GPU_INFO" | head -1 | cut -d',' -f1 | xargs)
        VRAM_PER_GPU_GB=$(echo "$GPU_INFO" | head -1 | cut -d',' -f2 | tr -d ' MiB' | awk '{printf "%.1f", $1/1024}')
        PLATFORM="CUDA"
    fi
fi

# ROCm (if no CUDA)
if [ -z "$PLATFORM" ] && command -v rocm-smi &>/dev/null; then
    GPU_INFO=$(rocm-smi --showmeminfo vram 2>/dev/null | grep -E "GPU|VRAM" | head -1)
    # Parse ROCm output — model and VRAM extraction varies by version
    PLATFORM="ROCm"
fi

# NPU (torch-based)
if [ -z "$PLATFORM" ]; then
    python3 -c "import torch_npu; print('NPU')" 2>/dev/null && PLATFORM="NPU"
fi

# XPU (Intel)
if [ -z "$PLATFORM" ]; then
    python3 -c "import torch.xpu; print('XPU')" 2>/dev/null && PLATFORM="XPU"
fi

# CPU-only fallback
if [ -z "$PLATFORM" ]; then
    PLATFORM="CPU"
    GPU_COUNT=0
    VRAM_PER_GPU_GB=0
fi
```

**Output variables:** `PLATFORM`, `GPU_COUNT`, `GPU_MODEL`, `VRAM_PER_GPU_GB`

---

## 3. Feasibility Check

Compare model requirements against available hardware.

### Model size estimation

Do NOT use parameter count × dtype bytes alone — this significantly underestimates actual VRAM:

```
estimated_vram_gb = (
    model_weights_gb          # param_count × dtype_bytes / 1e9
    + kv_cache_gb             # sequence_length × num_layers × 2 × hidden_size × dtype_bytes × batch_size / 1e9
    + activation_overhead_gb  # ~20-30% of model weights for inference
    + framework_overhead_gb   # ~1-2 GB for CUDA context, fragmentation
)
```

For quick estimation when KV cache size is unknown, use a multiplier:

| Model size | Quick estimate |
|-----------|---------------|
| < 7B params | weights × 1.5 |
| 7-14B params | weights × 2.0 |
| 14-70B params | weights × 2.5 |
| 70B+ params | weights × 3.0 |

### Verdict

| Condition | Verdict |
|-----------|---------|
| `estimated_vram_gb ≤ VRAM_PER_GPU_GB × GPU_COUNT` | `VERIFIABLE` |
| `estimated_vram_gb ≤ VRAM_PER_GPU_GB × GPU_COUNT × 1.5` and `--cpu-offload-gb` available | `NEEDS_OFFLOAD` |
| Otherwise | `CANNOT_VERIFY` |

**CPU-only path:** Can verify latency/accuracy for small models (< 2B params) that fit in system RAM. Cannot measure peak VRAM.

**No GPU path:** Cannot execute benchmarks. Proceed to static-only analysis.

---

## 4. Benchmark Plan Generation

Map PR type to benchmark runner.

| PR type | Benchmark runner | Notes |
|---------|-----------------|-------|
| Omni models (LLM) | `Omni(model=...).generate()` with `--log-stats` | Offline; or `vllm bench serve --omni` for online |
| Diffusion models | `benchmarks/diffusion/diffusion_benchmark_serving.py` | From vllm-omni repo |
| Accuracy (GEBench/GEdit-Bench) | `benchmarks/accuracy/` scripts | From vllm-omni repo |

### Execution strategy

1. Create git worktrees at `.claude/perf-worktrees/base` and `.claude/perf-worktrees/pr`
2. Install vllm-omni in each worktree (or share the install if dependencies are identical)
3. Run benchmark in base worktree, capture JSON results
4. Run benchmark in PR worktree, capture JSON results
5. Compare results

---

## 5. Tolerance Thresholds

These are **configurable defaults**. Adjust based on benchmark type, model size, and input variability.

| Metric | Default tolerance | When to tighten | When to loosen |
|--------|------------------|-----------------|----------------|
| Latency | ±10% | Microbenchmarks (< 100ms): ±20% | Large models with high variance: ±15% |
| Throughput | ±10% | High-concurrency benchmarks: ±15% | Single-request: ±20% |
| VRAM | ±5% | Small models (< 4GB): ±10% | Multi-GPU: ±10% |
| Accuracy | ±1% (absolute) | FID/SSIM: ±2% | Perplexity: ±0.5% |

**Disclaimer:** These thresholds assume controlled benchmark conditions (same hardware, same inputs, warm-up run completed). Results outside tolerance do not automatically mean NOT_CONFIRMED — check for measurement noise, input variability, or warm-up issues first.

---

## 6. Execution Limits

- **Hard timeout:** 20 minutes per benchmark run (base or PR). If exceeded, kill the process and report partial results with a `TIMEOUT` flag.
- **Pre-execution gate:** Before starting benchmark execution, present the plan to the user:
  - What benchmark will run
  - Estimated duration
  - Which model and hardware
  - Ask for explicit confirmation
- **No confirmation or timeout:** Fall back to static-only analysis.

---

## 7. Report Format

### Claimed vs Measured table

```markdown
## Perf Verification Report

**Reviewer hardware:** {GPU_MODEL} × {GPU_COUNT} ({VRAM_PER_GPU_GB} GB each), {PLATFORM}
**Verification mode:** {full | partial (offload) | static-only}
**Benchmark:** {type}

| Claim | Claimed | Measured | Delta | Verdict |
|-------|---------|----------|-------|---------|
| e2e latency | X ms | Y ms | +Z% | CONFIRMED / NOT_CONFIRMED / TIMEOUT |
| throughput | X tok/s | Y tok/s | -Z% | CONFIRMED / NOT_CONFIRMED / TIMEOUT |
| peak VRAM | X GB | Y GB | +Z GB | CONFIRMED / NOT_CONFIRMED / CANNOT_VERIFY |
```

### Verdict values

| Verdict | Meaning |
|---------|---------|
| `CONFIRMED` | Measured value within tolerance of claimed |
| `NOT_CONFIRMED` | Measured value outside tolerance |
| `CANNOT_VERIFY` | Hardware insufficient (model too large, no GPU) |
| `TIMEOUT` | Benchmark exceeded 20-min limit |
| `NOT_RUN` | Benchmark not executed (user declined or no clone) |

---

## 8. Graceful Degradation

| Level | Conditions | What runs |
|-------|-----------|-----------|
| **Full verification** | GPU available, model fits in VRAM | Before/after benchmarks, full comparison |
| **Partial verification** | GPU available, model needs offload | Benchmarks with `--cpu-offload-gb`, noted in report |
| **Static-only** | No GPU or model too large | Claim detection, analyze benchmark scripts in diff for correctness, flag implausible claims (e.g., "50% speedup" from a single-threaded loop change) |
| **Skip** | No relevant perf claims in PR | Do not activate this step |

### Static-only analysis checklist

When benchmarks cannot run, apply these checks to the benchmark/test code in the diff:

- [ ] Benchmark uses warm-up runs (at least 1) before timed runs
- [ ] Measurement uses `time.perf_counter()` or equivalent (not `time.time()`)
- [ ] VRAM measured via `torch.cuda.max_memory_allocated()` (not `nvidia-smi` at idle)
- [ ] Same hardware, model, inputs for before/after (not different machines)
- [ ] Multiple iterations reported (not single-run claims)
- [ ] No cherry-picked metrics (e.g., reporting best-of-5 without mentioning variance)

---

## 9. Delivery

1. **Local report first** — output the Claimed vs Measured table to the user
2. **Ask before posting** — "Post this as a PR comment? (y/n)"
3. If posting, use the existing review comment workflow (`gh api`) — this counts against the comment budget
4. If verification reveals a blocker (confirmed NOT_CONFIRMED for accuracy or VRAM regression), escalate to REQUEST_CHANGES via the normal verdict workflow
