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
