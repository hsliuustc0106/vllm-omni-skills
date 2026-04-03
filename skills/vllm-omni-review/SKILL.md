---
name: vllm-omni-review
description: Review PRs on vllm-project/vllm-omni by routing to the right domain skills, checking critical evidence, and focusing comments on blocking issues. Use when reviewing pull requests, triaging review depth, or checking tests, benchmarks, and breaking changes in vllm-omni.
---

# vLLM-Omni PR Review

## Overview

Review PRs like a real maintainer — direct, selective, and focused on high-signal issues. Prioritize 2-3 real problems per PR over exhaustive coverage. Most PRs should get 1-5 short comments; some just get an empty APPROVE.

Use this skill as a router for `vllm-project/vllm-omni` pull request reviews. Keep the default context small, load only the references that match the diff, and prioritize high-confidence findings over coverage theater.

## Priority Hierarchy Under Context Pressure

If context is limited, prioritize: blocker scan → evidence → domain routing → verdict.

Always run the blocker scan. Under context pressure, do a shallow scan of the most critical categories (Correctness, Security) and flag that the scan was incomplete.

## Core Workflow

### Step 0: Verify Review Gates First

Check mergeability and required checks (DCO, pre-commit, mergeability). If failing, stop and ask the author to fix gates before proceeding.

For gate commands, review submission, and comment style, see [references/review-execution.md](references/review-execution.md).

### Step 0.5: Check PR Size for Large Changes

For substantial changes (more than 1000 LOC OR more than 10 files changed):
- Ask the contributor to run L3 tests locally and paste results in PR description (highly recommended)

