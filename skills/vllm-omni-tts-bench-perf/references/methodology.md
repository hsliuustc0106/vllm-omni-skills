# TTS Perf Benchmark Methodology

## Sequential vs Parallel

Run benchmark cells **sequentially on the same GPU**. Do not parallelise across adjacent GPUs to save wall time — at `concurrency >= 8` the numbers degrade by:

- Inductor / CUDA-graph cold cache on the second process
- PCIe contention for ref-audio uploads
- Cross-process scheduler interference

Cold-cache effects can swing `c=8` median latency by 30-50%.

## Repetitions

Minimum **3 repetitions per cell**, drop the first. The first run pays one-shot costs:

- Model weight load from disk cache
- `torch.compile` / Inductor first-pass codegen
- CUDA graph capture

Median of runs 2–N is the headline number. Report the spread (min/max) alongside.

## Setting a CI Baseline

Order of operations:

1. Run the sweep three times.
2. Take the median of runs 2–3 per metric.
3. Add **~10% headroom** to the baseline (latency / RTF: round up; throughput: round down).
4. Commit alongside the change that produced it; do not retro-baseline regressions.

Re-baseline only when a documented optimisation lands. A re-baseline PR should reference the optimisation PR in its description.

## Warm vs Cold

For latency-sensitive metrics (`audio_ttfp_ms`, `ttft`), an explicit warm-up of 1–2 requests is required if the server has just started. CUDA-graph capture happens on the first sized input it sees; counting that in the median is misleading.

For throughput, sustained-state measurement matters more. Use `num_prompts >= 4 * concurrency` per cell so the saturation phase dominates.

## Hardware Class, Not Hardware Identity

Perf numbers depend on GPU class. When reporting:

- ✅ "single GPU, 80 GB HBM3, SM 9.0"
- ❌ a hostname or internal cluster label

Hardware class lets others reproduce; hardware identity does not.
