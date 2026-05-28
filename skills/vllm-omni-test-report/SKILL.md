---
name: vllm-omni-test-report
description: Two report kinds; **default output is always HTML** unless the user explicitly asks for Markdown (.md). **Release** — `scripts/compose_full_report.py` (**测试结论**, Buildkite metrics, **Test Result** = Common stack + optional `--log-dir-h*` nightly-style summaries + H100/CI block, **Issue tracking** = GitHub `ci-failure` + *local test* in:title, Open bugs); use `--format markdown` only when the user wants .md or `patch_report_*.py`. **Nightly** — `scripts/nightly_local_log_report.py` from local `nightly_jobs` (fetch: vllm-omni-nightly-local) plus optional latest Buildkite scheduled nightly when token is set; use `--markdown-report` / `--to-stdout markdown` only when the user asks for Markdown. Use when generating Buildkite release summaries, parsing local nightly_jobs with CI cross-check, or opening https://buildkite.com/vllm/vllm-omni/builds?branch=main for CI documentation.
---

# vLLM-Omni Test Report

## Report types

| Kind | Output | When to use |
|------|--------|-------------|
| **release** | **HTML** (default): `compose_full_report.py` without `--format markdown` | **测试结论** + **Metrics** + **Test Result** (matrix Common stack; H200/H800/A100 optional log roots; H100 = CI nightly) + **Issue tracking** (ci-failure + *local test* in:title) + **Open issues** (bugs in stats window). |
| **nightly** | **HTML** (default): `nightly_local_log_report.py --html-report …` | **Local** `nightly_jobs` tree (see nightly-local) **and** optional **Buildkite** latest scheduled nightly (same log analysis as local; needs token unless `--no-buildkite`). |

## Default output (HTML)

**Unless the user explicitly asks for Markdown** (e.g. “生成 md / markdown”、hand-editing, or `patch_report_*.py`), **always produce HTML**: `compose_full_report.py` (default) and `nightly_local_log_report.py --html-report <path>.html`. Use `--format markdown` or `--markdown-report` / `--to-stdout markdown` **only** after that explicit request.

## Agent Quick Path

**Intent keywords:**
- **Nightly**: `nightly`, `nightly report`, `nightly_jobs`, `scheduled nightly`, `生成 nightly`, `夜间报告`, `每日报告`.
- **Release**: `release report`, `test report`, `正式报告`, `发布报告`, `测试报告`.
- **Markdown opt-in only**: `markdown`, `.md`, `生成 md`, `生成 markdown`.

### Nightly Quick Path

Ask for or infer:
- Output date/name, e.g. `nightly-report-buildkite-latest-YYYY-MM-DD.html`.
- Buildkite token in the environment (`BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN`) unless the user explicitly wants `--no-buildkite`.
- Kanban repo root for baseline comparison: `--kanban-repo-root /path/to/vllm-omni-kanban`.
- Optional pinned Buildkite build: `--buildkite-build N`.
- Optional local logs: `REPO_ROOT=/path/to/local/vllm-omni` with `logs/nightly_jobs`, or pass `--log-dir`.

If the user asks for fresh kanban data (`fresh`, `latest assets`, `更新 kanban`, `最新 assets`), first use the kanban repo skill `.cursor/skills/update-main-docs/SKILL.md` in `vllm-omni-kanban`; then run the report command here.

```bash
export BUILDKITE_TOKEN=...  # or BUILDKITE_API_TOKEN; omit only with --no-buildkite
python scripts/nightly_local_log_report.py \
  --html-report ./nightly-report-buildkite-latest-YYYY-MM-DD.html \
  --kanban-repo-root /path/to/vllm-omni-kanban \
  --title "Nightly Buildkite report - YYYY-MM-DD"
```

### Release Quick Path

Ask for or infer:
- Buildkite token in the environment (`BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN`) - required unless using `--preview`.
- GitHub token (`GITHUB_TOKEN` or `GH_TOKEN`) - recommended for stable issue data.
- Optional stats window: `--stats-from YYYY-MM-DD --stats-to YYYY-MM-DD`.
- Optional GPU local logs: `--log-dir-h200`, `--log-dir-h800`, `--log-dir-a100`.
- Optional output path: `--out ./vllm-omni-test-report-YYYY-MM-DD.html`.

