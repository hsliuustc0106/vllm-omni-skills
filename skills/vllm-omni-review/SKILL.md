---
name: vllm-omni-review
description: Review PRs on vllm-project/vllm-omni by routing to the right domain skills, checking critical evidence, and focusing comments on blocking issues. Use when reviewing pull requests, triaging review depth, or checking tests, benchmarks, and breaking changes in vllm-omni.
---

# vLLM-Omni PR Review

## Overview

Use this skill as a router for `vllm-project/vllm-omni` pull request reviews. Keep the default context small, load only the references that match the diff, and prioritize high-confidence findings over coverage theater.

## Reviewer Posture

You are an **adversarial reviewer**. Your job is to find what will break in production.

- Absence of evidence IS evidence of absence
- Assume the PR is broken until proven otherwise
- Only APPROVE when all blockers are resolved
- Use REQUEST_CHANGES for any unresolved blocker
- COMMENT is reserved for non-blocking suggestions only

Default review priorities:

1. Missing regression or integration tests
2. Claims without evidence
3. Security or reliability regressions
4. Breaking API or behavior changes
5. Architecture flaws in critical paths

## Core Workflow

### Step 0: Verify Review Gates First

Check mergeability and required checks before reading the diff in depth. If DCO, pre-commit, or mergeability is failing, stop and ask the author to fix the gate before doing a full review.

For concrete gate commands, review submission commands, and comment style, see [references/review-execution.md](references/review-execution.md).

### Step 0.5: Check PR Size for Large Changes

For large PRs that exceed either threshold:
- **More than 1000 lines of code changed**, OR
- **More than 10 files changed**

Ask the contributor to run L3 tests locally and paste the test results in the PR (highly recommended). This helps ensure comprehensive validation for substantial changes before investing review effort.

