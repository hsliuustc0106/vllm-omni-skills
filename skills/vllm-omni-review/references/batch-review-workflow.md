# Batch Review Workflow

How to run a review session: select PRs, review them with varied depth, track state, and follow up on replies.

## Daily Review Session

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

## Pacing Rules

- **Max 3-5 PRs per day.** 34 PRs in 3 days was flagged as suspicious.
- Space reviews out -- not all in one burst.
- Some days, just do reply follow-ups with no new reviews.
- Skip days occasionally -- real reviewers don't review every day.

## Re-Review Protocol

When a contributor pushes new commits or asks for re-review:

1. Check if they addressed your previous comments (read thread replies + new commits)
2. If all resolved: APPROVE. Body: "LGTM" or "looks good now" or empty.
3. If some remain: comment only on unresolved items. Don't re-review from scratch.
4. If new code added: review only the new changes.

Re-reviews should almost always be shorter than the initial review.

## Staleness Rules

- **Contributor stops responding (>7 days):** One ping: "Any updates on this?"
- **PR stale (>14 days):** Move on.
- **PR superseded:** "Looks like this is superseded by #X?"
- **PR closed:** No action.