```bash
export BUILDKITE_TOKEN=...  # or BUILDKITE_API_TOKEN
export GITHUB_TOKEN=...     # optional but recommended
python scripts/compose_full_report.py \
  --out ./vllm-omni-test-report-YYYY-MM-DD.html
```

With optional GPU nightly summaries:

```bash
python scripts/compose_full_report.py \
  --log-dir-h200 /path/to/nightly_jobs_h200 \
  --log-dir-h800 /path/to/nightly_jobs_h800 \
  --log-dir-a100 /path/to/nightly_jobs_a100 \
  --out ./vllm-omni-test-report-YYYY-MM-DD.html
```

## Nightly report (local logs + optional Buildkite nightly, HTML)

**Prerequisite:** `LOG_DIR` on disk - paths and pytest rules in [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md). To **produce** logs on the HK cluster in Docker, follow [vllm-omni-nightly-local](../vllm-omni-nightly-local/SKILL.md): **inside the container**, run **`source /rebase/.venv/bin/activate`** before `run_nightly_jobs.sh` or other repo commands ([environment](../vllm-omni-nightly-local/references/nightly-local-environment.md)). To **copy** logs to your laptop, use [../vllm-omni-nightly-local/references/nightly-local-log-fetch.md](../vllm-omni-nightly-local/references/nightly-local-log-fetch.md) — including **`nightly_perf_manual.prev.xlsx`** when needed and **`rm -rf` local `logs/nightly_jobs`** before each sync so old runs are not mixed in.

**Performance workbook:** If **`logs/nightly_perf_manual.xlsx`** sits next to your `nightly_jobs` directory (same parent `logs/`), the report includes a **性能测试结果** section with one HTML/Markdown table per worksheet. Install **`openpyxl`** (`pip install openpyxl`) to read `.xlsx`. **Before you pull or sync logs for the next run**, if `logs/nightly_perf_manual.xlsx` already exists locally from the previous run, copy it to **`logs/nightly_perf_manual.prev.xlsx`** (baseline for ↑/↓ % deltas); then **remove the local `logs/nightly_jobs` tree** (`rm -rf`) so the new fetch does not keep stale job directories; then fetch the new logs and workbook as usual. Details: [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md) and [../vllm-omni-nightly-local/references/nightly-local-log-fetch.md](../vllm-omni-nightly-local/references/nightly-local-log-fetch.md).

**Local performance baseline:** For Local Test **性能基线对比**, the report auto-detects `<kanban-repo-root>/data/local_nightly_raw` when `--kanban-repo-root` is set. Pass `--local-perf-result-root <path>` only to override that root. The script reads the latest timestamped local perf benchmark result directory under the root. Supported result filenames follow the perf artifact patterns `result_test_*.json`, `diffusion_result_*.json`, and `benchmark_results_*.json`; records must include baseline data such as `benchmark_params.baseline`. This section is separate from `nightly_perf_manual.xlsx`: the workbook shows detailed benchmark tables, while local perf benchmark result JSON powers latest / baseline / vs baseline rows. It is also separate from kanban assets and does not mutate the kanban checkout.

**Full local logs (HTML):** Each failed local job has a **查看完整日志** button that toggles the concatenated raw log text. If the merged files exceed **2 MiB** (see `FULL_LOG_EMBED_MAX_BYTES` in `scripts/nightly_local_log_report.py`), the report does **not** embed the text and instead lists absolute paths to open locally.
By default the script also pulls **main** latest **scheduled nightly** from Buildkite (vllm/vllm-omni), downloads each reportable step log, and adds **reason / heuristic analysis / excerpts** for failures (same parsing as local). Set **`BUILDKITE_TOKEN`** or **`BUILDKITE_API_TOKEN`** in the environment; use **`--no-buildkite`** for local-only. Optional **`--buildkite-build N`** to pin a build number.

**Buildkite 性能基线对比（kanban assets）:** Nightly report reads precomputed history from `docs/assets/charts/*_history.json` and fills Buildkite **性能基线对比** with **latest / baseline / vs baseline**. The section keeps only rows with baseline data and only the **latest day** records (grouped to model-level metric rows). Daily report commands should use `--kanban-repo-root <vllm-omni-kanban>` (resolved to `<repo>/docs/assets/charts`).
If the user asks to ensure fresh kanban data, first use the kanban repo skill `.cursor/skills/update-main-docs/SKILL.md` in `vllm-omni-kanban` to update `main` and restart `mkdocs serve`; then generate this report with `--kanban-repo-root`.
Optional source checks:
- `--kanban-expected-remote` / `--kanban-expected-branch` add warnings when current/upstream config differs.

