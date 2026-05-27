---
name: vllm-omni-pre-check
description: Use before submitting a PR to vllm-project/vllm-omni — self-check the branch against project conventions, catch dead code, verify accuracy/performance claims, and confirm merge readiness. Use when the user says "pre-check", "self review", "pre-submit check", or "check my PR before I open it."
---

# vLLM-Omni Pre-Check

Self-review your branch before creating a PR. Two modes: **quick** catches showstoppers, **full** does a thorough maintainer-grade review. Never posts to GitHub.

## Mode Selection

| Mode | When | Time |
|------|------|------|
| **Quick** | About to push, final sanity check | ~3 min |
| **Full** | Ready for review, want maintainer-level scan | ~10 min |

Default to quick if unsure. Run full before marking a PR "ready for review."

## Workflow

### Step 1: Detect Base Branch

```bash
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main 2>/dev/null)
git diff --name-only ${BASE}...HEAD
```

If no base is found, use `main`.

### Step 2: Categorize the PR

| Diff contains | PR type |
|---------------|---------|
| New files under `vllm_omni/model_executor/models/<name>/` | **New Model** |
| Changes to `vllm_omni/diffusion/` | **Diffusion Model** |
| `[Perf]` in branch name, or benchmark/throughput changes | **Performance** |
| `[Bugfix]` or `[Bug]` in branch name, or single-file fix | **Bug Fix** |
| Everything else | **General** |

### Step 3: Run Checklist

Ask: "Quick mode or full mode?" Then walk the checklist for the detected PR type.

The full item-by-item checklists are in [references/checklists.md](references/checklists.md). Each item produces ✓, ✗, or ⚠.

**New Model PRs** — also load [model-addition-checklist.md](https://github.com/hsliuustc0106/vllm-omni-skills/blob/main/skills/vllm-omni-review/references/model-addition-checklist.md) for detailed dimensions 2 (dead code), 3 (copy-paste), 7 (accuracy), 8 (perf), 9 (benchmark).

### Step 4: Print Report

```
Pre-check report for <branch>

  Mode: quick | full
  Type: <new-model | bug-fix | perf | general>

  Dimension          Result
  ─────────────────  ──────
  PR desc integrity  ✓
  Registry/config    ✓
  Dead code          ⚠ 2 warnings
  Accuracy           ✓
  Benchmark          ✗ missing software versions

  Verdict: 1 blocking | 2 warnings | recommend fixing ✗ before PR
```

**Severity:**

| Mark | Meaning |
|------|---------|
| ✗ | Blocking — fix before opening PR |
| ⚠ | Warning — consider fixing |
| ✓ | Pass |
| — | Skipped (not applicable) |

### Step 5: Stop

Do not post comments, open PRs, or modify files. The report is for the contributor's terminal only.
