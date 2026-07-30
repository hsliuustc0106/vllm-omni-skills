# FM-Agent Verification

Use FM-Agent only as an optional second-pass verifier for high-risk PRs. It is not part of the default review loop.

FM-Agent repo: https://github.com/fmagent-project/FM-Agent

## When to Use

Good candidates:
- Async/deferred output materialization, scheduler state, connector lifecycle, request cleanup, and session reset/shutdown changes
- Config propagation or compatibility layers where legacy and new paths must preserve behavior
- Memory/KV ownership changes where leaks, stale state, or wrong lifetime boundaries are plausible
- Re-review after a large refactor when the likely bug shape is an invariant mismatch and a small probe can confirm it

Skip FM-Agent for:
- Docs-only, style-only, CI-gate, dependency metadata, or routine test-review PRs
- Performance and accuracy claims that need A/B hardware evidence
- Model-quality validation that requires real GPU/NPU/XPU execution and human inspection

## How to Run

1. Create or use an isolated checkout of the PR. Prefer a clean worktree so FM-Agent output does not mix with review edits.
2. Write a short intent file describing the risky change and invariants to check. Keep it factual: changed files, expected behavior, and suspected invariant boundaries. Do not include the intended answer.
3. In the FM-Agent checkout, configure the LLM provider and make sure the target repo's probe-test environment is usable.
4. If probe execution needs repo-specific commands, edit FM-Agent's `md/bug_validator.md` to prefer fast, local commands and to avoid unavailable hardware by default.
5. Run:

```bash
uv run python main.py <pr-worktree> --isolate --incremental <intent-file>
```

If no prior `fm_agent/version.log` exists, incremental mode falls back to a full run. For a fresh one-off check, `--isolate` is still useful because FM-Agent writes `fm_agent/` output inside the target checkout.

## Output Handling

Read:
- `fm_agent/bug_validation/summary.json`
- `fm_agent/bug_validation/*.md`
- relevant probe scripts and probe output

Treat every report as a lead, not a finding. FM-Agent can hallucinate when the model or context is weak. Before commenting:
- Verify code evidence and line numbers against the PR head
- Run or inspect the probe enough to confirm it matches vllm-omni runtime constraints
- Check whether the issue is already covered by an existing unresolved thread
- Reduce the result to one concise, actionable review comment

Do not post FM-Agent summaries, raw specifications, or long generated reports to GitHub. Use them to guide manual review.

## Suggested Intent Template

```text
Review PR <number>: <title>

Changed files:
- <path>: <brief role>

Risk focus:
- <state/lifecycle/config invariant to verify>
- <what must remain true across sync/async, stage, device, or legacy/new paths>

Probe constraints:
- Prefer CPU/unit-level probes when possible
- Do not require model downloads or unavailable GPU/NPU/XPU hardware
- Report suspected bugs with exact trigger conditions and minimal reproduction
```