**Kanban raw fallback:** By default the report remains read-only against kanban assets. If `*_history.json` is missing or has no baseline rows, the **性能基线对比** section shows diagnostics for `<kanban-repo>/data/buildkite_nightly_raw` (raw perf JSON count, recent build IDs, latest raw/history mtimes) and explains that local `nightly_jobs` and `nightly_perf_manual.xlsx` are separate report inputs, not baseline sources. To explicitly regenerate kanban assets from raw perf artifacts before rendering, add `--kanban-refresh-from-raw` with `--kanban-repo-root <vllm-omni-kanban>`; optional `--kanban-raw-root <path>` overrides the raw root. This runs kanban-side `scripts/sync_buildkite_raw_model_results.py` for known model groups and then `scripts/generate_charts.py`, so it mutates the kanban checkout under `data/results/` and `docs/assets/charts/`.

**Kanban raw model sync mapping:** Keep `KANBAN_RAW_MODEL_SYNCS` in `scripts/nightly_local_log_report.py` aligned with `vllm-omni-kanban/scripts/mkdocs_hooks.py`. Current mapping: `qwen3omni -> qwen3_omni`, `qwen3tts -> qwen3_tts`, `qwen_image -> qwen_image`, `qwen_image_edit -> qwen_image_edit`, `qwen_image_edit_2509 -> qwen_image_edit_2509`, `wan22 -> wan22`. When adding a model, update kanban first, then update both the report script constant and this note.

From **this** skill directory (after [fetch](../vllm-omni-nightly-local/references/nightly-local-log-fetch.md) into **`$REPO_ROOT/logs/`** on your machine):

```bash
export REPO_ROOT=/path/to/local/vllm-omni   # logs at $REPO_ROOT/logs/nightly_jobs
export BUILDKITE_TOKEN=...   # optional; omit with --no-buildkite
python scripts/nightly_local_log_report.py \
  --html-report ./nightly-report.html \
  --kanban-repo-root /path/to/vllm-omni-kanban
python scripts/nightly_local_log_report.py \
  --html-report ./nightly-report.html \
  --local-perf-result-root /path/to/vllm-omni-kanban/data/local_perf_results
python scripts/nightly_local_log_report.py \
  --html-report ./nightly-report.html \
  --kanban-repo-root /path/to/vllm-omni-kanban \
  --kanban-refresh-from-raw
python scripts/nightly_local_log_report.py --no-buildkite --html-report ./local-only.html
```

Other flags: `--title`, `--buildkite-build`, `--local-perf-result-root`, `--kanban-repo-root`, `--kanban-raw-root`, `--kanban-refresh-from-raw`, `--kanban-expected-remote`, `--kanban-expected-branch`. **Markdown** (only if the user explicitly asks): `--markdown-report`, `--to-stdout markdown`. See `python scripts/nightly_local_log_report.py --help`.

## Release report (Buildkite, HTML)

**Automated (recommended):** from **this** skill directory with `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` set:

```bash
python scripts/compose_full_report.py
# Optional: embed the same grouped Summary as nightly (see nightly-local-log-layout.md):
# python scripts/compose_full_report.py \
#   --log-dir-h200 /path/to/nightly_jobs_h200 \
#   --log-dir-h800 /path/to/nightly_jobs_h800 \
#   --log-dir-a100 /path/to/nightly_jobs_a100
# default: vllm-omni-test-report-YYYY-MM-DD.html in this skill directory
```

**Markdown (opt-in only):** if the user explicitly asks for a `.md` file or needs `scripts/patch_report_*.py`:

```bash
python scripts/compose_full_report.py --format markdown --out ./vllm-omni-test-report-YYYY-MM-DD.md
```

`--format markdown` is for hand-editing or `scripts/patch_report_*.py` (those tools expect `.md`). HTML is produced via `scripts/release_md_to_html.py` internally.

## Overview

Generate a **human-readable test report** ordered as:

