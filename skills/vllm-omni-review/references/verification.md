# Verification (Hardware)

Active verification: run the PR code on real hardware, not just static analysis. This catches bugs that reading diffs cannot — crashes, missing import paths, metric mismatches, and claims that don't hold up at runtime.

## When to activate

- Bench/tool/metric PRs (e.g. `[Bench]`, `[Tool]`, `[CI]`)
- PRs introducing new metrics, new CLI flags, or new output formats
- Any PR where the reviewer has SSH/server/GPU access

**Skip** if no hardware access is available — proceed to domain review instead.

## Workflow

### 1. Checkout

```bash
gh pr checkout <n> --repo vllm-project/vllm-omni
```

On a remote server, use `ssh <server> "cd /path/to/repo && gh pr checkout <n>"` or `git fetch origin pull/<n>/head:pr-<n> && git checkout pr-<n>`.

### 2. Run unit tests

Run at minimum the tests for the changed area:

```bash
# For bench/tool changes
pytest tests/benchmarks/ -v -m "core_model"

# For specific test files mentioned in the PR
pytest tests/path/to/test_file.py -v
```

Verify all tests pass. If any fail, report which ones and whether the failure is pre-existing or introduced by the PR.

### 3. E2E smoke test

For bench/tool/metric PRs, run a minimal end-to-end test:

1. **Find a running server** or start one with an appropriate model
2. **Run a quick benchmark** — 10 prompts, low concurrency (2-4)
3. **Check that** new outputs appear, values are sensible, and the tool exits clean (no crash)

Example for a bench PR:
```bash
vllm bench serve --omni \
  --host <host> --port <port> \
  --model <model> \
  --backend openai-audio-speech \
  --endpoint /v1/audio/speech \
  --dataset-name seed-tts-design \
  --num-prompts 10 --num-warmups 2 \
  --max-concurrency 4 --request-rate inf \
  --percentile-metrics <new-metric> \
  --save-result --result-dir /tmp/bench-results
```

### 4. Compare claims vs actual output

Check the PR claims against the actual benchmark output:

- Do the new metrics appear in the output?
- Are values within expected ranges?
- Does `--save-result` produce valid JSON?
- Are there any crashes or error traces?

### 5. Report

Post findings as a PR comment. Include:
- Hardware used (GPU model, count)
- Test results (passed/failed counts)
- E2E output excerpt showing new behavior
- Any bugs found (with stack traces)
- Verdict: verified / bugs found / could not verify (reason)

Bugs found during verification are **blocking** — flag them in the review.

## Graceful degradation

| Level | Condition | What happens |
|-------|-----------|-------------|
| Full verification | Server + GPU + model available | Checkout, unit tests, E2E smoke, claim comparison |
| Unit tests only | Server available, no GPU free | Checkout, run unit tests, report |
| Static only | No hardware access | Skip verification, proceed to domain review |

## Common pitfalls

- **Python version mismatch** — the server may use a different Python than the default; check `.venv` or `uv` setup
- **Missing HF token** — gated models need `HF_TOKEN` set
- **Port conflicts** — check for existing servers with `ps aux | grep vllm`
- **StrEnum on 3.10** — vllm-omni requires Python ≥3.11; if the venv is 3.10, create a new one with `uv venv --python 3.12`
