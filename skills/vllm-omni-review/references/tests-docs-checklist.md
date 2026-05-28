## PR Tests & Docs Review Addendum

This reference adds two structured outputs for `vllm-omni-review`:

- Coverage matrix (change point → existing tests → gap → minimal fix)
- PR description checklist (environment + runtime estimate + fill-in template)

### 1) Coverage Matrix (required for high-risk changes)

Use this format. Keep it short and actionable.

- Change point:
  - What changed:
  - Risk if broken:
  - Where it lives (paths/modules):
- Existing tests:
  - Unit tests:
  - E2E tests (`tests/e2e/`):
  - Example/gate tests (if any):
- Gaps:
  - Missing behavior coverage:
  - Missing failure/boundary case:
  - Missing regression (for bugfix):
- Minimal add:
  - Suggested test file(s):
  - Suggested test cases (1–3 bullets):
  - Suggested assertions (stable, deterministic):

### 2) Style / Tag / Stability Checklist (quick pass)

- Markers/labels follow repository CI docs and are justified (no marker sprawl).
- Assertions are stable (avoid external network/time/randomness).
- Numeric assertions avoid direct float `==` / `!=` and use tolerances/approx checks.
- Test names and failure messages are readable and help locate the issue quickly.

### Optional References (use as needed)

- CI test levels: `https://docs.vllm.ai/projects/vllm-omni/en/latest/contributing/ci/CI_5levels/`
- Test markers: `https://docs.vllm.ai/projects/vllm-omni/en/latest/contributing/ci/tests_markers/`
- Tests entry point: `https://github.com/vllm-project/vllm-omni/tree/main/tests`
- For anything else, open the most relevant pages under `vllm-omni/docs` based on the PR's change points.

### 3) Docs Sync Checklist (examples ↔ docs)

- If `examples/` README/docs were changed, ensure the corresponding `docs/` entry points are updated (avoid stale user-facing docs). If the repository uses MkDocs, run `mkdocs serve` to preview the docs site locally and verify the navigation/entry pages reflect the changes.
- If a new model/feature/parameter/default changed, ensure `vllm-omni/docs` includes:
  - What it is / how to use
  - Constraints and known limitations
  - Minimal runnable example (when appropriate)

### 4) PR Description Checklist (environment + runtime)

Ensure the PR description includes:

- Required hardware/environment:
  - CPU/GPU type, VRAM, CUDA/driver (or ROCm/NPU/XPU), OS
  - Python/vllm/vllm-omni version, key package versions (if relevant)
- What was run:
  - Commands (exact)
  - Expected outputs (brief)
- Runtime estimate:
  - Rough duration (order of magnitude is enough)

Fill-in template (2–3 lines):

```
Test env: <CPU/GPU + VRAM>, <CUDA/driver>, <OS>, Python <ver>
Commands: <cmd1>; <cmd2>
Runtime: ~<N> min
```

### 5) Performance + Accuracy A/B Test Checklist

**Required for:** `[Feature]` PRs that affect performance characteristics, and all `[Performance]` / `[Perf]` PRs.

Before approving, verify the PR includes **A/B test results for both performance AND accuracy** — comparing PR branch vs baseline (main) on the same hardware with the same inputs. A speedup that silently degrades output quality is a blocker.

**Minimum Requirements — Performance:**

- [ ] **Before/after benchmark** — Quantitative comparison on same hardware (A/B: baseline main vs PR branch)
- [ ] **Consistent environment** — Same GPU, driver, model, batch size, resolution/steps for both runs
- [ ] **Key metrics reported (mean ± stddev over ≥3 runs, warmup excluded):**
  - [ ] Latency (e2e generation time)
  - [ ] Throughput (requests/sec or tokens/sec, where applicable)
  - [ ] Peak memory usage (VRAM in GB)
- [ ] **Methodology documented** — Exact commands, parameters, prompts/dataset used, software versions

**Minimum Requirements — Accuracy:**

- [ ] **A/B accuracy comparison** — Same inputs, same seeds, baseline vs PR
- [ ] **Quantitative metric** where possible (PSNR, SSIM, MCD, WER, cosine similarity, etc.)
- [ ] **Side-by-side samples** when no quantitative metric exists (visual comparison for images/video, audio clips for TTS)
- [ ] **Tolerance explicitly stated** — what deviation is acceptable and why
- [ ] **fp16/bf16 accuracy verified** — if mixed-precision paths are changed, compare against fp32 baseline

**Evidence format to request when missing:**

```
⚠️ **Performance + Accuracy A/B Test Required**

This PR includes a [feature/performance enhancement] that may affect performance.
Please provide A/B comparison (baseline main vs this PR, same hardware, same inputs):

**Performance:**

| Metric           | Baseline (main) | This PR | Delta |
|------------------|-----------------|---------|-------|
| Latency (e2e)    | <value> ms      | <value> ms | +/- % |
| Throughput       | <value> req/s   | <value>    | +/- % |
| Peak VRAM        | <value> GB      | <value> GB | +/- % |

**Accuracy:**

| Metric           | Baseline (main) | This PR | Delta | Tolerance |
|------------------|-----------------|---------|-------|-----------|
| <PSNR/SSIM/etc.> | <value>         | <value> | ±Δ    | ≤ X       |

Test environment: <GPU model>, <CUDA version>, <torch version>, <vllm version>, <model>, <batch/resolution/steps>
Commands: <exact commands used for both runs>
Warmup: <# warmup runs excluded>, Measured runs: <# runs>, Reported as: mean ± stddev
```

**Blocking if missing:**
- No accuracy comparison → REQUEST_CHANGES (perf gain at quality cost is not acceptable)
- Accuracy regression (any visible/audible degradation or metric outside tolerance) → REQUEST_CHANGES
- Single measurement without stddev → request re-measurement
- No warmup excluded → request re-measurement
- Different seeds for baseline vs PR in accuracy test → request re-measurement

**Exceptions:**
- Doc-only or config-only changes without performance impact
- Bug fixes that only correct logic without changing performance characteristics
- Changes gated behind a new flag that defaults to disabled (document expected perf + accuracy when enabled)

**Reviewer-side verification:** For independently verifying contributor claims (running A/B benchmarks yourself), see [perf-verification.md](perf-verification.md). That reference covers git worktree setup, A/B execution, claimed-vs-measured reporting, and regression rules.

