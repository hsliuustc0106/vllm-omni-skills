#!/usr/bin/env python3
"""
Compose a full test report (default **HTML**).

Agents and users should **emit HTML by default**; pass ``--format markdown`` only when a Markdown file is explicitly required (e.g. hand-editing, ``patch_report_*.py``).

  - 测试结论: interactive checklist (HTML) / static MD; 自动行：「L2&L3…」= Buildkite 最新已结束
    **ready** + **merge**（与 metrics 同口径）均无 failed/broken job；「致命issue…」= 无 open ``critical``；
    「遗留bug…」= open ``bug`` 均有 assignee
  - Metrics overview: buildkite_build_stats.py --markdown
  - Test Result: Common stack from references/local-test-matrix.md; H200/H800/A100 from
    optional --log-dir-h* (nightly-style Summary); H100 = Buildkite scheduled nightly (**Build** 表
    仅 build 链接、branch、commit；**Summary** + failed-jobs 表 — no per-job pytest or bug+ci-failure analysis)
  - Issue tracking: GitHub Search label:ci-failure + local test in:title (stats window)
  - Open issues: GitHub open bugs (label:bug); filter `created_at` to --stats-from..--stats-to (UTC)

Requires BUILDKITE_TOKEN or BUILDKITE_API_TOKEN in the environment.
Run from skill dir: python scripts/compose_full_report.py
(Use ``--format markdown`` only when a ``.md`` artifact is explicitly needed, e.g. for ``patch_report_*.py``.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from md_table import render_markdown_table
from nightly_local_log_report import markdown_local_summary_from_log_dir
from release_md_to_html import (
    convert_release_report_markdown,
    materialize_release_conclusion_in_markdown,
    RELEASE_CONCLUSION_PLACEHOLDER,
)

CI_FAILURE_LABEL = "ci-failure"  # matches GitHub label on vllm-project/vllm-omni

ORG = "vllm"
PIPELINE = "vllm-omni"
BRANCH = "main"
UPLOAD_PIPELINE_RE = re.compile(r"^Upload .+ Pipeline$", re.IGNORECASE)


def _github_tls_verify() -> bool:
    """Same as ``GITHUB_INSECURE_SSL`` in ``buildkite_build_stats.py`` (GitHub API only)."""
    v = (os.environ.get("GITHUB_INSECURE_SSL") or "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return False
    return True


if not _github_tls_verify():
    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass


def http_get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> object:
    """
    GET JSON from ``url``. Prefer ``requests`` when installed (better TLS/proxy behavior on some
    Windows setups); fall back to :mod:`urllib`.

    For ``api.github.com``, TLS verification follows ``GITHUB_INSECURE_SSL`` (see
    ``buildkite_build_stats.py``). Other hosts always verify.
    """
    h = dict(headers or {})
    verify = True
    if "api.github.com" in url:
        verify = _github_tls_verify()
    try:
        import requests
    except ImportError:
        requests = None
    if requests is not None:
        last_err: Exception | None = None
        for attempt in range(12):
            try:
                r = requests.get(url, headers=h, timeout=timeout, verify=verify)
                if r.status_code == 429:
                    ra = r.headers.get("Retry-After", "60")
                    try:
                        wait_s = int(float(ra)) + 1
                    except ValueError:
                        wait_s = 61
                    time.sleep(min(180, max(1, wait_s)))
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                last_err = e
                if attempt < 11:
                    time.sleep(min(8, 2 ** min(attempt, 3)))
        assert last_err is not None
        raise last_err
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def http_json(url: str, token: str | None = None) -> object:
    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return http_get_json(url, headers=headers, timeout=120)


def latest_scheduled_nightly_number(token: str) -> int:
    url = (
        f"https://api.buildkite.com/v2/organizations/{ORG}/pipelines/"
        f"{PIPELINE}/builds?branch={BRANCH}&per_page=50"
    )
    builds = http_json(url, token)
    assert isinstance(builds, list)
    for b in builds:
        if re.search(r"scheduled\s+nightly", (b.get("message") or ""), re.I):
            return int(b["number"])
    sys.exit("No scheduled nightly build found on main (per_page=50).")


def _issue_created_date_utc(issue: dict) -> str | None:
    """``YYYY-MM-DD`` from GitHub ``created_at`` or ``None``."""
    ca = issue.get("created_at")
    if not ca or not isinstance(ca, str):
        return None
    s = ca.strip().replace("Z", "+00:00")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return None


def _github_fetch_open_issues_with_label(gh_token: str | None, label: str) -> list[dict]:
    """Paginate **open** issues with a single GitHub label (PR entries excluded)."""
    base = "https://api.github.com/repos/vllm-project/vllm-omni/issues"
    lab = urllib.parse.quote(label)
    all_items: list = []
    page = 1
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "vllm-omni-compose-report",
    }
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"
    while True:
        url = f"{base}?state=open&labels={lab}&per_page=100&page={page}"
        batch = http_get_json(url, headers=headers, timeout=60)
        if not batch:
            break
        for i in batch:
            if i.get("pull_request"):
                continue
            all_items.append(i)
        if len(batch) < 100:
            break
        page += 1
    return all_items


def _github_fetch_open_bug_issues(gh_token: str | None) -> list[dict]:
    """Paginate **open** issues with label ``bug`` (PR entries excluded)."""
    return _github_fetch_open_issues_with_label(gh_token, "bug")


def no_open_critical_labeled_issues(
    gh_token: str | None,
) -> tuple[bool, str]:
    """
    For **测试结论** row «致命issue遗留个数为0»: pass iff there is **no** open (non-PR)
    issue with label ``critical``.
    """
    try:
        issues = _github_fetch_open_issues_with_label(gh_token, "critical")
    except Exception as exc:
        return False, f"无法检测 label critical（{exc}）"
    if not issues:
        return True, ""
    nums: list[int] = []
    for i in issues:
        try:
            nums.append(int(i["number"]))
        except (KeyError, TypeError, ValueError):
            continue
    nums.sort()
    show = nums[:15]
    tail = f" 等共 {len(nums)} 个" if len(nums) > len(show) else ""
    lst = "、".join(f"#{n}" for n in show)
    return False, f"仍存在含 label **critical** 的 open issue：{lst}{tail}"


def open_bug_assignees_all_assigned(
    gh_token: str | None,
) -> tuple[bool, str]:
    """
    For **测试结论** auto row: pass iff every open ``bug`` issue has at least one assignee.

    Returns ``(ok, detail)`` — ``detail`` is empty on success; on failure, a short Chinese
    note listing unassigned issue numbers (or an error reason if the API call fails).
    """
    try:
        issues = _github_fetch_open_bug_issues(gh_token)
    except Exception as exc:
        return False, f"无法检测 assignee（{exc}）"
    unassigned: list[int] = []
    for i in issues:
        assignees = i.get("assignees")
        if assignees is None:
            assignees = []
        if not assignees:
            try:
                unassigned.append(int(i["number"]))
            except (KeyError, TypeError, ValueError):
                continue
    if not unassigned:
        return True, ""
    unassigned.sort()
    show = unassigned[:15]
    tail = f" 等共 {len(unassigned)} 个" if len(unassigned) > len(show) else ""
    nums = "、".join(f"#{n}" for n in show)
    return False, f"以下 open bug 未分配责任人：{nums}{tail}"


def github_open_bug_rows_in_range(
    gh_token: str | None,
    date_from: str,
    date_to: str,
) -> tuple[int, int, str]:
    """
    Paginate **open** issues with label ``bug`` (PR entries excluded).

    Return ``(total_open_bug_fetched, count_in_created_range, markdown_table)``.
    ``count_in_created_range`` = issues whose **UTC calendar date** of ``created_at``
    lies in ``[date_from, date_to]`` inclusive (``YYYY-MM-DD`` strings).
    """
    all_items = _github_fetch_open_bug_issues(gh_token)

    in_range = [
        i
        for i in all_items
        if (d := _issue_created_date_utc(i)) is not None and date_from <= d <= date_to
    ]
    in_range.sort(key=lambda x: x["created_at"], reverse=True)
    row_cells: list[list[str]] = []
    for i in in_range:
        t = (i.get("title") or "").replace("|", "\\|").replace("\n", " ")
        u = (i.get("user") or {}).get("login", "")
        row_cells.append(
            [
                f"[#{i['number']}](https://github.com/vllm-project/vllm-omni/issues/{i['number']})",
                t,
                str(i["created_at"])[:10],
                "open",
                f"@{u}",
            ]
        )
    body = render_markdown_table(
        ["Issue", "Title", "Opened at", "Status", "Owner"],
        row_cells,
    )
    return len(all_items), len(in_range), body


def render_open_issues_section(
    stats_from: str,
    stats_to: str,
    gh_token: str | None,
) -> str:
    """Markdown for ``## Open issues`` block (GitHub REST, open ``label:bug`` only)."""
    github_open_error = ""
    try:
        open_total, open_range_n, issue_rows = github_open_bug_rows_in_range(
            gh_token, stats_from, stats_to
        )
    except Exception as exc:
        open_total = 0
        open_range_n = 0
        issue_rows = render_markdown_table(
            ["Issue", "Title", "Opened at", "Status", "Owner"],
            [
                [
                    "*—*",
                    "*Failed to fetch; set `GITHUB_TOKEN` or fill in manually*",
                    "*—*",
                    "*—*",
                    "*—*",
                ]
            ],
        )
        github_open_error = str(exc)

    github_open_note = (
        f" **Note:** open-bugs fetch failed (`{github_open_error}`)."
        if github_open_error
        else ""
    )
    return (
        f"## Open issues (stats window)\n\n"
        f"Open issues labeled **bug**, state **open**, **excluding PRs**, with **`created_at`** "
        f"(UTC date) in **{stats_from}** … **{stats_to}** (same as Buildkite **`--stats-from`** / "
        f"**`--stats-to`**): **{open_range_n}** (total open `bug` issues when fetched: "
        f"**{open_total}**).{github_open_note}\n\n"
        f"{issue_rows}\n"
    )


