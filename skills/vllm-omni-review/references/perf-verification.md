# Performance & Accuracy Verification (A/B Testing)

Use when the PR has `[Performance]` / `[Perf]` prefix, or the PR body claims quantitative perf/accuracy improvements. This reference covers both reviewer-side verification and contributor-side evidence requirements.

---

## Core Principle: A/B Testing Required

**Every perf PR must provide A/B test results for both performance AND accuracy.** A speedup that silently degrades output quality is not acceptable. The reviewer must ask for both before approving.

**A/B test = same hardware, same inputs, same methodology, comparing PR branch vs baseline.**

---

## Contributor Evidence Requirements

### What to ask for (blocking if missing)

When reviewing a `[Performance]` PR, request the contributor provide:

**1. Performance A/B table:**

| Metric | Baseline (main) | This PR | Delta |
|--------|-----------------|---------|-------|
| End-to-end latency | X ms | Y ms | ±Z% |
| Throughput | X req/s | Y req/s | ±Z% |
| Peak VRAM | X GB | Y GB | ±Z% |
| TTFT (if AR model) | X ms | Y ms | ±Z% |

**2. Accuracy A/B table:**

| Metric | Baseline (main) | This PR | Delta | Tolerance |
|--------|-----------------|---------|-------|-----------|
| Output metric (PSNR/SSIM/MCD/WER/etc.) | X | Y | ±Δ | ≤ threshold |

If no quantitative metric exists (e.g., image quality), provide side-by-side visual/audio comparison samples from identical inputs. Flag any visible degradation as blocking.

**3. Environment spec:**
- GPU model + count + VRAM
- `torch.__version__`, CUDA version, vllm version, vllm-omni version
- Model checkpoint (HF repo ID or path)
- Batch size, concurrency, input spec (prompt length, audio duration, image resolution, etc.)
- `max_num_seqs`, `gpu_memory_utilization`, and any non-default config values

**4. Methodology:**
- At least 1 warmup run (excluded from measurements)
- At least 3 measured runs, reported as mean ± stddev
- Exact commands used for both baseline and PR runs
- Seed fixed for accuracy comparisons

---

## Regression Rules

| Regression | Severity | Action |
|------------|----------|--------|
| Accuracy degradation (any visible/audible, or metric outside tolerance) | **Blocking** | REQUEST_CHANGES — perf gain at quality cost is not acceptable |
| VRAM regression > 5% | **Blocking** | Must be justified or fixed |
| Latency regression > 10% | **Warning** | Must be explained (e.g., "amortized at higher batch sizes") |
| Throughput regression at any concurrency level | **Warning** | Must be explained or addressed |
| Missing accuracy comparison entirely | **Blocking** | Request accuracy A/B before proceeding |

---

## Reviewer-Side Verification

When hardware is available, independently verify the contributor's claims.

### Setup: Git worktrees for clean A/B

```bash
# Clone fresh
git clone https://github.com/vllm-project/vllm-omni pr-<NUMBER>-perf
cd pr-<NUMBER>-perf

# Baseline worktree (main)
git worktree add ../baseline main

# PR worktree
git fetch origin pull/<NUMBER>/head:pr-branch
git worktree add ../pr-branch pr-branch
```

### Environment setup (both worktrees)

```bash
# In each worktree:
rm -rf .venv
uv venv --python 3.12 .venv
uv sync
uv pip install vllm==<VERSION>
export HF_HOME=/path/to/hf-cache
```

### Run A/B benchmarks

```bash
# Baseline
cd ../baseline
.venv/bin/python -m pytest tests/benchmarks/<test> -v -s --json-report 2>&1 | tee baseline.log

# PR
cd ../pr-branch
.venv/bin/python -m pytest tests/benchmarks/<test> -v -s --json-report 2>&1 | tee pr.log
```

### Compare and report

Produce a Claimed vs Measured table:

```
CLAIMED vs MEASURED

| Metric        | Contributor Claim | Measured (Reviewer) | Match?     |
|---------------|-------------------|----------------------|------------|
| Latency       | -15%             | -13.5%              | CONFIRMED  |
| Throughput    | +20%             | +18.2%              | CONFIRMED  |
| VRAM          | no change        | +0.3 GB             | CONFIRMED  |
| Accuracy      | no regression    | ΔPSNR -0.02 dB      | CONFIRMED  |

Verdict: PASS / NOT_CONFIRMED (explain discrepancy)
```

---

## Graceful Degradation

| Level | Condition | What happens |
|-------|-----------|-------------|
| Full verification | GPU available, model fits, benchmark exists | Run A/B perf + accuracy (both worktrees) |
| Perf-only | GPU available, no accuracy benchmark in repo | Run A/B perf, request contributor provide accuracy evidence |
| Static-only | No GPU or model too large | Analyze benchmark scripts for correctness, check contributor's methodology for red flags (missing warmup, single run, no stddev, no accuracy test) |
| Skip | No perf claims in PR | Do not activate |

---

## Common Red Flags in Contributor Benchmarks

- Single measurement (no mean ± stddev)
- No warmup excluded
- Different batch sizes / inputs for baseline vs PR
- Claims improvement but only measured at one concurrency level
- No accuracy comparison at all ("it looks the same")
- Hardware/software versions not documented
- Cherry-picked best run rather than average
- Accuracy measured with different seeds for baseline vs PR
