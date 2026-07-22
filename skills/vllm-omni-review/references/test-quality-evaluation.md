# Test Quality Evaluation

Full workflow for **Step 8 (Evaluate Test Quality)** of the main review. Load this when a PR adds or
modifies test files, touches core code (`engine/`, `core/`, `worker/`,
`distributed/omni_connectors/`, `distributed/omni_coordinator/`, or diffusion runtime paths)
without adding tests, or is test-only. Produces an **internal** quality assessment — do not paste
the grades into the PR; convert only the worst 1-2 findings into inline comments (they count against
the comment budget).

## Goal

"Tests pass" is not "tests are good." A green suite with weak assertions, wrong markers, or missing
edge cases gives false confidence. This step scores whether the tests actually *prove* the change is
correct, and runs the affected ones where hardware allows.

## Workflow

### 1. Static analysis (always runs, no hardware needed)

Read the added/modified test files and check:

- **Assertion quality** — assertions pin the behavior that matters, not incidental output. Flag:
  `assert result is not None` / `assert len(x) > 0` as the *only* check; asserting on log strings;
  snapshot asserts with no invariant; `assert True` / commented-out asserts.
- **Anti-patterns** — no real assertion (test only runs code); over-mocking that stubs out the very
  thing under test; non-deterministic tests (unseeded RNG, wall-clock, ordering-dependent);
  `try/except: pass` swallowing the failure; sleeps instead of syncs; tests that never fail if the
  code is broken (mutate the code mentally — would this test catch it?).
- **Marker compliance** — the test declares the right run level (`core_model` = L1&L2,
  `advanced_model` = L3, `full_model` = L4) and domain marker (`omni`/`tts`/`diffusion`). A GPU/model
  test left unmarked will run in CPU CI and either fail or silently skip. See
  [tests-docs-checklist.md](tests-docs-checklist.md) for the coverage matrix.
- **Edge-case coverage** — batch > 1, empty input, max length, error/abort paths, and the specific
  regression the PR fixes (a `[Bugfix]` PR without a test that fails before the fix is a blocker).

### 2. Detect hardware

Use the hardware detection in [perf-verification.md](perf-verification.md). Determine available
GPU/accelerator and installed model assets before deciding what can run.

### 3. Find affected tests

Map changed source files to their tests by **grep**, not path convention (omni test layout does not
mirror `vllm_omni/`): grep the changed module/symbol names across `tests/` to find which tests
exercise them. Note any changed source file with **no** covering test.

### 4. Filter by hardware

Skip tests whose markers require resources not present (e.g. `full_model` / multi-GPU on a single-GPU
box). Record what was skipped and why — a skipped test is not a passed test.

### 5. Run the affected tests

Default to the CPU-safe level, escalate only if hardware is sufficient:

```
pytest <affected tests> --run-level core_model      # default
pytest <affected tests> --run-level advanced_model  # only if hardware matches
```

### 6. Categorize failures

For each failure, classify before reporting: **test bug** (assertion/fixture wrong) / **code bug**
(the PR is actually broken) / **infrastructure** (env, missing asset) / **flaky** (passes on rerun —
note it, don't hide it). Only code bugs and D-grade quality issues are blocking.

### 7. Assess quality (A–D, internal only)

Grade each dimension for your own summary; do not post the letter grades:

| Dimension | A | D (blocking) |
|-----------|---|--------------|
| Assertion quality | Pins the contract; fails if behavior regresses | No meaningful assertion / only smoke |
| Edge-case coverage | Batch, empty, max-len, error path, the fixed regression | Happy path only |
| Marker compliance | Correct run level + domain marker | Wrong/missing → runs in the wrong CI lane |
| Anti-patterns | None | Over-mocked / non-deterministic / can't fail |

## Graceful degradation

| Level | Condition | What happens |
|-------|-----------|--------------|
| Full analysis | Hardware matches test markers | Static analysis **+** runtime execution |
| Static-only | Hardware doesn't match / no GPU | Static analysis only; report which tests were skipped and why |

## Delivery

Assemble the assessment **locally first, then ask before posting.** Convert the worst 1-2 findings to
inline comments (counted against the comment budget). If a **D-grade dimension** or a **code bug** is
found, escalate to REQUEST_CHANGES via Step 9. Everything else stays in the local summary — this step
raises confidence, it is not a coverage-theater dump onto the author.