1. **测试结论** — 检查项表格：仅 **UT 覆盖率…** 与 **需求 / 性能** 共 3 项在 HTML 为手动 **通过 / 不通过**；**L2&L3最新一次通过率为100%**、**遗留 DI 小于 30**、**致命issue遗留个数为0**、**所有遗留 bug 均已分配责任人** 为 **自动**（Buildkite：与 Metrics 相同的 **ready**（non-main）与 **merge**（main 非 nightly/weekly）各自最近一次**已结束**构建，任一 job 为 `failed`/`broken` 则该项不通过；GitHub：stats window 内 open **`label:bug`** 按 priority labels 加权后 **DI < 30**；**无** open **`critical`**；open **`label:bug`** 均有 **assignee**）。归档/纯 Markdown 与 HTML 一致。
2. **Metrics overview** — Same as before: `buildkite_build_stats.py --markdown` (**Success rate/UT coverage**, **Bug avg first response**, **ut** / **ut (exclude models)**，与 **`--stats-from`..`--stats-to`** 对齐)。
3. **Test Result** — `### Common stack (all rows)` from [references/local-test-matrix.md](references/local-test-matrix.md)；`### H200` / `### H800` / `### A100` 为与 **nightly** 本地 **Summary** 相同的分组表（传入 `--log-dir-h200` / `--log-dir-h800` / `--log-dir-a100`，目录需符合 [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md)）；`### H100（CI — Buildkite scheduled nightly）` 仅含 **Build**（build 号/分支/commit）、可报告 Job **Summary**、**Failed test jobs**（**不含** per-job pytest 详表与 **Analysis (CI Failure)**；需要时请用手工或 `nightly_job_pytest_table.py` / `patch_report_ci_failure.py` 维护独立文档）。
4. **Issue tracking** — GitHub Search：`label:ci-failure`，**title** 含 **`local test`**，`created` 在 stats 窗口内（与 metrics 同源日期范围）。
5. **Open issues (stats window)** — 仍为分页 **`label:bug`**、**open**，`created_at` UTC 日期落在 **`--stats-from`..`--stats-to`**；同一批 issue 预计算每日 DI：`critical` = 10，`high priority` = 3，`medium priority` = 1，`low priority` = 0.1，`invalid` = 0，总和用于 **遗留DI小于30** 自动行。

## When to Apply

- User asks for a **release** / **Buildkite** / **CI** test report for vllm-omni — **default to HTML** via `compose_full_report.py`; use `--format markdown` **only** if they explicitly want Markdown
- User pastes a Buildkite build URL or build number
- User wants to summarize failures, flaky steps, or duration from Buildkite
- User needs **Common stack** or optional **H200/H800/A100** nightly log summaries in the **release** report — set **`--log-dir-h*`** on `compose_full_report.py` when logs are available
- User asks for **nightly** report from **local** `nightly_jobs` — **default to HTML** (`nightly_local_log_report.py --html-report`); Markdown **only** if they explicitly ask (`fetch` in vllm-omni-nightly-local)

## Definitions

| Term | Meaning |
|------|---------|
| **Scheduled nightly build** | A build whose **message/title** contains `Scheduled nightly build` (Buildkite scheduled job). It is **not** the same as arbitrary `main` commits. |
| **Latest** | Among matching builds, the one with the **most recent** `finished_at` or `created_at` (prefer finished if both present). |
| **Reportable job** | Any `jobs[]` entry whose **name** does **not** match `(?i)^Upload .+ Pipeline$` (exclude `Upload Ready/Nightly/Merge Pipeline` and similar upload-only steps). |

## Buildkite authentication (environment only)

- All Buildkite REST calls and skill scripts read **`BUILDKITE_TOKEN`** or **`BUILDKITE_API_TOKEN`** from the **process environment** (either name works for the scripts; use one consistently in CI).
- **Do not** paste the secret into chat, pass it on the command line, or embed it in files committed to git. If unset, ask the user to **export it in their local shell** or **configure it as a CI/secret env var**, then retry.
- Before `curl` or Python helpers, confirm the variable is set in the same shell (e.g. bash: `[ -n "${BUILDKITE_TOKEN:-}" ] || [ -n "${BUILDKITE_API_TOKEN:-}" ]`; PowerShell: `if (-not $env:BUILDKITE_TOKEN -and -not $env:BUILDKITE_API_TOKEN) { ... }`).

## Workflow (release only)

