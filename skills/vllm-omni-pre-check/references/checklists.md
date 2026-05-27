# Pre-Check Checklists

Each item is a concrete check the skill runs against the diff. ✗ = fix before PR. ⚠ = consider fixing.

## All PRs: Title Format (check first)

PR title must follow the structured format:

```
[domain][type][hardware?] title
```

| Tag | Required | Values |
|-----|----------|--------|
| **Domain** | Yes | `omni`, `tts`, `diffusion`, `world-model`, `image`, `video`, `audio`, `engine`, `worker`, `entrypoint`, `ci`, `docs` |
| **Type** | Yes | `feature`, `bugfix`, `perf`, `refactor`, `doc`, `test`, `ci`, `hotfix`, `release` |
| **Hardware** | Only if NOT GPU | `NPU`, `ROCm`, `XPU` |

**Examples:**

```
✓ [tts][feature] Add MiniCPM-o 4.5 support
✓ [diffusion][bugfix] Fix Ovis image text encoder dtype
✓ [omni][perf] Qwen3-Omni performance optimization
✓ [tts][bugfix][NPU] Fix VoxCPM2 on Ascend
✗ Fix Ovis image text encoder dtype          ← missing [domain][type]
✗ [Perf] Qwen3-Omni optimization             ← missing [domain], wrong case
✗ [WIP]: Add model                           ← WIP in title, no structured tag
```

- [ ] **Title matches `[domain][type][hardware?] title`** — ✗ if missing tags, wrong case, or WIP/Draft in title

---

## Bug Fix PRs

### Quick

- [ ] **PR body has 4 sections:** what broke (error message), repro steps, root cause, fix description
- [ ] **Fix is minimal:** diff touches only files directly related to the bug. No unrelated refactors or style changes.
- [ ] **Repro is runnable:** the PR body includes a copy-paste command that reproduces the bug
- [ ] **Branch is rebased:** `git merge-base HEAD origin/main` is recent, no merge conflicts

### Full (adds)

- [ ] **Regression test exists:** `git diff --name-only` includes at least one `tests/` file
- [ ] **Regression test reproduces the original error:** the test would fail on main, pass on this branch
- [ ] **Fix matches root cause exactly:** no "fix the symptom + something else" — if the root cause is dtype, the fix is dtype, not dtype + reformatting
- [ ] **No silent failure risk:** no bare `except: pass`, no `try: ... except: return None`, no empty fallback added
- [ ] **Upstream pattern match:** the fix follows the same pattern as existing code for similar cases (grep for analogous `from_pretrained` calls, etc.)
- [ ] **Environment documented:** torch/transformers/vllm versions listed if the bug is version-dependent

## Performance PRs

### Quick

- [ ] **Before/after numbers in PR body:** at minimum, one metric (RTF, RPS, latency, VRAM) with main vs PR values
- [ ] **Hardware specified:** GPU model, count, VRAM. "L4" or "H20" is sufficient. "tested on GPU" is not.
- [ ] **Concurrency scaling:** if the optimization claims better throughput, numbers at 2+ concurrency levels
- [ ] **No unexplained regressions:** if any metric goes down at any concurrency level, explain why
- [ ] **Branch is rebased:** `git merge-base HEAD origin/main` is recent, no merge conflicts

### Full (adds)

- [ ] **Software versions:** torch, CUDA, vllm, vllm-omni versions in PR body
- [ ] **Warmup stated:** "1 warmup + 3 measured" or equivalent
- [ ] **Stddev or range:** not just a single best run. "average of 2 rounds" is minimum.
- [ ] **VRAM measured:** peak GPU memory before and after
- [ ] **Benchmark script checked in:** under `tests/` or `examples/`, runnable by reviewer
- [ ] **Exact command line in PR:** not pseudocode, not "run the benchmark"
- [ ] **Pytest summary included:** `36 passed, 3 skipped, 17 warnings in 2897.66s` — proves the whole suite passes
- [ ] **Config changes documented:** if `max_num_seqs`, `gpu_memory_utilization`, or deploy YAML changed, old and new values stated with reasoning

## New Model PRs

### Quick

- [ ] **PR body file list matches `git diff --name-only`:** every file path in the description exists in the diff
- [ ] **Registry entries match claimed count:** count `_OMNI_MODELS` entries added vs claimed in body
- [ ] **Pipeline config `custom_process_input_func` paths resolve:** each referenced module.function exists
- [ ] **`__init__.py` exports match registry:** each registered class appears in `__init__.py` and `__all__`
- [ ] **Shell script modes match README:** `run_curl.sh` supports every mode the README documents
- [ ] **Branch is rebased:** `git merge-base HEAD origin/main` is recent, no merge conflicts

### Full (adds)

- [ ] **Dead code scan (5 patterns):** dead `forward()`, dead factory/builder fns, dead wrappers, dead branch guards, unused params
- [ ] **Copy-paste detection:** no string constant defined in 3+ files, no cross-module validation duplication, no near-identical shape coercion fns
- [ ] **Import hygiene:** no re-export-only imports, no module-level side effects without docs, no `import os` in function body when already at top
- [ ] **Accuracy:** at least one test compares output against reference; audio = valid WAV at correct sample rate; determinism verified if seed claimed
- [ ] **Performance:** hardware, software versions, warmup, and metrics (RTF, VRAM, RPS, latency) stated
- [ ] **Benchmark settings:** model config (TP, PP, max_model_len, enforce_eager, quant), runtime config (batch, input/output spec), environment versions
- [ ] **Benchmark script checked in + exact command line + pytest summary**

## General PRs

### Quick

- [ ] **PR body matches diff:** description doesn't claim changes not in the diff
- [ ] **Branch is rebased:** `git merge-base HEAD origin/main` is recent, no merge conflicts
- [ ] **CI gates passing:** DCO, pre-commit, build — check `gh pr view --json statusCheckRollup`

### Full (adds)

- [ ] **No new dead code in changed files:** scan for unreachable paths, unused imports
- [ ] **Test coverage:** if core code changed (`engine/`, `stages/`, `connectors/`), tests are added or existing tests cover the path
- [ ] **Import hygiene:** no redundant imports added
