# Review Discipline

Mechanics for *how* to review — the multi-pass process, strictness-by-area, and comment/test hygiene. Load on top of the Blocker Scan (Step 2) and the Comment Budget ([review-execution.md](review-execution.md)). Adapted from the graham-code-review pattern, ported to Python/vllm-omni (no Rust-specific rules).

## Review passes: iterate, then a forced second pass

A single linear sweep finds the obvious; later passes find the real bugs.

1. **Loop.** Using the Blocker Scan + the loaded domain reference, find one issue. Repeat — multiple passes over each changed hunk — until a full pass surfaces nothing new.
2. **Second-Pass Checklist (required before finalizing).** One more focused pass over each changed hunk, explicitly for:
   - **Correctness** — logic inversion, missing return, off-by-one, silent exception swallow
   - **Concurrency / async** — locks held across `await`, spawned-task lifecycle, cancellation, shared mutable state
   - **Naming** — misleading names, `is_`/`has_`/`needs_` for bools, names implying more than they do
   - **Comment hygiene** — see below
   - **Test adequacy** — see below
3. **Report all findings internally — then apply the Comment Budget.** Track every finding (category + file:line) in your notes. Do *not* paste them all to GitHub; filter through the budget in [review-execution.md](review-execution.md) (cap 5–6, ~50% one-liners) and drop the least important. "Report all" is an internal discipline; what you post is budgeted.

## Strictness by area

Be strict where correctness, lifecycle, or concurrency matters; lean to non-blocking suggestions elsewhere. Depth follows risk (mirrors [review-routing.md](review-routing.md)).

| Strict — block on real issues | Suggestions-only |
|---|---|
| `vllm_omni/engine/`, `stages/`, `connectors/`, `diffusion/`, `model_executor/models/` | docs, config/yaml, examples, README, peripheral scripts |
| async/distributed coordination, KV cache, tensor-parallel paths | formatting, import order (unless it masks correctness) |

## Comment hygiene (Python)

- **Delete comments that restate the code or the function name.** `i += 1  # increment i` goes.
- **No history in comments** — "that's what git is for." Remove `# used to be X`, `# changed from Y to Z`.
- **AI-generated obvious comments are a smell.** Flag dense blocks of `# Load the model` / `# Check if valid` restatement; ask the author to delete the verbose ones and keep the rest useful.
- **Docstrings (`"""..."""`) are the public contract; `# ...` is internal.** Don't mix them, and don't write a docstring that merely restates the signature. A docstring on a trivial private helper is usually noise.
- **Drop commented-out code.** "Remove the commented out code" — git holds the old version.

## Test hygiene

- **Behavior coverage > line coverage.** Ask "is the new logic exercised?", not "is the diff touched?" A test that calls the code without asserting the new behavior is theater.
- **Be skeptical of long lists of similar test cases** (especially AI-added). Push for the 3 most important — the ones that would actually catch a regression. Tests should cover behavior, not exhaustively enumerate inputs.
- **pytest markers are required** (`core_model`, `gpu_0`, `pre_merge`, …). Without them the test doesn't run in CI. See [tests-docs-checklist.md](tests-docs-checklist.md).
- **`[Bugfix]` PRs must include a regression test that reproduces the original bug.** A fix without one is incomplete.

## Minimal diff surface

A PR should do one thing well. Call out scope creep directly — "Is this change related?", "This part seems unrelated to the rest of the PR." Unrelated refactors mixed into a feature PR get flagged, not silently approved.