**Test Result (Common stack):** 维护 [references/local-test-matrix.md](references/local-test-matrix.md) 中 **`## Common stack (all rows)`**；H200/H800/A100 小节依赖本机/同步后的 `nightly_jobs` 路径并传给 `compose_full_report.py` 的 **`--log-dir-h*`**。

**Metrics overview、H100（CI）、Issue tracking、Open issues:** 见下文 Step 2–3；**nightly** HTML 仍仅用本文开头的 **Nightly report** 小节。

### Step 1: Resolve the target build (CI testing)

**Option A - API (recommended)**

1. Ensure **`BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN`** is set in the environment for the session that runs `curl` / scripts.
2. If missing, **do not** ask for the raw token in chat. Prompt the user to set it locally (or in CI), e.g. *"Set read-only Buildkite API token in the environment as `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN`, then ask again."* Offer **Option C** (web-only fallback) if they cannot use env-based auth.
3. With the env var set, list builds on `main`:

```bash
curl -s -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  "https://api.buildkite.com/v2/organizations/vllm/pipelines/vllm-omni/builds?branch=main&per_page=30" \
  | jq '.'
```

4. Select the **first** build in the array where `.message` matches `(?i)scheduled nightly` **or** the build is clearly labeled as scheduled in the UI message.
5. If none match, report that no scheduled nightly was found in the page and optionally fall back to the **most recent green/red `main` build** only if the user agrees.

**Option B - User-provided build**

If the user gives a URL like `https://buildkite.com/vllm/vllm-omni/builds/<number>`:

```bash
curl -s -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  "https://api.buildkite.com/v2/organizations/vllm/pipelines/vllm-omni/builds/<number>" | jq '.'
```

**Option C - No env token / user prefers web-only**