def github_ci_failure_analysis_rows(
    created_from: str,
    created_to: str,
    gh_token: str | None,
) -> tuple[int, str]:
    """
    Issues with labels ``bug`` and ``ci-failure``, ``created_at`` (UTC) in
    ``created_from`` .. ``created_to`` (inclusive, YYYY-MM-DD).

    Same date window as ``compose_full_report.py`` ``--stats-from`` / ``--stats-to``
    (Buildkite metrics window).
    """
    q = (
        f"repo:vllm-project/vllm-omni is:issue label:bug label:{CI_FAILURE_LABEL} "
        f"created:{created_from}..{created_to}"
    )
    base = "https://api.github.com/search/issues?q=" + urllib.parse.quote(q)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "vllm-omni-compose-report",
    }
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    collected: list[dict] = []
    page = 1
    while True:
        url = f"{base}&per_page=100&page={page}"
        data = http_get_json(url, headers=headers, timeout=120)
        items = data.get("items") or []
        if not items:
            break
        for i in items:
            if i.get("pull_request"):
                continue
            collected.append(i)
        if len(items) < 100:
            break
        page += 1

    collected.sort(key=lambda x: int(x.get("number", 0)), reverse=True)
    row_cells: list[list[str]] = []
    for i in collected:
        num = i["number"]
        title = (i.get("title") or "").replace("|", "\\|").replace("\n", " ")
        st = (i.get("state") or "").lower()
        status_label = "Closed" if st == "closed" else "Open"
        link = f"https://github.com/vllm-project/vllm-omni/issues/{num}"
        row_cells.append([f"[#{num}]({link})", title, status_label])
    if not row_cells:
        return 0, ""
    return len(collected), render_markdown_table(
        ["Issue #", "Title", "Status"], row_cells
    )


