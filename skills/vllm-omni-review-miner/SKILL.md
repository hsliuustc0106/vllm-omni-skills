---
name: vllm-omni-review-miner
description: "Scan pull requests of a specific type (e.g., new model support) from vLLM and vLLM-Omni repos, extract code review patterns and suggestions, then generate a specialized review automation skill. Use when learning from historical pull request reviews, building domain-specific code review expertise, or automating review pattern extraction."
---

# vLLM Review Pattern Miner

## Overview

This skill mines PR review comments from `vllm-project/vllm` and `vllm-project/vllm-omni` to extract recurring review patterns, common issues, and best practices for a specific PR category. It then generates a new specialized review skill under `.claude/skills/`.

## Usage

Invoke this skill with a PR category. Examples:

- `/vllm-omni-review-miner new model support` — mine reviews on PRs that add new model architectures
- `/vllm-omni-review-miner bugfix` — mine reviews on bug fix PRs
- `/vllm-omni-review-miner performance` — mine reviews on performance optimization PRs
- `/vllm-omni-review-miner diffusion` — mine reviews on diffusion/image generation PRs

## Core Workflow

### Step 1: Define Search Scope

Map the user-provided category to search queries. Common mappings:

- **new model**: `label:new-model` or title contains `[Model]`, `add support for`
- **bugfix**: `label:bug` or title contains `[Bugfix]`, `fix`
- **performance**: `label:performance` or title contains `[Perf]`, `optimize`
- **diffusion**: title contains `[Image]`, `diffusion`, `DiT`
- **tts/audio**: title contains `[TTS]`, `[Audio]`, `speech`
- **quantization**: title contains `[Quantization]`, `quant`, `awq`, `gptq`, `fp8`
- **distributed**: title contains `[Distributed]`, `tensor parallel`

For unrecognized categories, construct a best-effort search query from the user's keywords.

### Step 2: Fetch PRs from Both Repos

Use `gh` CLI to search for merged PRs in both repos. Prioritize PRs with substantive reviews (multiple review comments).

```bash
# Search vllm-project/vllm for merged PRs matching the category
gh pr list --repo vllm-project/vllm \
  --state merged \
  --search "<search_query>" \
  --limit 30 \
  --json number,title,url,reviewDecision,comments

# Search vllm-project/vllm-omni for merged PRs matching the category
gh pr list --repo vllm-project/vllm-omni \
  --state merged \
  --search "<search_query>" \
  --limit 30 \
  --json number,title,url,reviewDecision,comments
```

Filter to keep only PRs with review comments (skip auto-merged or rubber-stamped PRs). Aim for **10-20 high-quality reviewed PRs** total across both repos.

**Validation checkpoint**: Verify at least 5 PRs with review comments were found before proceeding. If fewer than 5, broaden the search query or warn the user that the generated skill may lack coverage.

### Step 3: Extract Review Comments

For each selected PR, fetch all review comments:

```bash
# Fetch review comments (inline code review comments)
gh api repos/<owner>/<repo>/pulls/<pr_number>/comments \
  --jq '.[] | {body, path, diff_hunk, created_at, user: .user.login}'

# Fetch review-level comments (top-level review body)
gh api repos/<owner>/<repo>/pulls/<pr_number>/reviews \
  --jq '.[] | {body, state, user: .user.login}'

# Fetch issue-style comments (discussion)
gh api repos/<owner>/<repo>/issues/<pr_number>/comments \
  --jq '.[] | {body, user: .user.login}'
```

### Step 4: Analyze and Categorize Patterns

Process all collected review comments and classify them into:

#### 4.1 Recurring Issues (things reviewers flag repeatedly)

Look for patterns such as:
- Missing tests or insufficient test coverage
- Missing error handling or validation
- Performance concerns (memory, latency, batch size)
- API compatibility issues
- Documentation gaps
- Code style or architecture violations
- Security concerns
- Race conditions or concurrency issues

