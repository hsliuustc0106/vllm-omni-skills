# Review Execution

Use this file when you are actively running the review and need the gate checks, concrete `gh` commands, or comment-writing rules.

## Review Gates

Check these before deep review. If any fail, stop and post a short comment instead of doing a full review.

| Check | Passing State | Action if Failed |
|-------|---------------|------------------|
| DCO | `SUCCESS` | Ask for signed commits with `git commit -s` |
| pre-commit | `SUCCESS` | "Please fix pre-commit" |
| mergeable | `MERGEABLE` | Ask the author to rebase and resolve conflicts |

Command:

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni --json mergeable,statusCheckRollup --jq '{mergeable, checks: [.statusCheckRollup[] | {name, conclusion}]}'
```

Gate-failure comment -- keep it short, no template:

```text
DCO / pre-commit / merge conflict needs fixing before review.
```

## Minimal Fetch Sequence

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni --json title,body,author,state,files,closingIssuesReferences
gh pr diff <pr_number> --repo vllm-project/vllm-omni
```

For linked issues:

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni --json closingIssuesReferences --jq '.closingIssuesReferences[] | {number, title, body}'
gh issue view <issue_number> --repo vllm-project/vllm-omni --json title,body,labels,state,comments
```

For more code context:

```bash
gh api repos/vllm-project/vllm-omni/contents/<path>?ref=<branch>
gh search code --repo vllm-project/vllm-omni "class <SymbolName>"
gh search code --repo vllm-project/vllm-omni "<config_key>" --extension yaml
```

## Comment Budget

| PR Shape | Inline Comments |
|----------|-----------------|
| docs-only or tiny fix | 0 -- empty APPROVE or "LGTM" |
| medium bug fix | 1-3 |
| large feature or risky refactor | 3-5 |
| **hard ceiling** | **6** |

Budget rules:

- Cap normal reviews at 5 inline comments. Never exceed 6.
- Merge related issues into one comment
- Skip low-confidence speculation
- If domain review already surfaced issues, skip extra comments
- **~50% of comments should be 1-line** -- suggestion blocks, "Seems unused", "ditto"
- When you have many findings, drop the least important ones

## Comment Style (Calibrated from 200 DarkLight1337 Reviews)

Real maintainer reviews are **direct, short, and varied**. The following rules are calibrated from a deep analysis of DarkLight1337 (Cyrus Leung) -- vllm's most active reviewer -- plus 12 other core maintainers. See [maintainer-style-study.md](maintainer-style-study.md) for the raw data.

### Review Body

- **~50% of reviews should have NO body** -- just inline comments with empty body string.
- When present, one line max. Vary:
  - "LGTM." / "Looks good."
  - "Thanks" / "Thanks for fixing!"
  - "Some more nits"
  - "Please fix pre-commit"
  - Sometimes just a high-level architectural point with no preamble
- **Do NOT say "left a few comments" or "left a couple comments"** -- the inlines speak for themselves.
- Skip "thanks" sometimes. Lowercase is fine.

### Inline Comment Tone

**Default: DIRECT.** Hedging should be ~15% of comments.

**For clear issues:**
- Direct statement: "This won't work when X is None." / "Seems unused"
- Direct question: "Is this really needed?" / "Where is this defined?"
- Imperative: "Please keep in alphabetical order" / "Move imports to the top"
- "Can you..." request: "Can you address this?" / "Can you move X to Y?"

**For uncertain findings only:**
- "Tbh I think..." / "Not sure if this is intentional --"

**For trivial issues:**
- Do NOT prefix with "Nit:" -- just state it. "Extra whitespace." not "Nit: extra whitespace."
- "ditto" / "same" when repeating
- suggestion block with no explanation text

**Recurring patterns (from DarkLight1337):**

| Context | Phrase |
|---------|--------|
| Imports | "Move imports to the top" |
| Ordering | "Please keep in alphabetical order" |
| Dead code | "Seems unused" / "Remove the commented out code" |
| Scope creep | "Is this change related?" |
| Pre-commit | "Please fix pre-commit" |
| Follow-up | "Can you address this?" / "Any update?" |
| Design | "Let's keep things simple" / "I prefer X" / "IMO..." |

### Banned Patterns

- Generic praise: "Good placement", "Well structured", "Nice refactor"
- Sycophantic openers: "Thanks for tackling this", "Great work"
- Dramatic emphasis: "CRITICAL", "BREAKING", all-caps
- Over-hedged: "I noticed X -- would it perhaps make sense to consider Y instead?"
- Structured templates in comment body (## Summary, bullet-point verdicts)
- "left a few comments inline" (unnecessary preamble)
- "Nit:" prefix (just state the issue directly)

### Good Examples

**Ultra-short (~50% of comments):**

```
Seems unused.
```

```
ditto
```

```
Is this really needed?
```

**Direct:**

```
This won't work for multimodal models -- `get_text_config()` accesses `text_config` during `super().__init__()`.
```

```
Why not use `field(default_factory=...)` here?
```

**Imperative:**

```
Please fix pre-commit
```

```
Revert changes to this file
```

**Soft opinion (for design):**

```
Tbh I think we can replace this whole block with cached_feature_extractor_from_config.
```

### Follow-Up Replies

When a contributor replies, **always reply back**. Silence is the #1 giveaway of a non-human reviewer.

- Acknowledge: "Makes sense" / "Fixed" / "Done" / "thanks!"
- Concede: "Hmm... that's true, OK then" / "Fair enough"
- Push back: "This is pre-existing behavior" / "We cannot do that because of [link]"
- Self-correct: "Oops, fixed" / "Good catch"

Keep replies to 1 sentence. Never a paragraph.

## Review Submission

Post review with inline comments. The `body` field can be empty string for ~50% of reviews.

```bash
gh api repos/vllm-project/vllm-omni/pulls/<pr_number>/reviews --method POST --input - <<EOF
{
  "commit_id": "<sha>",
  "event": "COMMENT",
  "body": "",
  "comments": [
    {"path": "<file>", "line": <num>, "side": "RIGHT", "body": "<comment>"}
  ]
}
EOF
```

### Inline Comment Line Accuracy

**Comments MUST land on the exact line they discuss.** Off-by-2-5 errors look sloppy.

How to get the correct line number:
1. Fetch the diff: `gh pr diff {N} --repo vllm-project/vllm-omni`
2. Read the hunk header: `@@ -old_start,old_count +new_start,new_count @@`
3. Count from `new_start`: context lines increment both counters, `+` lines increment new only, `-` lines increment old only
4. The `line` parameter = **new-file line number** of the exact line you're commenting on
5. **Verify:** grep the diff for the exact code string and confirm the line number matches

Common mistakes:
- Using diff sequential position instead of new-file line number
- Estimating from nearby code instead of counting exactly
- Commenting about `clamp()` but landing on `offsets =` two lines above

### Review Event

- `COMMENT` for most reviews
- `APPROVE` when code is clean -- use empty body for ~30% of approvals
- `REQUEST_CHANGES` only for genuine blocking bugs (crashes, data loss, security)

---

## Batch and daily review sessions


How to run a review session: select PRs, review them with varied depth, track state, and follow up on replies.

### Daily Review Session

### 1. Check replies first (highest priority)

Before reviewing new PRs, check for unanswered contributor replies:

```bash
./scripts/check_replies.sh --reviewer <your_login> --days 14
```

Reply to each one. Keep replies short:
- "Makes sense" / "Fixed" / "Done" / "thanks!"
- "Hmm... that's true, OK then" / "Fair enough"
- "This is pre-existing behavior"

Silence after engagement is the #1 giveaway of a non-human reviewer.

### 2. Select PRs to review

```bash
./scripts/select_prs.sh --days 7 --limit 5 --reviewer <your_login>
```

This gives you 3-5 PRs prioritized by zero reviews. Adjust `--days` and `--limit` as needed.

Manual filtering -- skip these:
- `[WIP]` / `[Draft]` / `[Don't merge]` in title
- Pure CI config / docs-only changes (unless they're substantial)
- PRs with 3+ existing reviews from maintainers
- Your own PRs

### 3. Review with varied depth

NOT every PR gets the same treatment. Vary intentionally:

| PR Type | Depth | Example |
|---------|-------|---------|
| Obvious small fix | Empty APPROVE | Click approve, no text |
| Clean bug fix | "LGTM" + 0-1 inline | One-liner body, maybe one nit |
| Medium feature | 2-3 inlines, no body | Just the inline comments |
| Large/risky change | 3-5 inlines + short body | "a few questions about X" |
| Copy-paste new model | REQUEST_CHANGES with specifics | Flag missing tests, broken weights |

**Target distribution per session:**
- 1-2 PRs: empty or near-empty APPROVE
- 2-3 PRs: 2-4 inline comments
- 0-1 PRs: 5+ comments (only for genuinely complex changes)

### 4. Post reviews with line verification

Before posting each review, verify line numbers:

```bash
echo "$REVIEW_JSON" | ./scripts/verify_line_numbers.sh <pr_number>
```

This catches off-by-N errors where comments land on the wrong line.

### 5. Log what you reviewed

Keep a simple log for dedup and follow-up tracking:

```
## 2026-04-02
| PR | Author | Comments | Event |
|----|--------|----------|-------|
| #2433 | alex-jw-brooks | 1 | APPROVE |
| #2399 | oscardev256 | 5 | REQUEST_CHANGES |
| #2390 | bjf-frz | 4 | REQUEST_CHANGES |
```

### Pacing Rules

- **Max 3-5 PRs per day.** 34 PRs in 3 days was flagged as suspicious.
- Space reviews out -- not all in one burst.
- Some days, just do reply follow-ups with no new reviews.
- Skip days occasionally -- real reviewers don't review every day.

### Re-Review Protocol

When a contributor pushes new commits or asks for re-review:

1. Check if they addressed your previous comments (read thread replies + new commits)
2. If all resolved: APPROVE. Body: "LGTM" or "looks good now" or empty.
3. If some remain: comment only on unresolved items. Don't re-review from scratch.
4. If new code added: review only the new changes.

Re-reviews should almost always be shorter than the initial review.

### Staleness Rules

- **Contributor stops responding (>7 days):** One ping: "Any updates on this?"
- **PR stale (>14 days):** Move on.
- **PR superseded:** "Looks like this is superseded by #X?"
- **PR closed:** No action.

---

## CI failure and duration triage

### Quick Start

When a user reports CI is **failing (red) / flaky / noticeably slower** and provides logs:

1. Focus only on the **first error** (the earliest fatal signal). Don’t get distracted by cascading follow-up errors.
2. Extract: job name/level, the stage/step where the first error occurs, exit code/exception stack, whether it’s a timeout, and per-stage durations (if available).
3. Classify into one of five categories: **build/install**, **test failure**, **infrastructure**, **timeout/perf regression**, **config/environment**.
4. Provide **1–3** root-cause hypotheses. Each must include an **exact log evidence excerpt**, and hypotheses must be ordered **from lowest verification cost to highest**.
5. Provide a **≤5-minute** minimal verification for **Hypothesis 1** only. Specify **environment + commands + expected result** (must not require running the full pipeline).

### Log-reading guardrail (must follow)

Do **not** triage by reading only the log tail. Many CI logs end with teardown noise, process-kill cascades, or warning lines that are not the first failure.

Required sequence:

1. Fetch the **full raw log** first (or confirm whether the current log view is truncated).
2. Locate pytest failure anchors before reading linearly:
   - `=========== FAILURES ===========`
   - `short test summary info`
   - first `FAILED tests/...` or first `Traceback` with assertion details
3. If you must inspect by line number, jump to the user-provided line and then read **both directions** (at least ±100 lines).
4. Treat warning-only lines (e.g., ffmpeg options, deprecation warnings) as non-fatal unless they are immediately followed by a fatal exit/assertion.
5. Report the **earliest fatal signal** (assertion/exception/exit reason), not the last error-looking line in teardown.

If only a partial/truncated log is available, explicitly state:
- “cannot attribute from current logs: raw log appears partial/truncated”
- and request the raw/full log or the missing window around the first failure block.

### Required inputs (list what’s missing if not provided)

- Job name and type (deploy / L1–L5 / other)
- Logs: **50–100 lines before and after the first error** (or the full log)
- Change: PR link or commit SHA (if unknown, explicitly mark as “unknown”)
- CI environment info (runner/image/Python/CUDA, etc.; cite from logs if present)

### Decision tree (branch on the first error)

- **Build/install failures**
  - Common signals: `SyntaxError`, compiler `error:`, `ld:`/`linker`, `undefined reference`, `CMake Error`, `nvcc fatal`, `ModuleNotFoundError`, `ImportError`, `pip install` failures, `Failed building wheel`, `No matching distribution found`
- **Test failures**
  - Common signals: pytest `FAILED`, `AssertionError`, `E   assert ...`, traceback pointing to a `tests/...` line, or still failing after flaky retries
  - Sub-classify the test failure as one of:
    - **Functional test** (feature behavior, API contract, workflow correctness, edge/error handling)
    - **Performance test** (latency/throughput/runtime/memory regression, perf guardrails)
    - **Accuracy test** (model output quality, numerics, golden outputs, tolerance)
- **Infrastructure issues**
  - Common signals: `Timeout`/`timed out`, `Killed`/`SIGKILL`, `OOM`/`Out of memory`, `No space left on device`, `Disk quota exceeded`, `Connection reset`, `TLS handshake`, `503`/`429`, image pull failures
- **Timeout/performance regressions**
  - Common signals: a stage/step duration increases significantly in logs/summary; approaches timeout threshold; or long periods with no output
- **Configuration/environment issues**
  - Common signals: `Permission denied`, `AccessDenied`, `401/403`, `missing required env`, `KeyError: <ENV>`, secrets/tokens not injected, `could not read credentials`

### Test failure sub-classification: functional vs performance vs accuracy

When classification is **test failure**, you must add a sub-type: **functional**, **performance**, or **accuracy**.

### Functional test

Use **functional** when the first failure is about expected behavior, API contract, control flow, or error handling correctness.

Common signals (look for these near the first error):

- API/contract behavior mismatches: wrong status/code/message, missing keys/fields, schema mismatches
- Workflow/logic mismatches: branch conditions, retries/fallbacks/tool calls, state transitions not matching expected behavior
- Edge/error path checks: invalid input handling, exception type/message mismatch, timeout/error propagation assertion failures
- Integration behavior checks: mocked dependency interactions, call order/count assertions, side-effect checks (file/db/message)

Evidence pattern:

- The failure line typically includes **behavioral assertions** (state/output/exception/call sequence), not metric thresholds.
- The traceback points into tests validating endpoint behavior, pipeline flow, or business logic expectations.

### Accuracy test

Use **accuracy** when the first failure is an assertion about output quality, score, or numeric tolerance.

Common signals (look for these near the first error):

- Golden / expected output mismatches: `expected`, `got`, `mismatch`, `diff`, `golden`, `baseline`, `reference`, `snapshot`
- Numeric tolerance issues: `atol`, `rtol`, `tolerance`, `allclose`, `max_abs_err`, `cosine`, `psnr`, `ssim`
- Quality metric regressions: `accuracy`, `bleu`, `rouge`, `wer`, `cer`, `mAP`, `F1`, `pass@k` (or similar task metrics)
- Determinism drift often shows up as: `seed`, `random`, `nondeterministic`, `torch.backends.cudnn.deterministic`

Evidence pattern:

- The failure line typically includes **an assertion and compared values/metrics**, not runtime thresholds.
- The traceback points into a test that computes a metric or compares outputs against a known-good reference.

### Performance test

Use **performance** when the first failure is a regression check on runtime/throughput/latency/memory, or when the test is explicitly a perf guardrail.

Common signals:

- Runtime thresholds: `took`, `elapsed`, `timeout`, `exceeded`, `slower`, `regression`, `p95`, `p99`, `latency`, `throughput`, `tok/s`, `tokens/s`, `iters/s`, `qps`
- Benchmark-style naming: `benchmark`, `perf`, `performance`, `microbench`, `speed`, `profile`
- Resource guardrails: `peak memory`, `RSS`, `VRAM`, `cuda memory`, `OOM` *inside the test assertion* (not runner OOM)

Evidence pattern:

- The failure line usually includes a **measured value vs threshold/baseline**, e.g. “X is 1.4× slower than baseline” or “p95 latency > limit”.

### Tie-breakers (when logs are ambiguous)

- If the first error references **time/throughput/memory limits**, treat as **performance**.
- If the first error is about **quality scores, numeric tolerance, or golden/reference output**, treat as **accuracy**.
- If the first error is about **API contract, workflow logic, exception handling, or integration behavior**, treat as **functional**.
- If the job fails by **global timeout** (no assertion, runner killed), classify as `timeout/perf regression` (not test failure).

### Output (must use this template)

Rules:

- Hypotheses must be grounded in log facts. If there’s no evidence, write “cannot attribute from current logs” and list what additional info is needed.
- For duration issues, explicitly state: **stage name + baseline vs current run**.
- If there are multiple hypotheses, mark priority (usually ordered by verification cost from low to high).

```markdown
## CI Triage Report

- **Job**: <job name> / <L1|L2|…> / <trigger>
- **Change**: <PR or SHA or unknown>
- **Classification**: <build/install | test failure | infrastructure | config/environment | timeout/perf regression | other>
- **Test sub-type (only if test failure)**: <functional | performance | accuracy | unknown>

### First error

- **Location**: <stage or step name>
- **Excerpt**:
```
<verbatim log lines>
```

### Duration (if relevant)

- **Anomalous stage**: <stage name>
- **Baseline vs current**: <e.g., 2min → 10min> or <multiplier>
- **Notes**: <log-based only: serialized waiting/retries/cache misses, etc.>

### Root-cause hypotheses (ordered by verification priority)

**Hypothesis 1 (verify first)**
- **Description**: <one sentence>
- **Evidence**:
```
<log excerpt>
```

**Hypothesis 2**
- **Description**: …
- **Evidence**: …

(Optional hypothesis 3)

### Minimal verification plan (for Hypothesis 1)

- **Environment**: <local / specific container image / minimal CI workflow name>
- **Steps**:
  1. `<command or action A>`
  2. `<command or action B>`
- **Expected result**: <success | reproduce an error | duration within a range>

### Recommended actions

- If verification **confirms**: <fix direction or recommend reverting the change>
- If verification **does not confirm**: <move to next hypothesis or expand logs/contact infra>
- If it’s **infra/environment**: <adjust parallelism/timeouts/resources or include key points for an ops ticket>
```

### Linking CI failures to a specific change

When you triage a CI failure from Buildkite (for example
`https://buildkite.com/...`), you should
always first identify **which change** the build is running:

- **Branch / commit**: at the top of the Buildkite job page you will see something like
  `Example:main / xxxx (#xxxx)`.
  - `Example:main` is the branch.
  - `xxxx` is the short commit SHA.
  - `#xxxx` is the PR number.
- Use these links to decide whether the failure is:
  - **Change-induced**: the failure only appears on this PR/commit, and does not
    reproduce on the current `main` (or the base branch).
  - **Pre‑existing or infra**: the same job is already red/flaky on `main` or on
    unrelated PRs.

Recommended checks:

1. Open the **commit link** and quickly scan the diff for files directly related to the
   failing job (e.g., TTS tests vs. engine code).
2. Open the **PR link** to see title, description, and any explicit claims (perf,
   correctness, infra, etc.).
3. Optionally compare with a recent **green run on `main`** for the same job to see
   whether the failure pattern is new.

When you fill in the triage template above, use:

- `Change`: set to the PR or full SHA (e.g. `#xxxx / xxxx`).
- In **Recommended actions**, explicitly say whether the evidence points to “regression
  introduced by this PR/commit” vs. “likely pre‑existing / infra issue”.

### Additional resources

- L1–L5 levels and directory conventions: `https://github.com/vllm-project/vllm-omni/blob/main/docs/contributing/ci/CI_5levels.md`


---

## Python style (review flags)

*This section replaces the former standalone `python-style-guide.md` — use it for consistent style nits (imports, naming, bare `except`, etc.).*

Key rules to check when reviewing Python code in vLLM-OMNI. Based on Google Python Style Guide.

### Imports
- Group order: `__future__` > stdlib > third-party > repo sub-packages
- Sort lexicographically within groups
- Use `import x` for packages/modules, `from x import y` for specific names
- No relative imports; use full package paths
- Never `import x, y` on one line

### Naming
- Modules/packages: `lower_with_under`
- Classes/Exceptions: `CapWords`
- Functions/methods/variables: `lower_with_under`
- Constants: `CAPS_WITH_UNDER`
- No type info in variable names (no `id_to_name_dict`)

### Formatting
- Max line length: 80 chars (exceptions: imports, URLs)
- 4 spaces indent, never tabs
- Use implicit line joining inside `()`, `[]`, `{}`
- Trailing commas when closing bracket is on separate line

### Common Review Flags
- `import math` inside function body -- "Move imports to the top"
- Imports not in alphabetical order -- "Please keep in alphabetical order"
- Mutable default arguments (`def f(x=[])`) -- always flag
- Bare `except:` or `except Exception: pass` -- always flag
- `logger.info(f"...")` -- should use `logger.info("...: %s", val)` for lazy formatting
- `+=` in loops for string concat -- use `''.join()` or `io.StringIO`
- `if len(seq):` -- should be `if seq:`
- `if x == None:` -- should be `if x is None:`

---

## Specialized Verification References

For PRs that require deeper automated verification beyond the standard blocker scan and evidence request:

- **Perf/Accuracy claim verification:** [perf-verification.md](perf-verification.md) — Detects quantitative claims in PR body, checks hardware feasibility, runs before/after benchmarks via git worktrees, produces Claimed vs Measured comparison. Graceful degradation to static-only when hardware is insufficient. Used in Step 6 of the main workflow.

- **Test quality evaluation:** [test-quality-evaluation.md](test-quality-evaluation.md) — Evaluates test assertion quality, anti-patterns, marker compliance, and edge case coverage. Runs affected tests with hardware-aware filtering. Produces internal quality assessment (not posted to PR). Used in Step 7 of the main workflow.