def render_ci_failure_section(
    stats_from: str,
    stats_to: str,
    gh_token: str | None,
) -> str:
    """
    Markdown for ``### Analysis (CI Failure)`` … (GitHub Search only; no Buildkite).

    Used by ``compose_full_report.py`` and ``patch_report_ci_failure.py``.
    """
    try:
        ci_fail_n, ci_fail_rows = github_ci_failure_analysis_rows(
            stats_from, stats_to, gh_token
        )
        ci_fail_error = ""
    except Exception as exc:
        ci_fail_n = -1
        ci_fail_rows = ""
        ci_fail_error = str(exc)

    ci_filter_note = (
        f"**Filter:** `label:bug` **and** `label:{CI_FAILURE_LABEL}`, "
        f"`created` (UTC) **{stats_from}** … **{stats_to}** (same window as Buildkite metrics / "
        f"`--stats-from` / `--stats-to`). "
        f"**Cross-check:** "
        f"[issues · bug + ci-failure](https://github.com/vllm-project/vllm-omni/issues?q=is%3Aissue+label%3Abug+label%3Aci-failure)."
    )
    if ci_fail_error:
        return (
            f"### Analysis (CI Failure)\n\n"
            f"*GitHub Search API unavailable: {ci_fail_error}.* Fill in manually per "
            f"[references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md) "
            f"from [open bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) "
            f"and [closed bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug).\n"
        )
    if ci_fail_n == 0:
        return (
            f"### Analysis (CI Failure)\n\n"
            f"{ci_filter_note}\n\n"
            f"*No matching issues in this date range.*\n"
        )
    return (
        f"### Analysis (CI Failure)\n\n"
        f"{ci_filter_note}"
        f" **Rows in table:** {ci_fail_n}.\n\n"
        f"{ci_fail_rows}\n"
    )


def github_issue_tracking_local_test_rows(
    created_from: str,
    created_to: str,
    gh_token: str | None,
) -> tuple[int, str]:
    """
    GitHub Search: ``label:ci-failure``, ``created`` in date range, **title** contains
    ``local test``. Excludes PR entries; post-filters title case-insensitively.
    """
    q = (
        f'repo:vllm-project/vllm-omni is:issue label:{CI_FAILURE_LABEL} '
        f"created:{created_from}..{created_to} "
        f'in:title "local test"'
    )
    base = "https://api.github.com/search/issues?q=" + urllib.parse.quote(q)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "vllm-omni-compose-report",
    }
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    collected: list[dict] = []
    page = 1
    while True:
        url = f"{base}&per_page=100&page={page}"
        data = http_get_json(url, headers=headers, timeout=120)
        items = data.get("items") or []
        if not items:
            break
        for i in items:
            if i.get("pull_request"):
                continue
            title = (i.get("title") or "").lower()
            if "local test" not in title:
                continue
            collected.append(i)
        if len(items) < 100:
            break
        page += 1

    collected.sort(key=lambda x: int(x.get("number", 0)), reverse=True)
    row_cells: list[list[str]] = []
    for i in collected:
        num = i["number"]
        title = (i.get("title") or "").replace("|", "\\|").replace("\n", " ")
        st = (i.get("state") or "").lower()
        status_label = "closed" if st == "closed" else "open"
        ca = str(i.get("created_at") or "")[:10]
        link = f"https://github.com/vllm-project/vllm-omni/issues/{num}"
        row_cells.append([f"[#{num}]({link})", title, status_label, ca])
    body = (
        render_markdown_table(
            ["Issue", "Title", "State", "Created (UTC date)"],
            row_cells,
        )
        if row_cells
        else ""
    )
    return len(collected), body


