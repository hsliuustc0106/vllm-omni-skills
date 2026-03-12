---
name: vllm-omni-review
description: Use when reviewing PRs on vllm-project/vllm-omni. Produces finding-driven reviews by combining domain skills with explicit checks for regressions, weak tests, and unsupported claims.
---

# vLLM-Omni PR Review

## Overview

Review pull requests for [vLLM-Omni](https://github.com/vllm-project/vllm-omni) by leveraging domain-specific skills. Focus on critical issues: missing tests, unvalidated claims, security, design flaws, and breaking changes.

## Review Posture

- Assume the diff hides at least one regression until the code, tests, and context disprove it.
- Spend **zero** review budget on praise, summaries, or intent restatement.
- Prefer one concrete blocker over five vague suggestions.
- If you cannot name the failure mode, missing evidence, or missing test, the comment is probably not ready.
- Approval means "no actionable findings found," not "the implementation is excellent."

## Review Layers

This skill orchestrates multiple review capabilities:

| Layer | Capability | Source | Trigger |
|-------|------------|--------|---------|
| 1. Gates | CI status, mergeability | Built-in | Always |
| 2. Context | Linked issues, related PRs | Built-in | Always |
| 3. Domain | ML/inference expertise | Domain skills | PR prefix match |
| 4. Pitfalls | vLLM-Omni specific bugs | This skill | Always |
| 5. General | Security, performance | `code-reviewer` agent | Non-domain code |
| 6. Deep dive | Error handling, types, tests | Specialized agents | Trigger conditions |

## Review Constraints

| Constraint | Value |
|------------|-------|
| Max inline comments | 5 per PR |
| Comment length | 2-4 sentences each |
| Small doc fix | 0 comments expected |
| Large feature | 3-5 comments on critical gaps |
| Praise budget | 0 lines |

### Banned Phrases (Generic Praise)

- "solid", "generally", "looks good", "well done", "nice work", "great job"
- "comprehensive", "well structured", "good implementation"
- Any phrase without specific code location reference

### Finding Bar

Only post a comment when it includes all of the following:

1. A concrete defect, risk, or evidence gap tied to a specific file, line, or behavior change
2. Why it matters: crash, hang, silent corruption, wrong output, compatibility break, or unverifiable claim
3. A concrete ask: fix, regression test, benchmark, or validation change

Reject comments that only paraphrase the diff, say "add tests" without naming the missing scenario, speculate without a trigger condition, or soften the finding with praise.

## Review Workflow

### Step 0: Verify CI Gate (REQUIRED FIRST)

**Check these BEFORE reviewing code. If any fail, post a gate-failure comment and STOP.**

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni --json mergeable,statusCheckRollup --jq '{mergeable, checks: [.statusCheckRollup[] | {name, conclusion}]}'
```

| Check | Passing State | Action if Failed |
|-------|---------------|------------------|
| DCO | `SUCCESS` | Comment "DCO check failed. Please sign your commits with `git commit -s`." |
| pre-commit | `SUCCESS` | Comment "Pre-commit checks failed. Run `pre-commit run --all-files` and fix issues." |
| mergeable | `MERGEABLE` | Comment "Merge conflicts detected. Please rebase onto main and resolve conflicts." |

**Gate failure comment template:**
```
🚫 **Review Blocked: CI Gate Failed**

- [ ] DCO: <status>
- [ ] Pre-commit: <status>
- [ ] Merge conflicts: <status>

Please resolve these issues before review proceeds.
```

**Only proceed to Step 1 when all gates pass.**

### Step 1: Fetch PR Data

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni --json title,body,author,state,files,closingIssuesReferences
gh pr diff <pr_number> --repo vllm-project/vllm-omni
```

### Step 1.5: Fetch Linked Context (Issues & Related PRs)

**Fetch linked issues for context:**

```bash
# Get closing issues referenced in PR body (Fixes #123, Closes #456, etc.)
gh pr view <pr_number> --repo vllm-project/vllm-omni --json closingIssuesReferences --jq '.closingIssuesReferences[] | {number, title, body}'

# For each linked issue, get full details
gh issue view <issue_number> --repo vllm-project/vllm-omni --json title,body,labels,state,comments
```

**Fetch related PRs touching the same files:**

```bash
# Get list of changed files from PR
gh pr view <pr_number> --repo vllm-project/vllm-omni --json files --jq '.files[].path'

# For each significant file, find other open/recent PRs
gh search prs --repo vllm-project/vllm-omni "<file_path>" --merged --limit 5 --json number,title,author,closedAt
```

**What linked context provides:**

| Context Type | Value for Review |
|--------------|------------------|
| **Linked Issues** | Original bug description, acceptance criteria, design decisions |
| **Related Merged PRs** | Patterns to follow, prior solutions, area-specific conventions |
| **Issue Labels** | Priority (P0/P1), area owners, breaking change flags |
| **Issue Comments** | Prior discussions, rejected approaches, constraints |

**When linked context is critical:**

- `[Bugfix]` PRs → **Always fetch linked issue** for bug reproduction steps
- `[Feature]` PRs → **Always fetch linked issue** for acceptance criteria
- Complex multi-file changes → **Check related PRs** for area conventions
- Changes to shared infrastructure → **Check related PRs** for coordination needs

**Limits:** 2-3 linked issues max, 5 related PRs per file max

### Step 1.8: Generate Failure Hypotheses

Before invoking skills or agents, write down **3 likely failure modes** for this PR. If you cannot produce 3, the review is still too shallow.

| Change Shape | Failure Hypothesis to Test |
|--------------|----------------------------|
| New default, config, or optional arg | Existing callers now get different behavior |
| Reordered async, stage, or connector code | Race, deadlock, cancellation leak, or cleanup drift |
| Added cache, memoization, or mutable state | Cross-request contamination or stale data |
| Validation or parsing changes | Invalid requests now reach the engine, or valid requests are rejected |
| `[Refactor]` with "no behavior change" claim | Exception type, return shape, logging, or side-effect order changed |

Use these hypotheses to decide where to fetch context and which references to consult.

### Step 2: Identify PR Type & Trigger Skill

Check PR title prefix against the table below. If domain-specific context is needed, invoke the corresponding skill.

| PR Prefix | Trigger Skill | Key Focus |
|-----------|---------------|-----------|
| `[Image]`, `[ImageGen]` | `vllm-omni-image-gen` | Generation quality, memory |
| `[Video]`, `[VideoGen]` | `vllm-omni-video-gen` | Temporal consistency, VRAM |
| `[Audio]`, `[TTS]` | `vllm-omni-audio-tts` | Audio quality, latency |
| `[Multimodal]` | `vllm-omni-multimodal` | Cross-modal alignment |
| `[Distributed]` | `vllm-omni-distributed` | Scaling, disaggregation |
| `[Quantization]` | `vllm-omni-quantization` | Accuracy loss, compatibility |
| `[Performance]` | `vllm-omni-perf` | Benchmarks, claims validation |
| `[Hardware]` | `vllm-omni-hardware` | Backend compatibility |
| `[API]` | `vllm-omni-api` | OpenAI compat, input validation |
| `[CI]` | `vllm-omni-cicd` | Pipeline correctness |
| `[Model]` | `vllm-omni-contrib` | Integration patterns |
| `[Bugfix]` | — | Regression test required |
| `[Refactor]` | — | No behavior change |
| `[Feature]` | — | Tests + docs required |

**When to invoke skill:**
- Diff content is unclear without domain context
- Domain-specific validation needed (e.g., model architecture, API contract)
- Performance claims need verification
- **Change affects a specialized subsystem** (CPU offloading, tensor parallelism, diffusion sampling, quantization methods)
- **Even if PR provides benchmark data**, invoke skill when the change is in a specialized area

**When NOT to invoke:**
- Simple refactors with clear intent
- Documentation-only changes
- Already have sufficient context from diff
- PR touches only one subsystem with obvious changes

### Multi-Category PRs

When a PR has multiple prefixes (e.g., `[Perf][Distributed]`):

1. **Identify primary type** (first prefix usually indicates main intent)
2. **Invoke primary skill first**
3. **Use secondary skill for cross-cutting concerns:**

| Scenario | Primary | Secondary |
|----------|---------|----------|
| `[Perf]` + `[Distributed]` | `vllm-omni-perf` | `vllm-omni-distributed` (check TP scaling) |
| `[Perf]` + `[Model]` | `vllm-omni-perf` | `vllm-omni-contrib` (check model integration) |
| `[Model]` + `[Quantization]` | `vllm-omni-contrib` | `vllm-omni-quantization` (check quality impact) |
| `[Feature]` + `[API]` | `vllm-omni-api` | — (API skill usually sufficient) |
| `[Distributed]` + `[Hardware]` | `vllm-omni-distributed` | `vllm-omni-hardware` (check backend compat) |

### Hardware Platform Detection

**Scan the diff for hardware-specific patterns. If found, invoke `vllm-omni-hardware` skill.**

```bash
gh pr diff <pr_number> --repo vllm-project/vllm-omni | grep -E 'is_npu|is_cuda|torch\.cuda|torch_npu'
```

| Pattern | Platform | Review Focus |
|---------|----------|--------------|
| `is_npu` | NPU (Ascend) | NPU-specific ops, memory, compatibility |
| `is_cuda` | CUDA | Device checks, conditional paths |
| `torch.cuda` | CUDA | Device placement, memory management |
| `torch_npu` | NPU (Ascend) | NPU bindings, compatibility |

**When detected, check for:**
- Missing NPU fallback paths when CUDA is primary
- Hardcoded device assumptions (`cuda:0` vs device-agnostic)
- Platform-specific ops without guards
- Memory management differences between platforms

### Step 3: Run Red Flag Checks

**Required for ALL PRs:**

- [ ] What invariant could this diff violate?
- [ ] Which error, cancellation, or cleanup path changed?
- [ ] Which caller, config, or test relies on the previous behavior?
- [ ] New API without tests?
- [ ] New model without tests?
- [ ] Performance claims without benchmarks?
- [ ] Mixin after `nn.Module` with `__init__` setting attributes?
- [ ] API changes without documentation?

### PR-Type Escalation Rules

| PR Type | What to be skeptical about |
|---------|-----------------------------|
| `[Refactor]` | Treat "no behavior change" as unproven. Look for reordered side effects, changed exception flow, lazy/eager init shifts, and altered defaults. |
| `[Bugfix]` | Verify the regression test would fail on the old code and covers the adjacent edge case, not just the happy path. |
| `[Feature]` | Check invalid input, docs/API contract, interaction with existing models, and whether existing configs keep working. |
| `[Performance]` | Require before/after numbers and look for hidden regressions in memory, cold start, async throughput, or distributed execution. |

### Step 3.5: Delegate to Specialized Agents

**Trigger-based delegation for deeper analysis.** Only invoke if trigger conditions are met.

| Trigger Condition | Agent | Focus | Max Comments |
|-------------------|-------|-------|--------------|
| `try/except` or `except:` blocks added/modified | `pr-review-toolkit:silent-failure-hunter` | Silent failures, inadequate error handling, bad fallbacks | 2 |
| New `class` definitions with `@dataclass` or `TypedDict` | `pr-review-toolkit:type-design-analyzer` | Invariant design, encapsulation, type safety | 1 |
| Test files modified (`.test.`, `_test.`, `tests/`) | `pr-review-toolkit:pr-test-analyzer` | Coverage gaps, edge case coverage, mock quality | 2 |
| Changes to `vllm_omni/entrypoints/` | `pr-review-toolkit:code-reviewer` | Security vulnerabilities, input validation, injection risks | 2 |
| Changes to config/validation code | `pr-review-toolkit:code-reviewer` | Validation completeness, edge cases | 1 |

**How to invoke:**

```bash
# Use the Agent tool with the appropriate subagent_type
# Example for silent-failure-hunter:
Agent(subagent_type="pr-review-toolkit:silent-failure-hunter", prompt="Review the error handling in this PR diff for silent failures...")
```

**Delegation rules:**
- Max 2 agents per PR (avoid review overload)
- Skip if PR is small (< 50 lines) or documentation-only
- Agent comments count toward the 5-comment limit
- If agent finds no issues, don't post anything

**Integration with domain skills:**
- Domain skills (Step 2) take priority over general agents
- Run agents AFTER domain skill invocation
- Agents can validate domain skill recommendations

### Step 4: General Code Quality Layer

**For non-domain code**, invoke general review capabilities.

**When to invoke `code-reviewer` agent:**
- Changes to utility files (`vllm_omni/utils/`, `vllm_omni/config/`)
- Changes to CLI or setup code
- PR has no domain prefix (no `[Image]`, `[Audio]`, etc.)
- Changes span multiple unrelated subsystems

```bash
# Invoke via Agent tool
Agent(subagent_type="code-reviewer", prompt="Review this PR for security vulnerabilities, performance issues, and production reliability. Focus on high-priority issues only.")
```

**Focus areas for general review:**
| Category | Examples |
|----------|----------|
| Security | SQL injection, command injection, path traversal |
| Performance | O(n²) algorithms, unnecessary allocations |
| Reliability | Race conditions, resource leaks |
| Code quality | Dead code, unreachable paths |

**Skip general review if:**
- Domain skill already covers the changes
- PR is < 20 lines
- PR is documentation-only

### Step 5: Check Pitfalls by Directory

Check pitfalls relevant to affected directories first, then consult [references/pitfalls.md](references/pitfalls.md) for detailed explanations.

| Affected Directory | Pitfalls to Check |
|--------------------|-------------------|
| `vllm_omni/engine/` | Scheduler state, pipeline coordination |
| `vllm_omni/diffusion/` | Memory growth, generation quality |
| `vllm_omni/connectors/` | Shared memory leaks, IPC issues |
| `vllm_omni/stages/` | Stage lifecycle, config validation |
| `vllm_omni/model_executor/` | Weight loading, device placement |
| `vllm_omni/entrypoints/` | Input validation, error handling |
| `*` (any) | MRO issues with mixins, async vs sync path differences |

### Step 6: Post Review

```bash
gh api repos/vllm-project/vllm-omni/pulls/<pr_number>/reviews --input - <<EOF
{
  "event": "REQUEST_CHANGES" | "APPROVE" | "COMMENT",
  "body": "<summary>",
  "comments": [
    {"path": "<file>", "line": <num>, "body": "<comment>"}
  ]
}
EOF
```

**Review event selection:**
- `REQUEST_CHANGES` for high-confidence correctness, safety, regression, or contract issues
- `COMMENT` for missing evidence or non-blocking concerns that still need action
- `APPROVE` only when no actionable findings remain after the failure-mode sweep

If approving, keep the body factual and short. Example: `No blocking issues found after reviewing tests, invariants, and error paths.`

## Comment Phrasing Guidelines

| PR State | Style |
|----------|-------|
| **Draft** | Ask questions, suggest alternatives: "Consider X for Y because..." |
| **Ready** | Request changes: "Please address..." "This needs..." |
| **Approved/In Progress** | Only comment if blocking: "Note: found issue at..." |

**Phrasing rules:**
- Lead with the defect, not the author's intent
- Name the trigger condition: "This breaks when..." "This changes the contract for..."
- Ask for the missing proof explicitly: test name, benchmark, validation path
- Delete any sentence that only adds politeness without technical content

## Comment Budget Allocation

Total: **5 comments max** per PR (soft limit, hard exceptions for critical issues)

| Source | Budget | When Used |
|--------|--------|-----------|
| Domain pitfalls (Step 5) | 2-3 | Always for domain PRs |
| Specialized agents (Step 3.5) | 1-2 | When triggers match |
| General review (Step 4) | 1-2 | Non-domain code |
| Manual observations | 0-1 | Critical issues not caught above |

**Budget rules:**
- If domain skill finds 3+ issues, skip general review (already comprehensive)
- Agent comments must be high-confidence (no speculation)
- Combine related findings into single comment when possible

## Priority Order

1. **Missing tests** — highest priority
2. **Unvalidated claims** — demand measurements/evidence
3. **Security concerns** — input validation, resource exhaustion
4. **Design flaws** — architectural issues, race conditions
5. **Breaking changes** — undocumented API changes

**Skip:** Minor style issues, nitpicks, nice-to-haves, linter-covered issues

## Critical Directories

| Directory | Impact | Review Focus |
|-----------|--------|--------------|
| `vllm_omni/engine/` | **Critical** | Scheduler, pipeline coordination |
| `vllm_omni/model_executor/` | **Critical** | Model loading, weight management |
| `vllm_omni/connectors/` | High | Shared memory, IPC |
| `vllm_omni/entrypoints/` | High | API validation, error handling |
| `vllm_omni/stages/` | High | Stage lifecycle, state management |
| `vllm_omni/diffusion/` | High | Generation quality, memory |

## Example Comments

**Good (Demands Evidence):**
```
Where are the memory measurements? The PR claims "50% reduction" but provides no before/after data. Run benchmarks with realistic workloads and report peak VRAM usage.
```

**Good (Missing Tests):**
```
Missing regression test for the pre-existing failure mode. Add a test that reproduces the old behavior first; otherwise this change only proves the happy path still works.
```

**Good (MRO Issue):**
```
This mixin is listed after nn.Module but has an __init__ that sets attributes. When nn.Module.__init__ is called, the mixin's __init__ won't run. Use lazy initialization with @property instead.
```

**Good (Refactor Regression):**
```
This refactor changes the fallback path from "raise" to "return None", which means callers now silently skip failed stage initialization instead of surfacing the error. Please preserve the previous exception contract or add coverage for the new behavior if the change is intentional.
```

**Good (Shallow Test):**
```
The new test only asserts that `generate()` returns a value, but the bug was about stage ordering after connector reuse. Add an assertion on the stage sequence or shared-memory cleanup so the regression is actually pinned down.
```

**Bad (Generic):**
```
The implementation looks good. Consider adding tests.
```

**Good (Agent-Generated - Silent Failure):**
```
This catch block returns an empty list on error, but the caller iterates over the result without checking. If the network fails, downstream code will silently process zero items instead of surfacing the connectivity issue. Consider logging the exception and re-raising, or returning None to signal failure explicitly.
```

**Good (Agent-Generated - Type Design):**
```
The `GenerationConfig` class has 12 fields but only 3 are validated. Fields like `max_tokens` and `temperature` have implicit constraints (must be positive) that aren't enforced. Consider adding a `validate()` method or using a library like pydantic for automatic validation.
```

## Context Fetching

**When to fetch more context:**
- New imports with performance/compatibility implications
- 3-line diff context isn't enough
- Code changes might require config updates
- Need to understand prior decisions or constraints

**Tools:**
```bash
# Get surrounding code
gh api repos/vllm-project/vllm-omni/contents/<path>?ref=<branch>

# Find symbol definition
gh search code --repo vllm-project/vllm-omni "class <SymbolName>"

# Check related configs
gh search code --repo vllm-project/vllm-omni "<config_key>" --extension yaml

# Find discussions on similar topics
gh search discussions --repo vllm-project/vllm-omni "<topic>"
```

**Limits:** 3-5 context fetches per review, 20-50 lines each

> **Note:** For linked issues and related PRs, see Step 1.5 which handles this systematically.

## Known Dependencies

Do NOT flag these as missing:
- `einops` — inherited from vLLM
- `diffusers` — already in requirements

## References

- [Common Pitfalls](references/pitfalls.md) — MRO issues, connector state, async patterns
- [Architecture](references/architecture.md) — System overview and critical paths
- [Code Patterns](references/code-patterns.md) — Async, distributed, KV cache patterns

## Quick Reference: What to Invoke When

| PR Contains | Invoke | Why |
|-------------|--------|-----|
| `[Image]`, `[Video]`, `[Audio]`, etc. | Domain skill (Step 2) | Domain-specific validation |
| `is_npu`, `torch_npu`, NPU code | `vllm-omni-hardware` | Platform compatibility |
| Changes to `vllm_omni/engine/` | Pitfalls check + domain skill | Critical path |
| `try/except` blocks | `silent-failure-hunter` | Catch silent failures |
| New dataclasses/TypedDicts | `type-design-analyzer` | Invariant validation |
| Test file changes | `pr-test-analyzer` | Coverage gaps |
| API endpoint changes | `code-reviewer` + `vllm-omni-api` | Security + domain |
| Utility/config changes | `code-reviewer` | General quality |
| No domain prefix | `code-reviewer` | General-purpose review |
| < 20 lines, doc-only | Nothing | Skip extra review |