- Clearly state that without **`BUILDKITE_TOKEN` / `BUILDKITE_API_TOKEN`** in the environment you can only produce a **summary-level** report (build status/duration), not full step/job breakdown.
- Open the [builds list](https://buildkite.com/vllm/vllm-omni/builds?branch=main) and locate the topmost **Scheduled nightly build** entry.
- Ask the user to paste the **build number** or **full build URL** (and optional failing log snippets) for fallback reporting.

### Step 2: Fetch jobs and steps (exclude Upload pipelines)

For the chosen `build_number`:

```bash
curl -s -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  "https://api.buildkite.com/v2/organizations/vllm/pipelines/vllm-omni/builds/<build_number>" \
  | jq '{
      state, message, commit, branch, created_at, finished_at,
      reportable_jobs: [.jobs[] | select(.name | test("^Upload .+ Pipeline$"; "i") | not)
        | {name, state, id, raw_log_url, log_url}]
    }'
```

- **Summary counts** (passed / failed / skipped / broken): count **only** `reportable_jobs`, not upload steps.
- **Failed steps** tables: include only reportable jobs (upload failures must **not** pollute "test failure" narrative unless the user explicitly asks for pipeline hygiene).

### Step 2b: Per-job pytest results (detailed table)

**Not included in `compose_full_report.py` release output.** Use when authoring a separate CI appendix or nightly-style doc:

1. For **each reportable job**, GET `raw_log_url` (fallback `log_url`) with `Authorization: Bearer` using the same credential as in [Buildkite authentication (environment only)](#buildkite-authentication-environment-only).
2. Parse pytest output from the log (session `=== ... ===` footer; `FAILED` / `ERROR` lines). See [references/buildkite-api.md](references/buildkite-api.md).
3. **Helper:** from the skill directory (requires `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` already exported in that shell):

```bash
python scripts/nightly_job_pytest_table.py              # latest scheduled nightly
python scripts/nightly_job_pytest_table.py --build 4708
```

Paste the emitted **Per-job test execution (pytest)** table where needed. The script **skips** `Upload * Pipeline` jobs.

### Step 2c: Metrics overview (success rate and average duration)

1. From the skill directory, run [scripts/buildkite_build_stats.py](scripts/buildkite_build_stats.py) with `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` set. Optional `GITHUB_TOKEN` (or `GH_TOKEN`) for the **Bug avg first response** column. The script uses `requests` (`pip install requests` if needed).
2. Optional: pass `--from` / `--to` as `YYYY-MM-DD` (UTC, inclusive) for a custom window. If **both are omitted**, the script uses **the current UTC calendar month through today** (month-to-date). To override one past month, pass both dates (e.g. `--from 2025-01-01 --to 2025-01-31`).
3. Add `--markdown` to print a ready-to-paste **Metrics overview** block: Source line plus CI category table (**Success rate/UT coverage**; **Bug avg first response** on **bugs (first response, YYYY-MM-DD..YYYY-MM-DD)** row from GitHub - same date window as **`--from` / `--to`**; **ut** / **ut (exclude models)** from **Simple Unit Test** log parsing - implementation detail stays in `buildkite_build_stats.py`, not in the pasted report prose).

```bash
pip install requests   # if not already installed
python scripts/buildkite_build_stats.py --markdown
# Or an explicit UTC window (must pass both --from and --to together):
# python scripts/buildkite_build_stats.py --from YYYY-MM-DD --to YYYY-MM-DD --markdown
```

4. Paste the full script output (the `## Metrics overview` section through the main metrics table, including **ut**, **ut (exclude models)**, and **bugs (first response, ...)** rows) into the report as the **first** body section (immediately after the report title). **Do not** hand-edit numbers or coverage; they must match the script run.

See [references/buildkite-api.md](references/buildkite-api.md) for how builds are classified into **ready** / **merge** / **nightly** buckets.

### Step 2d: CI testing - Analysis (CI Failure) GitHub issues (stats date window)

1. Enumerate issues with **`label:bug`** **and** **`label:ci-failure`** (exact names; see [references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md)) and **`created`** (UTC) in **`--stats-from`..`--stats-to`** (same `YYYY-MM-DD` inclusive range as **Metrics overview** / `compose_full_report.py`).
2. Prefer **GitHub Search API**: `GET /search/issues?q=repo:vllm-project/vllm-omni+is:issue+label:bug+label:ci-failure+created:YYYY-MM-DD..YYYY-MM-DD`. Include **open** and **closed** issues returned by Search (no title-based filter).
3. Optional: `GITHUB_TOKEN` / `GH_TOKEN` in the environment for higher rate limits (do not paste tokens into chat).
4. Add **#### Analysis (CI Failure)** (optional hand section; **not** generated by `compose_full_report.py`) with columns **Issue #** | **Title** | **Status** (`Open` / `Closed`). If none match, state that explicitly.
5. **compose_full_report.py** does **not** emit this subsection; use `scripts/patch_report_ci_failure.py` on a hand-maintained `.md` if you need it inside a report file.

### Step 3: Fetch **all** open bug issues (paginated), filter by stats window

Do **not** rely on the GitHub web UI first page for counts or tables - it is incomplete when there are many issues.

1. Prefer **GitHub REST API** pagination: `GET /repos/vllm-project/vllm-omni/issues?state=open&labels=bug&per_page=100&page=...` until a page has **fewer than 100** items (or empty). Merge pages; **exclude** entries with `pull_request` (PRs masquerading as issues).
2. If `GITHUB_TOKEN` is missing and you hit rate limits or need stable automation, **prompt the user** (e.g. `Provide GITHUB_TOKEN to paginate all open bugs reliably and avoid unauthenticated rate limits.`).
3. After the full list is assembled, **keep only** issues whose **`created_at` UTC calendar date** (**`YYYY-MM-DD`**) falls in **`--stats-from`..`--stats-to`** (inclusive), matching **Metrics overview** / `compose_full_report.py` - not "current calendar month" unless those flags happen to bound the month.
4. Commands and a bash/jq example: [references/github-issues-pagination.md](references/github-issues-pagination.md).
5. To refresh **Open issues** in an existing report without re-running the full composer: `python scripts/patch_report_open_issues.py --report <file.md> --stats-from YYYY-MM-DD --stats-to YYYY-MM-DD` (from the skill directory; `GITHUB_TOKEN` / `GH_TOKEN` recommended).

### Step 4: Produce the report

**Full document:** `python scripts/compose_full_report.py` (HTML). For a Markdown file (patch scripts, hand merge): `python scripts/compose_full_report.py --format markdown --out report.md`.

Use the **Report structure** below when assembling manually. Fill:

- **测试结论** — 检查项表 + Go/Rejected（HTML 交互；Markdown 静态默认 Go）
- **Metrics overview** from Step 2c — 紧接 **测试结论** 之后
- **Test Result** — Common stack 自 [references/local-test-matrix.md](references/local-test-matrix.md)；H200/H800/A100 为 nightly 式分组表（若有日志目录）；**H100** 内嵌 **Build**（仅 build 链接、branch、commit）、Summary、失败表（不含 Step 2b pytest、Step 2d **Analysis (CI Failure)**）
- **Issue tracking** — GitHub Search：`label:ci-failure`，title 含 **`local test`**，`created` 在 stats 窗口
- *(Optional)* **Test content (job scope)** — 不由 compose 生成；可用 `patch_report_scope_local.py` 或手写
- **Open issues** from Step 3
- **Unknown** if data was incomplete

## Report structure (same content as compose_full_report HTML / Markdown)

Hand-authored or review-only; automation emits the same sections in HTML by default.

```markdown
# vLLM-Omni Test Report - Scheduled Nightly

## 测试结论

| 检查项 | 检查结果 |
| ... | 通过 / 不通过（HTML：**UT、需求、性能、DI** 可点选；**L2&L3 / 致命 issue / 遗留 bug 责任人** 三行自动锁定；**测试结论：** Go 或 Rejected） |

## Metrics overview

(`buildkite_build_stats.py --markdown`，与 `--stats-from`..`--stats-to` 对齐。)

## Test Result

### Common stack (all rows)

（`references/local-test-matrix.md` 该节正文。）

### H200

（可选：`--log-dir-h200`，与 nightly 本地 Summary 分组一致。）

### H800

（可选：`--log-dir-h800`。）

### A100

（可选：`--log-dir-a100`。）

### H100（CI — Buildkite scheduled nightly）

#### Build
…
#### Summary (reportable jobs only)
…
#### Failed test jobs (if any)
…

## Issue tracking

**Filter:** `label:ci-failure` + **`local test` in:title** + `created` 在 stats 窗口。

| Issue | Title | State | Created (UTC date) |
|-------|-------|-------|---------------------|

## Open issues (stats window)

（REST 分页 `label:bug`；`created_at` 落在 stats 窗口；按 priority labels 计算 DI。）

## Data source

（Buildkite、GitHub、`--log-dir-*` 等。）
```

## Constraints

1. **Do not invent** pass/fail counts: use API JSON or user-confirmed paste.
2. If the API returns 401/403, state that **`BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` must be set in the environment** (read-only token) and fall back to Option C if the user cannot do that.
3. Prefer **Scheduled nightly** explicitly; do not label a random `main` build as nightly without matching the message/pattern.
4. For **open bugs**, **paginate until done**; do not report "all issues" from a single HTML page.
5. Keep prose concise; tables over long bullet lists.
6. **Always omit** `Upload * Pipeline` jobs from **test** summaries and the per-job pytest table unless the user explicitly requests pipeline upload health.

## Related

- CI pipeline concepts: [vllm-omni-cicd](../vllm-omni-cicd/SKILL.md)
- PR review and test gaps: [vllm-omni-review](../vllm-omni-review/SKILL.md)
- Cluster nightly run + docker (produces logs): [vllm-omni-nightly-local](../vllm-omni-nightly-local/SKILL.md)

## Reference

- Buildkite REST API: [Buildkite API documentation](https://buildkite.com/docs/apis/rest-api)
- Optional detail: [references/buildkite-api.md](references/buildkite-api.md)
- GitHub issues (pagination + month filter): [references/github-issues-pagination.md](references/github-issues-pagination.md)
- CI job test scope (what each nightly job tests): [references/ci-job-test-scope.md](references/ci-job-test-scope.md)
- Local / release **Common stack** + compose `--log-dir-*` 说明: [references/local-test-matrix.md](references/local-test-matrix.md)
- CI Failure GitHub issues (`label:bug` + `label:ci-failure`, stats `created` range): [references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md)
- HTML from Markdown (release): [scripts/release_md_to_html.py](scripts/release_md_to_html.py) (used by compose_full_report)
- **Nightly** log tree / pytest parsing: [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md) (fetch off cluster: [vllm-omni-nightly-local](../vllm-omni-nightly-local/SKILL.md))
- Buildkite performance summary from kanban assets: [scripts/kanban_assets_perf_summary.py](scripts/kanban_assets_perf_summary.py)

## Cursor copy

A synced copy for editor discovery: `.cursor/skills/vllm-omni-test-report/` - update both when changing this skill.