def render_issue_tracking_section(
    stats_from: str,
    stats_to: str,
    gh_token: str | None,
) -> str:
    """Markdown for ``## Issue tracking`` (ci-failure + *local test* in title)."""
    try:
        n, table_rows = github_issue_tracking_local_test_rows(
            stats_from, stats_to, gh_token
        )
        err_note = ""
    except Exception as exc:
        n = -1
        table_rows = ""
        err_note = str(exc)

    filt = (
        f"**Filter:** GitHub Search — `label:{CI_FAILURE_LABEL}`, **`created`** (UTC) "
        f"**{stats_from}** … **{stats_to}**, **title** contains **`local test`** (case-insensitive). "
        f"**Cross-check:** "
        f"[search · ci-failure + local in title](https://github.com/search?q=repo%3Avllm-project%2Fvllm-omni+is%3Aissue+label%3Aci-failure+local+test+in%3Atitle&type=issues).\n\n"
    )
    if err_note:
        return (
            "## Issue tracking\n\n"
            f"{filt}"
            f"*GitHub Search API 不可用: {err_note}。* 请配置 `GITHUB_TOKEN` / `GH_TOKEN` 后重试，"
            f"或手工检索上述链接。\n"
        )
    if n == 0:
        return (
            "## Issue tracking\n\n"
            f"{filt}"
            "*本窗口内无匹配 issue。*\n"
        )
    return (
        "## Issue tracking\n\n"
        f"{filt}"
        f"*Matching issues: **{n}**.*\n\n"
        f"{table_rows}\n"
    )


def extract_common_stack_from_matrix(skill_dir: Path) -> str:
    """Body text under ``## Common stack (all rows)`` in ``local-test-matrix.md``."""
    ref = skill_dir / "references" / "local-test-matrix.md"
    if not ref.is_file():
        return "*(`references/local-test-matrix.md` not found.)*\n"
    raw = ref.read_text(encoding="utf-8")
    m = re.search(
        r"(?ms)^## Common stack \(all rows\)\s*\n(.*?)(?=^\#\# |\Z)",
        raw,
    )
    if not m:
        return "*未找到 `## Common stack (all rows)` 段落；请检查 reference。*\n"
    body = (m.group(1) or "").strip()
    return (body + "\n") if body else "*（Common stack 正文为空）*\n"


def _gpu_log_placeholder(gpu_flag: str) -> str:
    return (
        f"*未传入 `{gpu_flag}`：无与 nightly 本地章节同结构的汇总表。* "
        f"请将集群/单机上的 `nightly_jobs` 日志根目录传给 compose（见 `--help`）。"
    )


def build_h100_ci_markdown_body(
    *,
    build_table_md: str,
    passed: int,
    failed: int,
    skipped: int,
    failed_section: str,
) -> str:
    return (
        f"#### Build\n\n{build_table_md}\n\n"
        f"#### Summary (reportable jobs only)\n\n"
        f"- **Passed**: {passed} jobs\n"
        f"- **Failed / broken**: {failed} jobs\n"
        f"- **Skipped / blocked / not_run**: {skipped} (if any)\n\n"
        f"#### Failed test jobs (if any)\n\n{failed_section}\n"
    )


def render_test_result_section(
    skill_dir: Path,
    *,
    log_h200: Path | None,
    log_h800: Path | None,
    log_a100: Path | None,
    h100_ci_markdown: str,
) -> str:
    chunks: list[str] = [
        "## Test Result",
        "",
        "布局说明：`### Common stack` 来自 reference；"
        "`### H200` / `### H800` / `### A100` 与 **nightly** 报告中本地 **Summary** 分组一致（需传入对应 `--log-dir-*`）；"
        "`### H100` 为 **Buildkite scheduled nightly**（Build / Summary / 失败 Job 表；不含 per-job pytest 与 bug+ci-failure 分析）。",
        "",
        "### Common stack (all rows)",
        "",
        extract_common_stack_from_matrix(skill_dir).rstrip(),
        "",
        "### H200",
        "",
    ]
    chunks.append(
        markdown_local_summary_from_log_dir(log_h200)
        if log_h200
        else _gpu_log_placeholder("--log-dir-h200")
    )
    chunks.extend(["", "### H800", ""])
    chunks.append(
        markdown_local_summary_from_log_dir(log_h800)
        if log_h800
        else _gpu_log_placeholder("--log-dir-h800")
    )
    chunks.extend(["", "### A100", ""])
    chunks.append(
        markdown_local_summary_from_log_dir(log_a100)
        if log_a100
        else _gpu_log_placeholder("--log-dir-a100")
    )
    chunks.extend(
        [
            "",
            "### H100（CI — Buildkite scheduled nightly）",
            "",
            h100_ci_markdown.rstrip(),
            "",
        ]
    )
    return "\n".join(chunks)


