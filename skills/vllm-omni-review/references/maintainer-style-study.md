# Maintainer Review Style Study

Calibration data from **200 DarkLight1337 (Cyrus Leung) reviews** on vllm-project/vllm plus **400+ comments** from 12 other core maintainers across vllm and vllm-omni. Use this as ground truth for how real reviews should look.

## Reviewers Studied

| Reviewer | Role | Sample Size |
|----------|------|-------------|
| DarkLight1337 | Core maintainer (multimodal) | ~200 reviews deep dive |
| njhill | Core maintainer (engine/perf) | ~24 inline + replies |
| jeejeelee | Model reviewer | ~11 inline |
| hmellor | Core maintainer (models/transformers) | ~9 inline |
| ProExpertProg | Core maintainer (compilation/IR) | ~14 inline |
| mgoin | Quantization/eval | ~9 inline + replies |
| WoosukKwon | Project lead | Few but high-signal |
| varun-sundar-rabindranath | Kernel reviewer | ~27 inline |
| AndreasKaratzas | ROCm CI | ~23 inline + many replies |

## DarkLight1337 Review Body Stats

| Pattern | Frequency |
|---------|-----------|
| Empty body (just inline comments or silent APPROVE) | ~60% |
| Ultra-short ("Thanks", "LGTM", "Some more nits") | ~25% |
| One-sentence architectural point | ~10% |
| Multi-sentence design discussion | ~5% |

## DarkLight1337 Inline Comment Distribution

| Type | Frequency | Examples |
|------|-----------|---------|
| Direct imperative | ~35% | "Move imports to the top", "Please keep in alphabetical order", "Revert changes to this file", "Fix this" |
| Direct question | ~25% | "Is this really needed?", "Why change this?", "Where is this defined?", "Does X not work here?" |
| Suggestion blocks | ~15% | Code fix with zero explanation text |
| "Can you/we" requests | ~10% | "Can you move X to Y?", "Can you address this?", "Can we cache this?" |
| Soft opinion | ~8% | "Tbh I think...", "I prefer...", "IMO...", "I don't like how..." |
| Ultra-short | ~7% | "Ditto", "Same", "No need", "Good catch", "Seems unused" |

## DarkLight1337 Stock Phrases

These are real phrases used repeatedly across 200 reviews:

- "Is this really needed?"
- "Can you address this?" / "Please address this"
- "Seems unused" / "Looks unused"
- "Is this change related?"
- "Please keep in alphabetical order"
- "Please fix pre-commit"
- "Move imports to the top" / "Import from the top"
- "Remove the commented out code"
- "Let's keep things simple"
- "Any update?"
- "Tbh I think..."
- "I don't quite understand this"
- "Hmm... that's true, OK then"
- "Sorry for the delay!"
- "Thanks for your patience!"

## Things DarkLight1337 Never Does

- Never prefixes with "Nit:" -- just states the issue
- Never says "left a few comments inline"
- Never praises code structure inline ("Good placement", "Nice refactor")
- Never over-explains obvious suggestion blocks
- Never uses structured review templates (## Summary, BLOCKER tables)
- Never uses dramatic emphasis ("CRITICAL", "BREAKING")

## Other Maintainer Patterns

### Comment Length
- **Ultra-short (1-5 words):** "ditto", "DITTO", "Done", "Fixed", "Good catch", "nope"
- **Short (1 line):** "Can we fuse this add into norm?", "Why not use field(default_factory=...)?"
- **Medium (2-4 lines):** Typical for suggestions with brief rationale
- **Long (5+ lines):** RARE -- only for architectural discussions

**Distribution:** ~50% ultra-short/short, ~30% medium, ~20% long

### Reply Thread Patterns

**Acknowledgments:**
- "Done" / "Fixed" / "Oops, fixed" -- DarkLight1337
- "Makes sense" -- jeejeelee
- "Good catch" -- multiple reviewers

**Pushback (direct, not hedged):**
- "This is pre-existing behavior" -- AndreasKaratzas
- "We cannot do that because of [link]" -- DarkLight1337
- "I think you misunderstood this" -- njhill

**Concessions:**
- "Alright, thanks for explaining" -- DarkLight1337
- "Yeah that's fair, I didn't notice that initially" -- ProExpertProg

### PR-Level Comments
- "cc @X" -- extremely common for tagging area owners
- "@X PTAL." -- (Please Take A Look)

### Review Body Patterns
- "LGTM." / "Looks good."
- "this is consistent with our other models. thanks!"
- "I assume you have tested this locally."

## Key Gaps Between AI Reviews and Real Maintainers

| Aspect | Real Maintainers | Common AI Pattern | Fix |
|--------|-----------------|-------------------|-----|
| Review body | ~60% empty | Always writes a body | Skip body ~50% |
| "Nit:" prefix | Rarely used | Overused | Drop it -- just state the issue |
| "left X comments" | Never | Common preamble | Never say this |
| Hedging | ~15% of comments | ~50%+ | Be direct by default |
| Empty APPROVE | ~30% of approvals | Rare | Use more silent approves |
| Depth variation | 0-15 comments | Consistently 3-5 | Vary more |
| Structured templates | Never | Common (## Summary, tables) | Drop all templates |
| Inline praise | Never | Occasional | Never do it |