Example:
> This PR is substantial (>1000 LOC / >10 files). Could you please run the [L3 tests](https://docs.vllm.ai/projects/vllm-omni/en/latest/contributing/ci/test_guide/#l3-level--l4-level) locally and paste the results here?

Then continue with the workflow below.

### Step 1: Gather Minimal Context

Fetch:
- PR metadata and changed files
- The diff
- Linked issues for `[Bugfix]` and `[Feature]` PRs only when conventions are unclear
- Related PRs only when conventions or prior decisions are unclear

Do not fetch broad extra context unless the diff leaves real ambiguity.

### Step 2: Blocker Scan (Required First)

Execute this scan before any other review activity. For each category, explicitly mark PASS or list blocking issues found.

```
BLOCKER scan:
| Category            | Result                                  |
|---------------------|-----------------------------------------|
| Correctness         | PASS / ISSUES: (list)                   |
| Reliability/Safety  | PASS / ISSUES: (list)                   |
| Breaking Changes    | PASS / (check PR description first)     |
| Test Coverage       | PASS / (check PR desc for evidence) / needs tests |
| Documentation       | PASS / ISSUES: (list)                   |
| Security            | PASS / ISSUES: (list)                   |
```

**Blocker categories:**

| Category | Flag These Patterns |
|----------|---------------------|
| **Correctness** | Silent exception swallows, uninitialized variables, off-by-one errors, logic inversions, missing returns |
| **Reliability/Safety** | Unclosed resources, race conditions, missing None checks, hardcoded timeouts, silent fallbacks |
| **Breaking Changes** | Signature changes without compat, removed public APIs, changed defaults, config removals |
| **Test Coverage** | Bug fix without regression test, new API without tests, performance claims without benchmarks |
| **Documentation** | New public API without docs, breaking changes without migration guide, new config without docs |
| **Security** | Hardcoded secrets, user input in eval/format strings, insecure deserialization |

**Evidence standard:** Code inspection suffices for code-level blockers. For test coverage, require CI logs or PR description evidence.

**Confidence threshold:** Flag obvious cases only. For suspicious but uncertain cases, add a non-blocking comment.

**Special cases:**
| PR Type | Action |
|---------|--------|
| Doc-only PRs | Skip categories 1-4 and 6, proceed to 5 (Documentation) |
| Config-only PRs | Focus on Breaking Changes + Documentation |
| Test-only PRs | Focus on Correctness of test logic |
| Draft PRs | Do not block; add a single non-blocking comment: "Ready for full review when draft status removed. Preliminary scan available on request." |

For detailed anti-patterns with code examples, see [references/blocker-patterns.md](references/blocker-patterns.md).

**If blockers found:**
```
BLOCKING ISSUES:
1. [Category] [Line/File] - [description]
2. ...
VERDICT: REQUEST_CHANGES (cannot approve until blockers resolved)
```

**If no blockers:**
List non-blocking suggestions and proceed to Step 3.

### Step 3: Route to the Right Skill

Use the title prefix and changed directories to decide whether a domain skill is required.

| Signal                                      | Action                       |
| ------------------------------------------- | ---------------------------- |
| `[Image]`, `[ImageGen]`                     | Use `vllm-omni-image-gen`    |
| `[Video]`, `[VideoGen]`                     | Use `vllm-omni-video-gen`    |
| `[Audio]`, `[TTS]`                          | Use `vllm-omni-audio-tts`    |
| `[Multimodal]`                              | Use `vllm-omni-multimodal`   |
| `[Distributed]`                             | Use `vllm-omni-distributed`  |
| `[Quantization]`                            | Use `vllm-omni-quantization` |
| `[Performance]`                             | Use `vllm-omni-perf`         |
| `[Hardware]` or backend-specific code       | Use `vllm-omni-hardware`     |
| `[API]` or `vllm_omni/entrypoints/` changes | Use `vllm-omni-api`          |
| `[CI]`                                      | Use `vllm-omni-cicd`         |
| `[Model]`                                   | Use `vllm-omni-contrib`      |

For multi-skill routing and hardware detection, see [references/review-routing.md](references/review-routing.md).

### Step 4: Load Only the Relevant Review Reference

Load targeted references based on the diff:

| Diff Area                                                                                 | Load                                                       |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `vllm_omni/engine/`, `vllm_omni/stages/`, `vllm_omni/connectors/`, `vllm_omni/diffusion/` | [references/pitfalls.md](references/pitfalls.md)           |
| Async, distributed coordination, validation, connector behavior                           | [references/code-patterns.md](references/code-patterns.md) |
| Scheduler, stage boundaries, execution model, critical paths                              | [references/architecture.md](references/architecture.md)   |
| High-risk changes (core logic, configs/params, error handling, concurrency/distributed, I/O) or `[Feature]` / `[Bugfix]` PRs | [references/tests-docs-checklist.md](references/tests-docs-checklist.md) |

Avoid loading all three by default.

### Step 5: Ask for Concrete Validation Evidence

When tests or benchmarks are missing **and PR description evidence is insufficient**, ask for specific evidence:

| Change Type | Minimum Evidence to Request |
|-------------|-----------------------------|
| API behavior | Functional tests covering success + invalid input + response contract |
| Model execution | Inference correctness tests comparing outputs against baseline |
| Performance optimization | Benchmark showing before/after latency on stated hardware |
| New feature (performance-affecting) | Performance comparison test: baseline vs. with change (latency, throughput, VRAM) |
| Memory management | Peak memory measurement showing no regression |
| Bug fixes | Regression test that reproduces the original bug |

For `[Feature]` PRs affecting performance or `[Performance]` PRs, use the checklist in [references/tests-docs-checklist.md](references/tests-docs-checklist.md) section 5.

Be explicit in review comments. Treat "manual verification only" as insufficient unless automation is genuinely impossible.

### Step 6: Final Verdict

Use the review body to summarize:
- What was validated
- What still lacks evidence

**Verdict:** Use the review event directly — no formatted verdict block in the body.

- `APPROVE` — code is clean. Body can be empty, "LGTM", or "Thanks".
- `COMMENT` — has suggestions but nothing blocking. Body optional (~50% should be empty).
- `REQUEST_CHANGES` — genuine blocking bugs only (crashes, data loss, security).

Do NOT use structured verdict templates — real maintainers never do this. For tone calibration and comment style, see [references/review-execution.md](references/review-execution.md). For calibration data, see [references/maintainer-style-study.md](references/maintainer-style-study.md).


## Review Heuristics

- Check PR description evidence before requesting tests
- Only flag missing tests when evidence is genuinely absent
- For [Bugfix] PRs, require a regression test unless automation is impossible
- For API-facing PRs, prefer contract tests over broad smoke tests
- Be suspicious of silent fallbacks, swallowed exceptions, device-specific assumptions
- Review critical paths first: engine, connectors, stages, API entrypoints
- Skip nits and style comments unless they hide a correctness issue

## Scenario Coverage

| Scenario | Blocker Scan | Domain Routing | Verdict |
|----------|--------------|----------------|---------|
| Standard code PR | Full 6-category scan | Route by prefix/diff | Standard format |
| Doc-only PR | Skip to Documentation only | Skip | Standard format |
| Config-only PR | Breaking Changes + Documentation | Skip | Standard format |
| Test-only PR | Correctness of test logic | Skip | Standard format |
| Draft PR | Run scan (non-blocking); offer preliminary feedback on request | Skip | COMMENT: "Ready for full review when draft removed" |
| Large PR (>1000 LOC) | Shallow scan + request L3 tests | Route by prefix/diff | Standard format |

## When to Fetch More Context

Fetch more context when:
- The diff snippet hides lifecycle or cleanup behavior
- A config key or API field is introduced without nearby validation
- A benchmark claim references unseen measurement code
- The PR appears to rely on prior design discussion

Keep additional fetches narrow and tied to a specific uncertainty.

## Diffusion Model PR Review

> **Invoked when PR prefix is `[Model]`, `[New Model]`, `[Image]`, `[ImageGen]`, `[Video]`, `[VideoGen]`, or `[Diffusion]`.**

All four dimensions below must pass before approving. Work through them in priority order. See [references/diffusion-checklist.md](references/diffusion-checklist.md) for full per-item criteria across all dimensions.

### Priority Order

1. **PR body evidence** — missing samples/metrics block the entire review
2. **Missing inference mode** — model must work offline and online
3. **Missing acceleration feature** — required for all new diffusion models
4. **Missing memory optimization** — required for all new diffusion models
5. **Missing documentation** — tables and examples must be updated
6. **Missing e2e test** — required for merge gate
7. **Missing offline inference test** — recommended; required only when no e2e test is present
8. **Combined feature test** — required when two or more acceleration/memory features are implemented

---

### Dimension 1: PR Body Completeness

Required: generation script, sample outputs, e2e latency, peak VRAM. Recommended: matching diffusers baseline for all four.

**Comment when required items are missing:**

```
🔴 **PR Body Incomplete — Required Evidence Missing**

The following items are required before this PR can be reviewed:

- [ ] vLLM-Omni generation script (offline `Omni` or online `vllm serve`)
- [ ] Generated sample output (image / video / audio)
- [ ] vLLM-Omni e2e latency (hardware: GPU model, count; resolution; steps)
- [ ] vLLM-Omni peak VRAM usage (GB)

Please update the PR description with this information.
```

**Comment when diffusers baseline is absent:**

```
💡 **Recommended: diffusers Baseline Comparison**

Adding a diffusers comparison would strengthen this PR:

- diffusers generation script (same prompt, same resolution/steps)
- diffusers sample output
- diffusers e2e latency vs vLLM-Omni latency
- diffusers peak VRAM vs vLLM-Omni VRAM
```

---

### Dimension 2: Code Review

```bash
# Detect leftover diffusers mixins
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep '^\+' | grep -E 'DiffusionPipelineMixin|SchedulerMixin|ConfigMixin'

# Check acceleration features
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -iE 'sequence_parallel|cfg_parallel|vae_patch_parallel|tensor_parallel|teacache|cache_dit'

# Check memory optimizations
gh pr diff <pr_number> --repo vllm-project/vllm-omni \
  | grep -iE 'cpu_offload|offload_to_cpu|quantization|int8|fp8|bitsandbytes|vae_tiling'
```

**2.1 Inference modes** — both offline (`Omni`) and online (`vllm serve` / `AsyncOmni`) must be implemented.

```
🔴 Missing <offline inference / online serving> support. The model must work in both
Omni (offline) and vllm serve / AsyncOmni (online) modes before merging.
```

**2.2 Diffusers mixin cleanup** — flag any mixin still present in `+` lines.

```
🔴 Leftover diffusers mixin detected: `<MixinName>` in `<file>:<line>`.
Remove diffusers mixins and use vLLM-Omni's native abstractions instead.
```

**2.3 Acceleration features** — at least one of: sequence parallel, CFG parallel, VAE patch parallel, tensor parallel, TeaCache/step cache.

```
🔴 No acceleration feature detected. The model must support at least one of:
sequence parallel, CFG parallel, VAE patch parallel, tensor parallel, or step caching (TeaCache).
```

**2.4 Memory optimization** — at least one of: CPU offload, quantization (int8/fp8/bnb), VAE tiling.

```
🔴 No memory optimization feature detected. The model must support at least one of:
CPU offload (`--cpu-offload-gb`), quantization (int8/fp8/bnb), or VAE tiling.
```

---

### Dimension 3: Documentation

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni \
  --json files --jq '.files[].path' | grep -E 'docs/|\.md$'
```

Required: model support table, feature support table, usage example doc (offline + online).

```
🔴 Documentation incomplete:
- [ ] Model support table not updated (docs/models/supported_models.md or equivalent)
- [ ] Feature support table not updated
- [ ] Usage example doc missing or not updated for <ModelName>
```

---

### Dimension 4: Test Coverage

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni \
  --json files --jq '.files[].path' | grep -E '^tests/'
```

Required: e2e online serving test. Recommended: offline inference test. Required when 2+ features: combined feature test.

```
🔴 Missing e2e online serving test in `tests/e2e/online_serving/`.
Please add a test that:
1. Starts `vllm serve <model> --omni`
2. Sends a generation request via the API
3. Asserts the response contains a valid image / video / audio output
```

```
⚠️ Multiple features are implemented (e.g., <feature A> + <feature B>) but no combined
feature test is present. Please add a test (or extend the e2e test) that enables both
features together and asserts output validity + reports latency + VRAM.
```

> See [Diffusion Checklist](references/diffusion-checklist.md) for full per-item criteria and the Quick Red Flags summary.

---

## Batch Review Session

For daily review sessions, use the scripts and workflow in [references/batch-review-workflow.md](references/batch-review-workflow.md):

1. **Check replies first:** `./scripts/check_replies.sh --reviewer <login>` — respond to unanswered threads
2. **Select PRs:** `./scripts/select_prs.sh --days 7 --limit 5 --reviewer <login>` — pick 3-5 reviewable PRs
3. **Review with varied depth:** some empty APPROVE, some 2-3 inlines, rarely 5+
4. **Verify line numbers:** `echo "$JSON" | ./scripts/verify_line_numbers.sh <pr>` — catch off-by-N errors
5. **Log reviews** for dedup and follow-up tracking

## References

- [Review Execution](references/review-execution.md) - Gate checks, commands, comment budget, tone calibration, line accuracy
- [Maintainer Style Study](references/maintainer-style-study.md) - Raw data from 200 DarkLight1337 reviews + 12 other maintainers
- [Batch Review Workflow](references/batch-review-workflow.md) - Daily session workflow, pacing rules, re-review protocol
- [Python Style Guide](references/python-style-guide.md) - Common style flags for Python code review
- [Blocker Patterns](references/blocker-patterns.md) - Anti-patterns that block approval with code examples
- [Review Routing](references/review-routing.md) - Prefix mapping, multi-skill routing, hardware detection
- [Common Pitfalls](references/pitfalls.md) - MRO issues, connector state, async differences
- [Architecture](references/architecture.md) - System overview and critical paths
- [Code Patterns](references/code-patterns.md) - Async, distributed, cache, validation, error handling patterns
- [Diffusion PR Requirements](references/diffusion-pr-requirements.md) - PR body requirements for diffusion model contributions
