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

### 5) Performance Comparison Test Checklist

**Required for:** `[Feature]` PRs that affect performance characteristics, and all `[Performance]` PRs.

Before approving, verify the PR includes performance comparison tests that measure the change against baseline (without the change).

**Minimum Requirements:**

- [ ] **Before/after benchmark** — Quantitative comparison on same hardware
- [ ] **Consistent environment** — Same GPU, driver, model, batch size, resolution/steps for both runs
- [ ] **Key metrics reported:**
  - [ ] Latency (e2e generation time)
  - [ ] Throughput (requests/sec or tokens/sec, where applicable)
  - [ ] Peak memory usage (VRAM in GB)
- [ ] **Methodology documented** — Commands, parameters, prompts/dataset used

**Evidence format to request when missing:**

```
⚠️ **Performance Comparison Test Required**

This PR includes a [feature/performance enhancement] that may affect performance.
Please provide benchmark comparison:

| Metric           | Baseline (w/o change) | With Change | Delta |
|------------------|----------------------|-------------|-------|
| Latency (e2e)    | <value> ms           | <value> ms  | +/- % |
| Throughput       | <value> req/s        | <value>     | +/- % |
| Peak VRAM        | <value> GB           | <value> GB  | +/- % |

Test environment: <GPU model>, <CUDA version>, <model>, <batch/resolution/steps>
Commands: <exact commands used>
```

**Exceptions:**
- Doc-only or config-only changes without performance impact
- Bug fixes that only correct logic without changing performance characteristics
- Changes gated behind a new flag that defaults to disabled (document expected perf when enabled)

**Reviewer-side verification:** For independently verifying contributor perf claims (running benchmarks yourself), see [perf-verification.md](perf-verification.md). This checklist defines what contributors must provide; that reference defines how reviewers can verify it.