def render_test_conclusion_section() -> str:
    """``## 测试结论`` + placeholder for interactive widget (HTML) or static MD."""
    return f"## 测试结论\n\n{RELEASE_CONCLUSION_PLACEHOLDER}\n\n"


def run_script(py: Path, args: list[str], cwd: Path, env: dict[str, str]) -> str:
    cmd = [sys.executable, str(py)] + args
    child_env = dict(env)
    child_env.setdefault("PYTHONIOENCODING", "utf-8")
    if sys.platform == "win32":
        child_env.setdefault("PYTHONUTF8", "1")
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=child_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=3600,
    )
    if p.returncode != 0:
        sys.stderr.write(p.stderr or "")
        sys.exit(f"Command failed ({p.returncode}): {' '.join(cmd)}")
    return p.stdout or ""


def extract_ci_markdown(stats_stdout: str) -> str:
    heading = "## Metrics overview"
    if heading not in stats_stdout:
        return stats_stdout.strip()
    part = stats_stdout.split(heading, 1)[1]
    if "Done." in part:
        part = part.split("Done.", 1)[0]
    return (heading + part).strip()


def _job_scope_ref_lookup_key(cell: str) -> str:
    """First column of a scope table row -> lookup key (matches Buildkite `job.name`)."""
    t = (cell or "").replace("**", "").strip()
    if " (" in t:
        t = t.split(" (", 1)[0].strip()
    return t


def load_job_scope_lookup(ref_path: Path) -> dict[str, str]:
    """
    Parse pipe tables in ``ci-job-test-scope.md`` -> job name -> scope / intent (second column).

    Skips separator rows and header cells ``Typical job name`` / ``Source``.
    """
    if not ref_path.is_file():
        return {}
    lookup: dict[str, str] = {}
    for line in ref_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        parts = [p.strip() for p in s.split("|")[1:-1]]
        if len(parts) < 2:
            continue
        k_raw, scope = parts[0], parts[1]
        if not k_raw or re.match(r"^:?-+:?$", k_raw):
            continue
        key = _job_scope_ref_lookup_key(k_raw)
        low = key.lower()
        if low in ("typical job name", "source"):
            continue
        if not key:
            continue
        lookup[key] = scope.replace("|", "/")
    return lookup


def render_job_scope_section(build: dict, build_no: int, skill_dir: Path) -> str:
    """
    ``## Test content (job scope)``: one row per **reportable** job in this nightly
    (same rule as Summary: omit ``Upload * Pipeline``), scope text from reference lookup.
    """
    ref = skill_dir / "references" / "ci-job-test-scope.md"
    lookup = load_job_scope_lookup(ref)
    jobs = build.get("jobs") or []
    reportable = [
        j
        for j in jobs
        if not UPLOAD_PIPELINE_RE.match((j.get("name") or "").strip())
    ]
    reportable.sort(key=lambda x: (x.get("name") or ""))
    missing = "*—* *(not in reference; add to [references/ci-job-test-scope.md](references/ci-job-test-scope.md) or see log)*"
    rows: list[list[str]] = []
    for j in reportable:
        name = (j.get("name") or "").replace("|", "/")
        st = (j.get("state") or "").replace("|", "/")
        jid = j.get("id") or ""
        link = f"[open](https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}#{jid})"
        scope = lookup.get(name.strip(), missing)
        rows.append([name, st, link, scope])
    table = render_markdown_table(
        ["Job (this nightly)", "State", "Step link", "Scope / intent"],
        rows,
    )
    return (
        "## Test content (job scope)\n\n"
        f"Jobs match **scheduled nightly** "
        f"[#{build_no}](https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}) "
        "(**reportable** only: `Upload * Pipeline` omitted). "
        "**Scope / intent** is looked up from "
        "[references/ci-job-test-scope.md](references/ci-job-test-scope.md) "
        "by exact job name (see categorized reference for maintenance).\n\n"
        f"{table}\n"
    )


PREVIEW_BUILD_NO = 12880