#### 4.2 Common Suggestions (advice reviewers give)

Extract actionable recommendations:
- "You should add a test for..."
- "Consider using X instead of Y..."
- "This needs to handle the case where..."
- "Please add type annotations for..."

#### 4.3 Approval Criteria (what makes a PR approvable)

Identify what reviewers look for before approving:
- Required tests present and passing
- Benchmark results provided
- Documentation updated
- No breaking changes (or migration path provided)
- Code follows existing patterns

#### 4.4 Domain-Specific Knowledge

Extract technical knowledge unique to this PR category:
- Architecture constraints
- Required integration points
- Common pitfalls
- Performance expectations

**Validation checkpoint**: Review extracted patterns with the user before generating the skill. Confirm the top 5 patterns are accurate and relevant to the category.

### Step 5: Generate the Specialized Review Skill

Create a new skill directory and files:

```
.claude/skills/vllm-omni-review-<category>/
├── SKILL.md                    # Main skill with review checklist
└── references/
    ├── review-checklist.md     # Detailed checklist derived from patterns
    ├── common-issues.md        # Recurring issues with examples
    └── review-examples.md      # Real review comment examples (anonymized)
```

#### SKILL.md Template

The generated SKILL.md should follow this structure:

```markdown
---
name: vllm-omni-review-<category>
description: Specialized review skill for <category> PRs in vLLM/vLLM-Omni, derived from analysis of N historical PR reviews. Use when reviewing <category>-related pull requests.
---

# <Category> PR Review Guide

## Overview

This review skill was generated by analyzing N reviewed PRs from vLLM and vLLM-Omni
repositories. It encodes the most common review patterns, issues, and approval criteria
specific to <category> PRs.

## Quick Checklist

[Generated checklist of the top 10-15 most important review points, ordered by frequency]

## Detailed Review Areas

### [Area 1: Most Common Issue Category]
[Description, what to look for, examples from real reviews]

### [Area 2: Second Most Common]
...

## Common Pitfalls

[List of domain-specific pitfalls extracted from review comments]

## Approval Criteria

[What reviewers expect before approving this type of PR]

## Anti-Patterns

[Things that reviewers consistently reject or request changes for]

## References

- [Review Checklist](references/review-checklist.md)
- [Common Issues](references/common-issues.md)
- [Review Examples](references/review-examples.md)
```

### Step 6: Update Review Router (Optional)

If the generated skill should be integrated into `vllm-omni-review`, suggest adding a routing entry in `vllm-omni-review/references/review-routing.md`.

### Step 7: Present Summary to User

After generating the skill, present:
1. How many PRs were analyzed from each repo
2. Top 5 most common review patterns found
3. The generated skill location and structure
4. Suggestion to review and refine the generated skill

## Important Guidelines

- **Anonymize when appropriate**: Don't attribute specific criticism to specific reviewers in the generated skill. Focus on the patterns, not the people.
- **Prioritize by frequency**: Issues that appear in 5+ PRs are more valuable than one-off comments.
- **Include real examples**: Concrete code snippets from reviews are more useful than abstract rules.
- **Cross-repo patterns**: Note when a pattern appears in both vLLM and vLLM-Omni — these are likely the most important.
- **Keep it actionable**: Every item in the generated skill should be something a reviewer can check in under 2 minutes.
- **Rate limit awareness**: Space out API calls to avoid GitHub rate limiting. Use `--paginate` judiciously.

## Error Handling

- If `gh` is not authenticated, prompt the user to run `gh auth login`
- If a repo returns no results, try broadening the search query
- If rate-limited, inform the user and suggest retrying later
- If fewer than 5 PRs are found, warn that the generated skill may lack coverage

## References

- See [references/search-strategies.md](references/search-strategies.md) for advanced search query patterns
- See [references/analysis-prompts.md](references/analysis-prompts.md) for review comment classification guidance