For test level definitions and commands, see the [L3/L4 test guide](https://docs.vllm.ai/projects/vllm-omni/en/latest/contributing/ci/test_guide/#l3-level--l4-level).

Example request:
> This PR is substantial (>1000 LOC / >10 files). Could you please run the [L3 tests](https://docs.vllm.ai/projects/vllm-omni/en/latest/contributing/ci/test_guide/#l3-level--l4-level) locally and paste the results here? This helps validate the change across broader scenarios before we proceed with the detailed review.

### Step 1: Gather Minimal Context

Fetch:

- PR metadata and changed files
- The diff
- Linked issues for `[Bugfix]` and `[Feature]` PRs
- Related PRs only when conventions or prior decisions are unclear

Do not fetch broad extra context unless the diff or linked issue leaves real ambiguity.

### Step 2: Route to the Right Skill

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

If the PR spans multiple specialized areas, choose the primary skill first and load a secondary skill only when the diff crosses a real subsystem boundary.

For multi-skill routing, hardware detection, and delegation rules, see [references/review-routing.md](references/review-routing.md).

### Step 3: Load Only the Relevant Review References (and Required Outputs)

Load targeted references based on the diff:

| Diff Area                                                                                 | Load                                                       |
| ----------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `vllm_omni/engine/`, `vllm_omni/stages/`, `vllm_omni/connectors/`, `vllm_omni/diffusion/` | [references/pitfalls.md](references/pitfalls.md)           |
| Async, distributed coordination, validation, connector behavior                           | [references/code-patterns.md](references/code-patterns.md) |
| Scheduler, stage boundaries, execution model, critical paths                              | [references/architecture.md](references/architecture.md)   |
| High-risk changes (core logic, configs/params, error handling, concurrency/distributed, I/O) or `[Feature]` / `[Bugfix]` PRs | [references/tests-docs-checklist.md](references/tests-docs-checklist.md) |

Avoid loading all three by default. Start with the one that matches the changed files or the most likely failure mode.

If the tests/docs addendum is triggered, include in the review body:

- A **coverage matrix** (change point → existing tests → gap → minimal add)
- A **review addendum snippet** (environment + runtime estimate + short fill-in template)

### Step 4: Run the Critical Checks

**First, check the PR description for evidence.** Many PRs include comprehensive testing evidence directly in their description. Before requesting additional tests, verify whether the PR already provides:

| Evidence Type | Valid Forms in PR Description |
|---------------|------------------------------|
| **Inference correctness** | E2E generation results, visual outputs (images/videos), output shape verification |
| **Quality metrics** | LPIPS, FID, CLIP scores comparing quantized vs baseline |
| **Performance claims** | Benchmark tables with timing, speedup percentages, memory reduction |
| **Memory profiling** | Weights/activations/peak breakdown, TP scaling data |
| **Regression tests** | Test commands with [x] checkmarks showing they were run successfully |

**Only request additional tests if evidence is genuinely missing or insufficient.**

Then apply these checks:

- Is there a regression test for bug fixes? (Check PR description first!)
- Do new features include tests and docs where needed? (PR description evidence counts!)
- Are performance claims backed by benchmark data? (Look for tables in PR body)
- Are API or config changes validated early and documented?
- Does the change preserve cleanup, state transitions, and distributed invariants?
- **Does the PR introduce new environment variables?** If so, ask the contributor to explain:
  - Why this environment variable is necessary (what problem does it solve?)
  - Whether there are alternatives (config file, CLI flag, API parameter) that could avoid runtime environment dependencies
  - Environment variables should be a last resort for configuration that cannot be achieved through other means

If a finding is speculative, do not comment. Fetch a bit more code context first or drop it.

### Step 4.5: Mandatory Blocker Triage

Before writing any review output, complete this triage:

| Category | Status | Evidence/Gap |
|----------|--------|--------------|
| Tests    | PASS/FAIL/NA | <evidence or what's missing> |
| Docs     | PASS/FAIL/NA | <evidence or what's missing> |
| Perf     | PASS/FAIL/NA | <evidence or what's missing> |
| Accuracy | PASS/FAIL/NA | <evidence or what's missing> |
| API      | PASS/FAIL/NA | <evidence or what's missing> |

**Any FAIL = REQUEST_CHANGES (non-negotiable)**

Triage criteria:
- Tests: Regression test for bugfix? Coverage for new code? Evidence in PR description?
- Docs: Examples updated? API changes documented? README synced?
- Perf: Benchmark data for optimization claims? Memory regression check?
- Accuracy: Quality metrics (FID/LPIPS) for generative models? Output verification?
- API: Contract tests for endpoint changes? Backward compatibility verified?

### Step 4.6: Ask for Concrete Validation Evidence

When tests or benchmarks are missing **and PR description evidence is insufficient**, ask for the specific evidence needed for the changed area instead of a generic "please add tests" comment.

Required evidence by change type:

| Change Type | Minimum Evidence to Request |
|-------------|-----------------------------|
| API behavior, request parsing, response schema, streaming, modality I/O | Functional API tests covering success path, invalid input, and response contract |
| Model execution logic, kernels, sampling, connector/stage behavior | Inference correctness tests that compare outputs, shapes, tokens, or modality payloads against an expected result or trusted baseline |
| Performance optimization, scheduling, caching, parallelism, quantization, serving throughput | Performance regression benchmark showing before/after latency or throughput on stated hardware |
| Memory management, offloading, large-model support, batching changes | Peak memory measurement showing the change does not regress VRAM/RAM usage beyond the claimed budget |
| Bug fixes | A regression test that reproduces the original bug and fails without the fix |

Be explicit in review comments:

- For API changes, ask for tests that exercise both valid and invalid requests and verify the response contract.
- For inference changes, ask for accuracy or correctness checks, not only smoke tests.
- For performance claims, ask for benchmark scripts, commands, hardware details, and before/after numbers.
- For memory claims, ask for peak memory numbers and the measurement method.
- For bug fixes, treat "manual verification only" as insufficient unless the bug cannot be automated and the reason is explained.

### Step 5: Make the Review Decision

Use the triage results to determine the review action:

| Triage Result | Action |
|---------------|--------|
| All PASS or NA | APPROVE |
| Any FAIL, fixable | REQUEST_CHANGES |
| Any FAIL, unclear fix | REQUEST_CHANGES + clarifying questions |

**Never use COMMENT for blockers.** COMMENT is for non-blocking polish only.

### Step 6: Keep the Output Tight

Comment only on blocking or high-value issues. Combine related problems into a single comment when possible, and avoid praise-only or low-signal remarks. Small documentation-only PRs often need no inline comments.

**Comment Format (Haiku Mode):**

Every inline comment follows this template:

`[CATEGORY] [STATUS]: <problem in 10 words> | <what's required>`

Examples:
- `[TESTS] FAIL: No regression test | Add test that reproduces original bug`
- `[PERF] FAIL: No benchmark data | Include before/after latency numbers`
- `[DOCS] FAIL: API change undocumented | Document new parameter in docs/`
- `[ACCURACY] FAIL: No quality metrics | Include FID/LPIPS comparison vs baseline`

Use the review body to summarize:

- Triage table (categories with PASS/FAIL/NA)
- What still lacks evidence
- What must change before approval

For comment budget, phrasing, examples, and posting mechanics, see [references/review-execution.md](references/review-execution.md).

## Review Heuristics

- **PR description evidence satisfies triage** — don't re-request.
- Any gap in triage = FAIL (no partial credit).
- "Manual verification" for bugfix = FAIL unless automation is impossible AND the reason is explained.
- Performance claim without numbers = FAIL.
- New API without contract test = FAIL.
- Skip all non-blockers (style, nits, polish).
- Be suspicious of silent fallbacks, swallowed exceptions, and device-specific assumptions.
- Review critical paths first: engine, model executor, connectors, stages, and API entrypoints.

## When to Fetch More Context

Fetch more code or issue context when:

- the diff snippet hides lifecycle or cleanup behavior
- a config key or API field is introduced without nearby validation
- a benchmark or quality claim references unseen measurement code
- the PR appears to rely on prior design discussion

Keep additional fetches narrow and tied to a specific uncertainty.

## References

- [Review Routing](references/review-routing.md) - prefix mapping, multi-skill routing, hardware detection, delegation
- [Review Execution](references/review-execution.md) - gate checks, commands, comment budget, review phrasing
- [Common Pitfalls](references/pitfalls.md) - MRO issues, connector state, async differences, validation gaps
- [Architecture](references/architecture.md) - system overview and critical paths
- [Code Patterns](references/code-patterns.md) - async, distributed, cache, validation, and error handling patterns