def preview_report_markdown(
    skill_dir: Path,
    *,
    stats_from: str,
    stats_to: str,
    build_no: int = PREVIEW_BUILD_NO,
) -> str:
    """
    Same section layout as the live **release** report (minus any hand-only sections), but **no network** and no subprocess calls.

    Embeds real ``references/local-test-matrix.md`` Common stack when present.
    """
    conclusion = render_test_conclusion_section()
    ci_md = (
        "## Metrics overview\n\n"
        "*本段为 **预览假数据**：未运行 `buildkite_build_stats.py`，下列数值仅为版式演示。*\n\n"
        + render_markdown_table(
            ["指标（示例）", "数值"],
            [
                ["**Stats window**", f"`{stats_from}` … `{stats_to}`"],
                ["**Pipeline**", f"`{ORG}/{PIPELINE}` · branch `{BRANCH}`"],
                ["**Job success rate（窗口内）**", "97.4%"],
                ["**UT 覆盖率（示例）**", "84.6%"],
                ["**Bug 平均首次响应（h）**", "6.2"],
                ["**本窗口新建 bug 数（示例）**", "5"],
                ["**L4 / nightly 触达**", "✓ 示例：最近 7 次定时构建均完成"],
                [
                    "**说明**",
                    "去掉 `--preview` 并配置 token 后将替换为 `buildkite_build_stats.py` 真实输出。",
                ],
            ],
        )
    )

    demo_link_a = (
        f"https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}#step-demo-jid-a"
    )
    demo_link_b = (
        f"https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}#step-demo-jid-b"
    )

    build_table_md = render_markdown_table(
        ["Field", "Value"],
        [
            [
                "**Build**",
                f"[{build_no}](https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no})",
            ],
            ["**Branch**", BRANCH],
            [
                "**Commit**",
                "`c0ffee1` ([full](https://github.com/vllm-project/vllm-omni/commit/c0ffee1deadbeefcafe000000000000000000001))",
            ],
        ],
    )

    failed_section = render_markdown_table(
        ["Step / Job", "State", "Notes", "Step link"],
        [
            [
                "L2_Diffusion_Accuracy_Test",
                "failed",
                "AssertionError: max diff 0.08 > 0.05 *(示例)*",
                f"[open]({demo_link_a})",
            ],
            [
                "L3_Merge_Example_Suite",
                "failed",
                "Timeout after 45m *(示例)*",
                f"[open]({demo_link_b})",
            ],
        ],
    )

    h100_body = build_h100_ci_markdown_body(
        build_table_md=build_table_md,
        passed=11,
        failed=2,
        skipped=1,
        failed_section=failed_section,
    )

    test_result = render_test_result_section(
        skill_dir,
        log_h200=None,
        log_h800=None,
        log_a100=None,
        h100_ci_markdown=h100_body,
    )

    issue_tracking = (
        "## Issue tracking\n\n"
        "**Filter:** GitHub Search — `label:ci-failure`, **`created`** (UTC) "
        f"**{stats_from}** … **{stats_to}**, **title** contains **`local test`**。\n\n"
        "*以下为 **预览假数据**（列与正式报告一致）。*\n\n"
        "*Matching issues: **2**.*\n\n"
        + render_markdown_table(
            ["Issue", "Title", "State", "Created (UTC date)"],
            [
                [
                    "[#10042](https://github.com/vllm-project/vllm-omni/issues/10042)",
                    "local test · H100 diffusion batch flaky",
                    "open",
                    stats_to,
                ],
                [
                    "[#10018](https://github.com/vllm-project/vllm-omni/issues/10018)",
                    "Regression in local test matrix for A100 path",
                    "closed",
                    stats_from,
                ],
            ],
        )
        + "\n"
    )

    open_issues_block = (
        "## Open issues (stats window)\n\n"
        f"Open issues labeled **bug**，**`created_at`** 落在 **{stats_from}** … **{stats_to}** "
        "（*以下为预览假数据；正式发布为 GitHub 分页结果。*）\n\n"
        + render_markdown_table(
            ["Issue", "Title", "Opened at", "Status", "Owner"],
            [
                [
                    "[#10055](https://github.com/vllm-project/vllm-omni/issues/10055)",
                    "OOM when loading Qwen-Omni with FP8 on 40GB",
                    "2026-05-14",
                    "open",
                    "@alice-preview",
                ],
                [
                    "[#10042](https://github.com/vllm-project/vllm-omni/issues/10042)",
                    "Intermittent timeout on L2 diffusion accuracy",
                    stats_to,
                    "open",
                    "@bob-preview",
                ],
                [
                    "[#10030](https://github.com/vllm-project/vllm-omni/issues/10030)",
                    "Docs: wrong env var for TEE cache",
                    "2026-05-10",
                    "open",
                    "@carol-preview",
                ],
            ],
        )
        + "\n"
    )

    return f"""# vLLM-Omni Test Report - Scheduled Nightly

* **Preview mode:** 无 Buildkite / GitHub / pytest 日志拉取；下列内容仅供版式预览。*

{conclusion}{ci_md}

{test_result}
{issue_tracking}{open_issues_block}
## Data source

- **Mode:** `compose_full_report.py --preview` (sample tables only)
- **Test Result:** Common stack 自 `references/local-test-matrix.md`；H200/H800/A100 可传 `--log-dir-*`；H100 为 Buildkite 块
- **Issue tracking:** `label:ci-failure` + title **local test**；Open issues 仍为 `label:bug` 分页
- Live report: `buildkite_build_stats.py`, GitHub REST/Search
"""


