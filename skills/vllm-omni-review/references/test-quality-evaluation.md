# Test Quality Evaluation

Reviewer-side evaluation of test quality — run the affected tests, categorize failures, and grade quality. **Output is internal by default** (not posted to the PR); convert only the worst 1–2 findings into inline comments. Used in Step 8 of the main workflow.

This is the reviewer-side counterpart to [tests-docs-checklist.md](tests-docs-checklist.md) (which is contributor-facing: what tests/docs a PR must contain). For perf/accuracy A/B, see [perf-verification.md](perf-verification.md).

## 1) Static analysis (always runs)

Read the changed/added test files and score them, no hardware needed:

- **Assertion quality** — does the test assert the *new* behavior, or just `assert result is not None` / `assert True`? A test that exercises code without asserting the new logic is theater.
- **Anti-patterns** — flag: no assertions; `assert True`; sleep-based timing without retry; "tests the mock" (everything mocked, real path never runs); direct float `==`/`!=` instead of tolerance; hardcoded absolute paths; catching `Exception` and passing.
- **Marker compliance** — every test needs a level/hardware marker or CI skips it. Expected markers: `core_model` (CPU-runnable, fast), `advanced_model` (needs real GPU/model), `gpu_0`/`gpu_1`, `pre_merge`. No marker = test doesn't run. (See marker doc link in [tests-docs-checklist.md](tests-docs-checklist.md).)
- **Edge-case coverage** — None/empty input, error paths, boundary/shape conditions for the changed logic.

## 2) Detect hardware

Same detection as Step 7 (cross-ref [perf-verification.md](perf-verification.md)): is a GPU available? How much VRAM? Does the model fit? This decides the run-level below.

## 3) Find affected tests

Map changed **source** files to test files by content, not path convention:

```bash
# By import of the changed module
grep -rl "from vllm_omni.<changed_module>" tests/ 2>/dev/null
grep -rl "import vllm_omni.<changed_module>" tests/ 2>/dev/null
# By symbol (class/function) that changed
grep -rl "<ChangedClassOrFunc>" tests/ 2>/dev/null
```

## 4) Filter by hardware

Drop tests whose markers exceed what's available (e.g. skip `advanced_model`/`gpu_1` tests on a single-GPU or no-GPU box). Record which were skipped and why.

## 5) Run tests

```bash
.venv/bin/python -m pytest <affected_test_files> -v -s --run-level core_model
```

Default to `--run-level core_model`. Use `--run-level advanced_model` only when hardware is sufficient to actually run those tests. Use `-x` only when you want to stop at the first failure.

## 6) Categorize each failure

| Category | Signals |
|---|---|
| **Test bug** | assertion wrong/over-specified, brittle expected value, missing fixture/setup, bad mock |
| **Code bug** | the new code is actually wrong — the test caught a real regression (blocking) |
| **Infrastructure** | OOM, timeout, missing weight/env, network/flaky runner — not the PR's fault |
| **Flaky** | passes on retry, timing/ordering-dependent, non-deterministic seed |

A **code bug** found here is blocking — escalate via Step 9 (REQUEST_CHANGES). Everything else is a quality note.

## 7) Quality grade (internal, A–D)

Grade the changed tests across the static-analysis dimensions. **Internal only** — do not post grades.

| Grade | Meaning |
|---|---|
| **A** | Asserts the new behavior; clean markers; covers happy path + ≥1 edge/error case; no anti-patterns |
| **B** | Solid assertions but minor gap (e.g. missing one edge case, or a tolerance nit) |
| **C** | Weak assertions or a marker missing; exercises code but wouldn't catch a regression |
| **D** | Theater (no real assertions), pervasive anti-patterns, or a test bug — needs rewrite |

A **D** in any dimension, or a code bug found in step 6, escalates to REQUEST_CHANGES.

## Graceful degradation

| Level | Condition | What happens |
|---|---|---|
| Full analysis | Hardware matches test markers | Static analysis + run affected tests |
| Static-only | No GPU, or model too large | Static analysis only (steps 1 + 7); explicitly report which tests were skipped and why |

## Delivery

- Produce the assessment **locally first**; ask the user before posting anything to the PR.
- Convert at most the **worst 1–2 findings** into inline comments (these count against the comment budget in [review-execution.md](review-execution.md)).
- D-grade dimension or code bug → escalate to REQUEST_CHANGES via Step 9.
