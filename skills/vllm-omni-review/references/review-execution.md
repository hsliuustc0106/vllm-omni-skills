# Review Execution

Use this file when you are actively running the review and need the gate checks, concrete `gh` commands, or comment-writing rules.

## Review Gates

Check these before deep review. If any fail, stop and post a gate-failure summary instead of doing a full review.

| Check | Passing State | Action if Failed |
|-------|---------------|------------------|
| DCO | `SUCCESS` | Ask for signed commits with `git commit -s` |
| pre-commit | `SUCCESS` | Ask the author to run `pre-commit run --all-files` |
| mergeable | `MERGEABLE` | Ask the author to rebase and resolve conflicts |

Command:

```bash
gh pr view <pr_number> --repo vllm-project/vllm-omni --json mergeable,statusCheckRollup --jq '{mergeable, checks: [.statusCheckRollup[] | {name, conclusion}]}'
```

Gate-failure template:

```text
Review blocked until the PR is mergeable and required checks pass.

- DCO: <status>
- pre-commit: <status>
- mergeability: <status>
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

Keep reviews selective.

| PR Shape | Expected Inline Comments |
|----------|--------------------------|
| docs-only or tiny fix | 0 |
| medium bug fix | 1-3 |
| large feature or risky refactor | 3-5 |

Budget rules:

- Cap normal reviews at 5 inline comments
- Merge related issues into one comment
- Skip generic praise and low-confidence speculation
- Praise budget is zero lines
- If domain review already surfaced several issues, skip extra general comments

## Finding Bar

Only post a comment when it includes all of the following:

1. A concrete defect, risk, or evidence gap tied to a specific file, line, or behavior change
2. Why it matters: crash, hang, silent corruption, wrong output, compatibility break, or unverifiable claim
3. A concrete ask: fix, regression test, benchmark, or validation change

Do not post comments that only paraphrase the diff, ask for "more tests" without naming the missing scenario, or speculate without a clear trigger condition.

## Comment Style

Use short, direct comments tied to a concrete file and behavior.

| PR State | Preferred Tone |
|----------|----------------|
| Draft | Ask focused questions and call out missing evidence |
| Ready for review | Request specific changes for blocking issues |
| Approved or already addressed | Comment only on newly found blockers |

Banned patterns:

- generic praise without evidence
- vague quality language like "solid" or "well structured"
- comments without a concrete failure mode or missing validation

Phrasing rules:

- Lead with the defect, not the author's intent
- Name the trigger condition: "This breaks when..." or "This changes the contract for..."
- Ask for the missing proof explicitly: test case, benchmark, or validation path
- Delete any sentence that adds politeness without technical content

## Good Comment Shapes

Missing test:

```text
This bug fix still needs a regression test that reproduces the original failure. Without it, this path can regress silently in a future refactor.
```

Missing evidence:

```text
The PR claims a latency reduction, but I do not see before/after measurements or the benchmark setup. Please include numbers for a representative workload.
```

MRO issue:

```text
This mixin appears after `nn.Module` but still relies on `__init__` side effects. In that hierarchy the mixin initializer will not run, so the new attribute is not guaranteed to exist.
```

Refactor regression:

```text
This refactor changes the fallback path from raising to returning `None`, so callers now silently skip failed stage initialization instead of surfacing the error. Please preserve the previous exception contract or add coverage proving the new behavior is intentional.
```

Shallow test:

```text
The new test only checks that `generate()` returns a value, but the bug was about stage ordering after connector reuse. Add an assertion on the stage sequence or connector cleanup so the regression is actually pinned down.
```

## Review Submission

Use one review summary plus inline comments for the actual findings.

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

Review event selection:

- `REQUEST_CHANGES` for high-confidence correctness, safety, regression, or contract issues
- `COMMENT` for missing evidence or non-blocking concerns that still need action
- `APPROVE` only when no actionable findings remain after reviewing tests, invariants, and error paths

Approval body example:

```text
No blocking issues found after reviewing tests, invariants, and error paths.
```

Summary checklist:

- what you validated
- what still lacks tests or evidence
- whether the PR is blocked or only needs follow-up