def local_testing_markdown(skill_dir: Path) -> str:
    """Backward-compatible stub for patch scripts: Test Result without log dirs, dummy H100."""
    return render_test_result_section(
        skill_dir,
        log_h200=None,
        log_h800=None,
        log_a100=None,
        h100_ci_markdown=(
            "*（此处应放入完整 H100 / Buildkite 块；请运行 `compose_full_report.py` 重新生成报告。）*\n"
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compose full vllm-omni test report (HTML default; optional Markdown).",
    )
    parser.add_argument(
        "--format",
        choices=("html", "markdown"),
        default="html",
        help="Output format (default: html). Use markdown for patch_report_*.py workflows.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "Output path. Default: <skill-dir>/vllm-omni-test-report-YYYY-MM-DD.html "
            "or .md when --format markdown."
        ),
    )
    parser.add_argument(
        "--stats-from",
        default=None,
        help=(
            "buildkite_build_stats.py --from (UTC YYYY-MM-DD). "
            "Default: first day of current UTC month (month-to-date, matches SKILL)."
        ),
    )
    parser.add_argument(
        "--stats-to",
        default=None,
        help="buildkite_build_stats.py --to (default: today UTC)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help=(
            "Emit sample data only (no Buildkite, GitHub, or pytest log fetch). "
            "Default output: vllm-omni-test-report-preview-YYYY-MM-DD.html"
        ),
    )
    parser.add_argument(
        "--log-dir-h200",
        type=Path,
        default=None,
        help=(
            "Optional. Root directory of nightly job logs for **Test Result → H200** "
            "(same layout as nightly `nightly_jobs`; see references/nightly-local-log-layout.md)."
        ),
    )
    parser.add_argument(
        "--log-dir-h800",
        type=Path,
        default=None,
        help="Optional. Log root for **Test Result → H800** (same layout as --log-dir-h200).",
    )
    parser.add_argument(
        "--log-dir-a100",
        type=Path,
        default=None,
        help="Optional. Log root for **Test Result → A100** (same layout as --log-dir-h200).",
    )
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    scripts_dir = skill_dir / "scripts"

    token = (
        os.environ.get("BUILDKITE_API_TOKEN") or os.environ.get("BUILDKITE_TOKEN") or ""
    ).strip()
    if not args.preview and not token:
        print(
            "BUILDKITE_API_TOKEN or BUILDKITE_TOKEN is not set.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.preview:
        today_d = datetime.now(timezone.utc).date()
        today_utc = today_d.isoformat()
        stats_to = args.stats_to or today_utc
        stats_from = args.stats_from or today_d.replace(day=1).isoformat()
        md = preview_report_markdown(skill_dir, stats_from=stats_from, stats_to=stats_to)
        out_path = args.out
        if out_path is None:
            ext = ".html" if args.format == "html" else ".md"
            out_path = skill_dir / f"vllm-omni-test-report-preview-{today_utc}{ext}"
        else:
            out_path = Path(args.out)
        if args.format == "html":
            archive_name = out_path.with_suffix(".md").name
            out_path.write_text(
                convert_release_report_markdown(
                    md,
                    archive_download_name=archive_name,
                    l2_l3_row_ok=True,
                    l2_l3_row_detail="",
                    critical_row_ok=True,
                    critical_row_detail="",
                    assignee_row_ok=True,
                    assignee_row_detail="（预览：未请求 GitHub / 未跑 Buildkite 门控，自动行占位为通过）",
                ),
                encoding="utf-8",
            )
        else:
            out_path.write_text(
                materialize_release_conclusion_in_markdown(
                    md,
                    l2_l3_row_ok=True,
                    l2_l3_row_detail="",
                    critical_row_ok=True,
                    critical_row_detail="",
                    assignee_row_ok=True,
                    assignee_row_detail="（预览：未请求 GitHub / 未跑 Buildkite 门控，自动行占位为通过）",
                ),
                encoding="utf-8",
            )
        print(f"Wrote {out_path}")
        return

    today_d = datetime.now(timezone.utc).date()
    today_utc = today_d.isoformat()
    stats_to = args.stats_to or today_utc
    stats_from = args.stats_from or today_d.replace(day=1).isoformat()

    build_no = latest_scheduled_nightly_number(token)
    build_url = (
        f"https://api.buildkite.com/v2/organizations/{ORG}/pipelines/"
        f"{PIPELINE}/builds/{build_no}"
    )
    build = http_json(build_url, token)
    assert isinstance(build, dict)

    jobs = build.get("jobs") or []
    reportable = [j for j in jobs if not UPLOAD_PIPELINE_RE.match((j.get("name") or "").strip())]
    states = [(j.get("state") or "").lower() for j in reportable]
    passed = sum(1 for s in states if s == "passed")
    failed = sum(1 for s in states if s in ("failed", "broken"))
    skipped = sum(1 for s in states if s in ("skipped", "not_run", "blocked"))

    commit = build.get("commit") or ""
    short = commit[:7] if len(commit) >= 7 else commit
    env = os.environ.copy()

    stats_raw = run_script(
        scripts_dir / "buildkite_build_stats.py",
        ["--from", stats_from, "--to", stats_to, "--markdown"],
        skill_dir,
        env,
    )
    ci_md = extract_ci_markdown(stats_raw)

    gh_token = (
        os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    ).strip() or None

    try:
        from buildkite_build_stats import l2_l3_ready_merge_gate

        l2_l3_row_ok, l2_l3_row_detail = l2_l3_ready_merge_gate(token)
    except ImportError:
        l2_l3_row_ok, l2_l3_row_detail = (
            False,
            "无法导入 buildkite_build_stats（请 pip install requests）",
        )
    except Exception as exc:
        l2_l3_row_ok, l2_l3_row_detail = False, f"L2&L3 检测失败（{exc}）"

    critical_row_ok, critical_row_detail = no_open_critical_labeled_issues(gh_token)
    assignee_row_ok, assignee_row_detail = open_bug_assignees_all_assigned(gh_token)
    out_path = args.out
    if out_path is None:
        ext = ".html" if args.format == "html" else ".md"
        out_path = skill_dir / f"vllm-omni-test-report-{today_utc}{ext}"
    else:
        out_path = Path(args.out)

    failed_jobs_rows: list[list[str]] = []
    for j in reportable:
        st = (j.get("state") or "").lower()
        if st in ("failed", "broken"):
            name = (j.get("name") or "").replace("|", "/")
            jid = j.get("id") or ""
            link = f"https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}#{jid}"
            failed_jobs_rows.append([name, st, "See step log", f"[open]({link})"])

    failed_section = (
        render_markdown_table(
            ["Step / Job", "State", "Notes", "Step link"],
            failed_jobs_rows,
        )
        if failed_jobs_rows
        else "*None.*"
    )

    build_table_md = render_markdown_table(
        ["Field", "Value"],
        [
            [
                "**Build**",
                f"[{build_no}](https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no})",
            ],
            ["**Branch**", build.get("branch") or "main"],
            [
                "**Commit**",
                f"`{short}` ([full](https://github.com/vllm-project/vllm-omni/commit/{commit}))",
            ],
        ],
    )

    conclusion = render_test_conclusion_section()
    h100_body = build_h100_ci_markdown_body(
        build_table_md=build_table_md,
        passed=passed,
        failed=failed,
        skipped=skipped,
        failed_section=failed_section,
    )
    test_result = render_test_result_section(
        skill_dir,
        log_h200=args.log_dir_h200,
        log_h800=args.log_dir_h800,
        log_a100=args.log_dir_a100,
        h100_ci_markdown=h100_body,
    )
    issue_tracking_block = render_issue_tracking_section(
        stats_from, stats_to, gh_token
    )
    open_issues_block = render_open_issues_section(stats_from, stats_to, gh_token)

    md = f"""# vLLM-Omni Test Report - Scheduled Nightly

{conclusion}{ci_md}

{test_result}
{issue_tracking_block}{open_issues_block}
## Data source

- **测试结论（自动）：** (1) Buildkite **ready**（non-main）与 **merge**（main 非 nightly/weekly）各自**最近一次已结束**构建中无 `failed`/`broken` job（与 Metrics「ready / merge」bucket 同分类）；(2) 无 open **`critical`**；(3) open **`label:bug`** 均有 assignee
- **Test Result:** Common stack from `references/local-test-matrix.md`; H200/H800/A100 via `--log-dir-h200` / `--log-dir-h800` / `--log-dir-a100` (nightly-style Summary); H100 = Buildkite scheduled nightly (this build #{build_no}: **Build** 表仅链接/分支/commit + Summary + failed jobs)
- **Issue tracking:** GitHub Search — `label:ci-failure`, **`local test` in:title**, `created` in `{stats_from}`..`{stats_to}` (UTC)
- **Open issues:** REST `label:bug`, `created_at` UTC date in `{stats_from}`..`{stats_to}`
- Buildkite API: `{ORG}/{PIPELINE}` branch `main`
- `scripts/buildkite_build_stats.py --from {stats_from} --to {stats_to} --markdown` (**bugs (first response, …)** = GitHub `label:bug` issues with `created_at` UTC date in the same `--from`..`--to` window)
"""
    if args.format == "html":
        archive_name = out_path.with_suffix(".md").name
        out_path.write_text(
            convert_release_report_markdown(
                md,
                archive_download_name=archive_name,
                l2_l3_row_ok=l2_l3_row_ok,
                l2_l3_row_detail=l2_l3_row_detail,
                critical_row_ok=critical_row_ok,
                critical_row_detail=critical_row_detail,
                assignee_row_ok=assignee_row_ok,
                assignee_row_detail=assignee_row_detail,
            ),
            encoding="utf-8",
        )
    else:
        out_path.write_text(
            materialize_release_conclusion_in_markdown(
                md,
                l2_l3_row_ok=l2_l3_row_ok,
                l2_l3_row_detail=l2_l3_row_detail,
                critical_row_ok=critical_row_ok,
                critical_row_detail=critical_row_detail,
                assignee_row_ok=assignee_row_ok,
                assignee_row_detail=assignee_row_detail,
            ),
            encoding="utf-8",
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
