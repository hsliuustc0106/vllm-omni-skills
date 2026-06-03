---
name: vllm-omni-tts-bench-perf
description: Benchmark TTS serving performance in vLLM-Omni, covering RTF, TTFA/TTFP, end-to-end latency, audio throughput, and concurrency sweeps. Use when measuring TTS latency or throughput, comparing two builds for regressions, sweeping max-concurrency, sizing GPU capacity for a TTS deployment, or writing a `tests/dfx/perf/tests/test_*.json` baseline for CI.
---

# vLLM-Omni TTS Performance Benchmark

## Overview

TTS serving has streaming-audio metrics that text-generation benchmarks do not report. Use the universal CLI at `benchmarks/tts/bench_tts.py`, which wraps `vllm bench serve --omni` with audio-aware metric extraction. Pair it with the `tests/dfx/perf/tests/test_*.json` schema when you need a baseline that CI can enforce.

## Metrics

| Metric | Meaning | Read as |
|---|---|---|
| `audio_ttfp_ms` | Time to first **audio packet** | User-perceived start-of-speech latency |
| `audio_rtf` | Wall time / synthesized audio duration | <1.0 = faster than real-time |
| `audio_throughput` | Total synthesized seconds / wall seconds | Server-side capacity |
| `audio_duration` | Per-request synthesized seconds | Sanity check for early termination |
| `ttft`, `e2el` | First token, end-to-end latency | Standard vLLM metrics, still useful |

`audio_ttfp_ms` is the right latency metric for **streaming** TTS. `audio_rtf` is the right metric for **non-streaming** quality of serving. Both should be reported.

## Workflow

### 1. Start the server (no CUDA-graph debug noise)

```bash
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --omni --port 8000
```

For models requiring `trust_remote_code` under vllm 0.22+, pass it explicitly — `bench_tts.py` forwards extra args after `--` to the underlying client. See [references/vllm-022-trust-remote-code.md](references/vllm-022-trust-remote-code.md).

### 2. Run a concurrency sweep

```bash
python benchmarks/tts/bench_tts.py \
  --model Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
  --task voice_clone \
  --dataset-name seed-tts \
  --dataset-path linyueqian/seed-tts-eval-subset \
  --concurrency 1 4 8 16 \
  --num-prompts 20 80 128 128 \
  --locale en \
  --host localhost --port 8000
```

`--concurrency` and `--num-prompts` are aligned positionally. For accurate measurements, **`num_prompts ≥ 4 × concurrency`** at each level so the saturation phase dominates.

### 3. Sequential runs, same hardware, ≥3 repetitions

Benchmark cells must run **sequentially on the same GPU**, with at least 3 repetitions per cell, and the warm cell discarded. Parallel runs on adjacent GPUs distort `c=8+` measurements via inductor cold-cache and PCIe contention. See [references/methodology.md](references/methodology.md).

### 4. Compare against a baseline

Two patterns:

**Ad-hoc comparison (two branches):**
```bash
# Run the sweep on main and on the PR branch, then diff the JSON.
python benchmarks/tts/bench_tts.py ... --output-dir results/main
python benchmarks/tts/bench_tts.py ... --output-dir results/pr
diff <(jq -S . results/main/*.json) <(jq -S . results/pr/*.json)
```

**CI-enforced baseline:** add a cell to `tests/dfx/perf/tests/test_tts.json` with a `baseline` block. The fields below are checked by `--assert-baseline`:

```json
{
  "task": "voice_clone",
  "eval_phase": "latency",
  "max_concurrency": [1],
  "num_prompts":     [20],
  "baseline": {
    "median_audio_ttfp_ms": [3000],
    "median_audio_rtf":     [0.6]
  }
}
```

Throughput cells additionally use `audio_throughput`:
```json
"baseline": {
  "median_audio_ttfp_ms": [1000, 3000, 14000],
  "median_audio_rtf":     [0.70, 1.15, 3.90],
  "audio_throughput":     [12,   14,   14]
}
```

Each baseline array index lines up with the `max_concurrency` and `num_prompts` index. Set baselines from the **median of ≥3 sequential runs**, then add ~10% headroom so CI does not flake on noise.

See [references/test-tts-json-schema.md](references/test-tts-json-schema.md) for the full schema.

## Pre-Bench Server Hygiene

Zombie vllm processes return engine-dead 500s that look like real perf regressions. Before any bench:

```bash
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
ps -ef | grep -E 'vllm|python' | grep -v grep
```

Confirm exactly one server is running on the target GPU and no orphan workers (`StageDiffusionProc`, `vllm::Worker`) are holding memory. Kill orphans by PID — not by pattern.

## Profiling (when bench numbers say "regression" but you do not know where)

Three layers, escalate as needed:

| Layer | Tool | Use for |
|---|---|---|
| Server-side | `VLLM_TORCH_PROFILER_DIR=...` + `/start_profile` HTTP hook | Per-step Stage 1 / Stage 2 breakdown |
| Client-side | `bench_tts.py --profile` | Tokenization / I/O cost |
| GPU kernels | nsys, then NCU for hot kernels | Attention/RMSNorm regressions |

See [references/profiling.md](references/profiling.md) for the exact recipes.

## Common Mistakes

| Symptom | Cause | Fix |
|---|---|---|
| `c=8+` numbers fluctuate ±30% | Inductor cold cache + adjacent-GPU runs | Sequential same-GPU runs, ≥3 reps, drop first |
| `audio_throughput` flat across concurrencies | Server bottleneck before benchmark saturates | Increase `--num-prompts`, recheck `nvidia-smi` utilization |
| `audio_ttfp_ms` baseline keeps regressing | First-request graph capture counted in median | Warm-up phase: discard first N requests, or set `--num-warmup` |
| `bench` returns 500s | Zombie server / engine dead | Pre-bench hygiene above |
| Base TTS variants reject the request instantly | Base task needs `ref_audio` | Use `voice_clone` with seed-tts, not `tts` |

## References

- [methodology.md](references/methodology.md) — sequential vs. parallel runs, repetitions, what to drop
- [test-tts-json-schema.md](references/test-tts-json-schema.md) — perf JSON schema and `--assert-baseline` semantics
- [profiling.md](references/profiling.md) — torch profiler, nsys, NCU recipes
- [vllm-022-trust-remote-code.md](references/vllm-022-trust-remote-code.md) — `trust_remote_code` under vllm 0.22+
