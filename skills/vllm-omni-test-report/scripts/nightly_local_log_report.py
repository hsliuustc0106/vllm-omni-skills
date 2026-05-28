#!/usr/bin/env python3
"""
Parse pytest-style logs under logs/nightly_jobs (or --log-dir) and emit HTML or Markdown.

Used for **report type nightly** in vllm-omni-test-report. Discovery rules:
../references/nightly-local-log-layout.md
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from pytest_log_parse import (
    extract_pytest_counts,
    extract_pytest_duration_display,
    parse_pytest_log,
)
from nightly_job_pytest_table import (
    ORG,
    PIPELINE,
    collect_nightly_job_log_analyses,
    fetch_nightly_build,
)
from nightly_perf_manual_xlsx import (
    PERF_MANUAL_FILENAME,
    load_perf_manual_with_compare,
)
from kanban_assets_perf_summary import _build_perf_rows, build_assets_perf_summary
from report_html_theme import EDITORIAL_THEME_CSS


def _buildkite_token() -> str | None:
    tok = (
        os.environ.get("BUILDKITE_API_TOKEN") or os.environ.get("BUILDKITE_TOKEN") or ""
    ).strip()
    return tok or None


# Inline SVG paths (24×24, stroke) for HTML report headings — no external assets.
_SVG_CLIPBOARD = (
    '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
    '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>'
)
_SVG_CLOUD = '<path d="M18 10h-1.26A8 8 0 1 0 9 22h9a5 5 0 1 0 0-12z"/>'
_SVG_SERVER = (
    '<rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>'
    '<rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>'
    '<line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'
)
_SVG_ALERT = (
    '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
    '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
)
_SVG_LIST = '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>'
_SVG_CODE = '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>'
_SVG_MSG = '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
_SVG_SPARK = '<path d="m12 3-1.9 5.8L4 10l5.8 1.9L12 18l1.9-5.8L20 10l-6.2-1.9L12 3z"/>'
_SVG_LOG = (
    '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
    '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>'
    '<line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/>'
)
# Plus-in-circle (new issue)
_SVG_PLUS_ISSUE = (
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>'
)
# Subcollapsible section icons (summary row)
_SVG_CHART_BARS = (
    '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>'
    '<line x1="6" y1="20" x2="6" y2="14"/>'
)

VLLM_OMNI_REPO = "https://github.com/vllm-project/vllm-omni"
VLLM_OMNI_BUG_ISSUE_TEMPLATE = "400-bug-report.yml"

# Total raw log bytes (per failing local job) embeddable in HTML; larger logs get a notice + paths only.
FULL_LOG_EMBED_MAX_BYTES = 2 * 1024 * 1024
DEFAULT_KANBAN_ASSETS_DIR = Path(
    os.environ.get("KANBAN_ASSETS_DIR", "").strip()
).resolve() if os.environ.get("KANBAN_ASSETS_DIR", "").strip() else None
DEFAULT_KANBAN_REPO_ROOT = Path(
    os.environ.get("KANBAN_REPO_ROOT", "").strip()
).resolve() if os.environ.get("KANBAN_REPO_ROOT", "").strip() else None


@dataclass
class KanbanAssetsConfig:
    assets_dir: Path | None
    repo_root: Path | None
    expected_remote: str | None = None
    expected_branch: str | None = None
    raw_root: Path | None = None
    refresh_from_raw: bool = False
    refresh_note: str | None = None
    refresh_warnings: list[str] = field(default_factory=list)


@dataclass
class LocalPerfResultConfig:
    result_root: Path | None = None


def _default_local_perf_result_root(kanban_repo_root: Path | None) -> Path | None:
    if kanban_repo_root is None:
        return None
    candidate = (kanban_repo_root / "data/local_nightly_raw").resolve()
    return candidate if candidate.is_dir() else None


# Keep this list aligned with vllm-omni-kanban/scripts/mkdocs_hooks.py and
# the maintenance note in SKILL.md.
KANBAN_RAW_MODEL_SYNCS: tuple[tuple[str, str], ...] = (
    ("qwen3omni", "qwen3_omni"),
    ("qwen3tts", "qwen3_tts"),
    ("qwen_image", "qwen_image"),
    ("qwen_image_edit", "qwen_image_edit"),
    ("qwen_image_edit_2509", "qwen_image_edit_2509"),
    ("wan22", "wan22"),
)
KANBAN_RAW_PATTERNS = (
    "result_test_*.json",
    "diffusion_result_*.json",
    "benchmark_results_*.json",
)


def _svg_icon(inner: str, *, size: int = 20, extra_class: str = "") -> str:
    c = f"ico {extra_class}".strip()
    return (
        f'<svg class="{c}" width="{size}" height="{size}" viewBox="0 0 24 24" '
        'aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</svg>"
    )


def _heading_html(
    tag: str,
    icon_paths: str,
    label_inner: str,
    *,
    sub: str | None = None,
    klass: str | None = None,
) -> str:
    """`label_inner` / `sub` are trusted HTML fragments (callers must escape)."""
    attrs = ""
    if klass:
        attrs = f' class="{html.escape(klass)}"'
    sub_html = ""
    if sub:
        sub_html = f'<span class="heading-sub">{sub}</span>'
    return (
        f"<{tag}{attrs}>"
        '<span class="heading-row">'
        f'<span class="heading-ico">{_svg_icon(icon_paths, size=22)}</span>'
        f'<span class="heading-text"><span class="heading-label">{label_inner}</span>{sub_html}</span>'
        "</span>"
        f"</{tag}>"
    )


def _table_wrap(table_html: str) -> str:
    return f'<div class="table-scroll">{table_html}</div>'


def _details_subcard(
    title: str,
    body_html: str,
    *,
    open_default: bool = False,
    details_class: str = "",
    icon_paths: str | None = None,
) -> str:
    """Collapsible sub-section inside Buildkite Test / Local Test cards."""
    op = " open" if open_default else ""
    extra = f" {details_class.strip()}" if details_class.strip() else ""
    te = html.escape(title)
    if icon_paths:
        ico = _svg_icon(icon_paths, size=18, extra_class="report-subcard-ico")
        label = (
            f'<span class="report-subcard-summary-inner">{ico}'
            f'<span class="report-subcard-title">{te}</span></span>'
        )
    else:
        label = f'<span class="report-subcard-title">{te}</span>'
    return (
        f'<details class="report-subcard{extra}"{op}>'
        f'<summary class="report-subcard-summary">{label}</summary>'
        f'<div class="report-subcard-body">{body_html}</div>'
        "</details>"
    )


def _github_issue_button_cell() -> str:
    return (
        '<td class="issue-action-cell">'
        '<button type="button" class="btn-github-issue">'
        f'{_svg_icon(_SVG_PLUS_ISSUE, size=17, extra_class="btn-issue-ico")}'
        '<span class="btn-issue-text">File issue</span>'
        "</button></td>"
    )


def _github_issue_modal_and_script() -> str:
    """Modal + client script: open GitHub bug template, prefilled title; body copied to match upstream form."""
    tmpl_url = f"{VLLM_OMNI_REPO}/blob/main/.github/ISSUE_TEMPLATE/{VLLM_OMNI_BUG_ISSUE_TEMPLATE}"
    issue_new = f"{VLLM_OMNI_REPO}/issues/new"
    return f"""
<div id="gh-issue-modal" class="gh-modal" hidden aria-hidden="true">
  <div class="gh-modal-backdrop" tabindex="-1"></div>
  <div class="gh-modal-panel" role="dialog" aria-modal="true" aria-labelledby="gh-issue-dialog-title">
    <header class="gh-modal-head">
      <h2 id="gh-issue-dialog-title">File a vllm-omni bug report</h2>
      <button type="button" class="gh-modal-x" id="gh-issue-close" aria-label="Close">×</button>
    </header>
    <p class="gh-modal-hint">Body sections follow the upstream
      <a href="{html.escape(tmpl_url)}" target="_blank" rel="noopener noreferrer">bug report template</a>
      (<code>{html.escape(VLLM_OMNI_BUG_ISSUE_TEMPLATE)}</code>).
      For <strong>Buildkite</strong> rows, the body uses <code>ci env</code> and tries to fill <strong>vllm / vllm-omni</strong>
      versions by scanning the step log; paste anything missing from the build log if needed.
      Click <strong>Open GitHub</strong> (template and title are pre-filled), then paste the Markdown below into
      <strong>Describe the bug</strong>. Redact secrets before submitting.</p>
    <textarea id="gh-issue-body-text" class="gh-issue-textarea" rows="20" spellcheck="false"></textarea>
    <footer class="gh-modal-actions">
      <button type="button" class="btn-gh-copy" id="gh-issue-copy">Copy body</button>
      <a class="btn-gh-open" id="gh-issue-open" href="{html.escape(issue_new)}" target="_blank" rel="noopener noreferrer">Open GitHub</a>
    </footer>
  </div>
</div>
<script>
(function () {{
  var modal = document.getElementById("gh-issue-modal");
  var ta = document.getElementById("gh-issue-body-text");
  var openA = document.getElementById("gh-issue-open");
  var copyBtn = document.getElementById("gh-issue-copy");
  var closeBtn = document.getElementById("gh-issue-close");
  var backdrop = modal ? modal.querySelector(".gh-modal-backdrop") : null;
  if (!modal || !ta || !openA || !copyBtn || !closeBtn || !backdrop) return;
  var issueBase = {json.dumps(issue_new)};
  var bugTemplate = {json.dumps(VLLM_OMNI_BUG_ISSUE_TEMPLATE)};

  function gatherRow(btn) {{
    var tr = btn.closest("tr");
    if (!tr || !tr.cells || tr.cells.length < 5) return null;
    var ctx = tr.getAttribute("data-report-context") || "";
    var node = tr.cells[0].innerText.trim();
    var reason = tr.cells[1].innerText.trim();
    var analysis = tr.cells[2].innerText.trim();
    var pre = tr.cells[3].querySelector(".log-excerpt");
    var excerpt = pre ? pre.innerText : "";
    var isErr = node.indexOf("(ERROR)") !== -1;
    var env = tr.getAttribute("data-issue-env") || "local";
    var vllmVer = tr.getAttribute("data-vllm-version") || "";
    var omniVer = tr.getAttribute("data-vllm-omni-version") || "";
    var buildCommit = tr.getAttribute("data-build-commit") || "";
    return {{
      ctx: ctx, node: node, reason: reason, analysis: analysis, excerpt: excerpt, isErr: isErr,
      env: env, vllmVer: vllmVer, omniVer: omniVer, buildCommit: buildCommit,
    }};
  }}

  function buildMarkdown(d) {{
    var kind = d.isErr ? "pytest ERROR" : "pytest FAILED";
    var analysisNote;
    if (d.analysis && d.analysis.trim()) {{
      analysisNote = [
        "**Automated analysis (from report, not copied):**",
        "The HTML report may include a short heuristic summary in another language in the Analysis column.",
        "Please restate the failure in English for maintainers if you rely on that text.",
        "",
      ].join("\\n");
    }} else {{
      analysisNote = [
        "**Automated analysis:**",
        "None in report.",
        "",
      ].join("\\n");
    }}

    var envSection;
    if (d.env === "ci") {{
      envSection = [
        "### Your current environment",
        "",
        "```text",
        "ci env",
        "```",
        "",
      ].join("\\n");
    }} else {{
      envSection = [
        "### Your current environment",
        "",
        "*(Local nightly logs — add `python collect_env.py` output here if useful.)*",
        "",
        "```text",
        "(pending -- paste collect_env.py output here)",
        "```",
        "",
      ].join("\\n");
    }}

    var vllmLine, omniLine;
    if (d.env === "ci") {{
      vllmLine = (d.vllmVer && d.vllmVer.trim()) ? d.vllmVer.trim() : "(not found in Buildkite step log)";
      if (d.omniVer && d.omniVer.trim()) {{
        omniLine = d.omniVer.trim();
      }} else if (d.buildCommit && d.buildCommit.trim()) {{
        omniLine = d.buildCommit.trim();
      }} else {{
        omniLine = "(not found in Buildkite step log)";
      }}
    }} else {{
      vllmLine = "(pending)";
      omniLine = "(pending)";
    }}

    return [
      envSection,
      "### Your code version",
      "",
      "The commit id or version of vllm",
      "",
      "```text",
      vllmLine,
      "```",
      "",
      "The commit id or version of vllm-omni",
      "",
      "```text",
      omniLine,
      "```",
      "",
      "### 🐛 Describe the bug",
      "",
      "**Report source:** " + d.ctx,
      "**Failure kind:** " + kind,
      "**Test node:** `" + d.node + "`",
      "",
      "**Log reason:**",
      d.reason,
      "",
      analysisNote,
      "**Pytest / CI log excerpt:**",
      "",
      "```text",
      d.excerpt,
      "```",
      "",
      "---",
      "*Generated from a nightly HTML report. Redact secrets before submitting; complete the checkboxes on GitHub.*",
    ].join("\\n");
  }}

  function issueTitle(d) {{
    var n = d.node.replace(/\\s*\\(ERROR\\)\\s*$/i, "");
    var t = "[Bug]: Nightly / CI failed - " + n;
    return t.length > 220 ? t.slice(0, 217) + "..." : t;
  }}

  function openModal(d) {{
    ta.value = buildMarkdown(d);
    var u = new URL(issueBase);
    u.searchParams.set("template", bugTemplate);
    u.searchParams.set("title", issueTitle(d));
    openA.href = u.toString();
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    ta.focus();
  }}

  function closeModal() {{
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }}

  document.addEventListener("click", function (ev) {{
    var b = ev.target.closest && ev.target.closest(".btn-github-issue");
    if (b) {{
      ev.preventDefault();
      var d = gatherRow(b);
      if (d) openModal(d);
    }}
  }});
  closeBtn.addEventListener("click", closeModal);
  backdrop.addEventListener("click", closeModal);
  document.addEventListener("keydown", function (ev) {{
    if (ev.key === "Escape" && !modal.hidden) closeModal();
  }});
  copyBtn.addEventListener("click", function () {{
    var v = ta.value;
    var reset = function () {{ copyBtn.textContent = "Copy body"; }};
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(v).then(function () {{
        copyBtn.textContent = "Copied";
        setTimeout(reset, 1400);
      }}).catch(function () {{ ta.select(); document.execCommand("copy"); reset(); }});
    }} else {{
      ta.select();
      try {{ document.execCommand("copy"); }} catch (e) {{}}
      copyBtn.textContent = "Copied";
      setTimeout(reset, 1400);
    }}
  }});

  document.querySelectorAll(".btn-view-full-log").forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      var id = btn.getAttribute("aria-controls");
      var panel = id ? document.getElementById(id) : null;
      if (!panel) return;
      var nowHidden = !panel.hidden;
      panel.hidden = nowHidden;
      btn.setAttribute("aria-expanded", nowHidden ? "false" : "true");
      btn.textContent = nowHidden ? "查看完整日志" : "收起完整日志";
    }});
  }});

  function applyPerfFilters(scope) {{
    var testSel = scope.querySelector('select[data-filter-key="test"]');
    var metricSel = scope.querySelector('select[data-filter-key="metric"]');
    var statusSel = scope.querySelector('select[data-filter-key="status"]');
    var rows = scope.querySelectorAll('tr[data-perf-row="1"]');
    var empty = scope.querySelector("[data-perf-empty]");
    if (!testSel || !metricSel || !statusSel || !rows.length) return;

    var testVal = testSel.value || "";
    var metricVal = metricSel.value || "";
    var statusVal = statusSel.value || "";
    var visibleCount = 0;
    rows.forEach(function (row) {{
      var ok = true;
      if (testVal && row.getAttribute("data-test") !== testVal) ok = false;
      if (metricVal && row.getAttribute("data-metric") !== metricVal) ok = false;
      if (statusVal && row.getAttribute("data-status") !== statusVal) ok = false;
      row.hidden = !ok;
      if (ok) visibleCount += 1;
    }});
    if (empty) {{
      empty.hidden = visibleCount !== 0;
    }}
  }}

  document.querySelectorAll("[data-perf-filter-scope]").forEach(function (scope) {{
    scope.querySelectorAll("select[data-filter-key]").forEach(function (sel) {{
      sel.addEventListener("change", function () {{
        applyPerfFilters(scope);
      }});
    }});
    applyPerfFilters(scope);
  }});
}})();
</script>
"""


def _md_cell(s: str) -> str:
    return (s or "").replace("|", "/").replace("\n", " ")


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    cols = len(headers)
    if not headers:
        return ""
    for row in rows:
        if len(row) != cols:
            raise ValueError(f"row has {len(row)} cells, expected {cols}: {row!r}")
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * cols) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_html_table(
    headers: list[str],
    rows: list[list[str]],
    *,
    table_class: str = "",
    row_classes: list[str] | None = None,
    cell_suffixes: list[list[str]] | None = None,
) -> str:
    cls = f' class="{html.escape(table_class)}"' if table_class else ""
    parts = [f"<table{cls}>", "<thead><tr>"]
    for h in headers:
        parts.append(f"<th>{html.escape(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for i, row in enumerate(rows):
        tr_attr = ""
        if row_classes and i < len(row_classes) and (row_classes[i] or "").strip():
            tr_attr = f' class="{html.escape(row_classes[i].strip())}"'
        parts.append(f"<tr{tr_attr}>")
        suffix_row = (
            cell_suffixes[i]
            if cell_suffixes and i < len(cell_suffixes)
            else None
        )
        for j, c in enumerate(row):
            suf = ""
            if suffix_row is not None and j < len(suffix_row):
                suf = (suffix_row[j] or "").strip()
            inner = html.escape(c)
            if suf:
                if suf.startswith("↑"):
                    dcls = "perf-delta perf-delta--up"
                elif suf.startswith("↓"):
                    dcls = "perf-delta perf-delta--down"
                else:
                    dcls = "perf-delta"
                inner += f' <span class="{dcls}">{html.escape(suf)}</span>'
            parts.append(f"<td>{inner}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def _summary_row_kind(info: dict[str, Any] | None) -> str:
    """``ok`` = no failures/errors; ``fail`` = failures; ``unknown`` = could not classify."""
    if not info:
        return "unknown"
    if info.get("failed_nodes") or info.get("error_nodes"):
        return "fail"
    counts = extract_pytest_counts(info.get("summary"))
    if counts["failed"] or counts["error"]:
        return "fail"
    summ = (info.get("summary") or "").strip()
    if not summ:
        return "unknown"
    if re.search(r"\d+\s+(?:passed|failed|skipped|errors?)\b", summ, re.I):
        return "ok"
    return "unknown"


def _summary_row_kind_bk(rec: dict[str, Any]) -> str:
    if rec.get("log_error"):
        return "fail"
    if not rec.get("raw_url"):
        return "unknown"
    return _summary_row_kind(rec.get("info"))


def _job_is_clean(info: dict[str, Any]) -> bool:
    return not info["failed_nodes"] and not info["error_nodes"]


def default_log_dir(repo_root: Path) -> Path:
    return repo_root / "logs" / "nightly_jobs"


def discover_job_logs(log_dir: Path) -> list[tuple[str, list[Path]]]:
    if not log_dir.is_dir():
        return []
    subs = sorted(
        [p for p in log_dir.iterdir() if not p.name.startswith(".")],
        key=lambda p: p.name,
    )
    if not subs:
        return []

    merged: dict[str, list[Path]] = {}

    for d in sorted((p for p in subs if p.is_dir()), key=lambda p: p.name):
        resolved: list[Path] = []
        for pat in ("*.log", "*.out", "*.txt"):
            resolved.extend(sorted(d.glob(pat)))
        if resolved:
            merged.setdefault(d.name, []).extend(resolved)

    for p in subs:
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".log", ".out", ".txt"):
            continue
        merged.setdefault(p.stem, []).append(p)

    out: list[tuple[str, list[Path]]] = []
    for name in sorted(merged.keys()):
        paths = merged[name]
        if not paths:
            continue
        seen: set[str] = set()
        uniq: list[Path] = []
        for path in sorted(paths, key=lambda q: q.as_posix().lower()):
            key = str(path.resolve())
            if key not in seen:
                seen.add(key)
                uniq.append(path)
        out.append((name, uniq))
    return out


# Local Test summary: group jobs by pillar × dimension (folder / job name prefix).
_LOCAL_SUMMARY_PILLARS = ("Omni", "TTS", "Diffusion")
_LOCAL_SUMMARY_DIMS = ("Perf", "Acc", "Function", "doc", "stability")


def _classify_local_nightly_job_strict(job_name: str) -> tuple[str | None, str | None]:
    """
    Prefix form only: ``<pillar>_<dim>`` or ``<dim>_<pillar>`` at start of name
    (after normalizing spaces/hyphens to underscores).
    """
    n = job_name.strip()
    n = re.sub(r"[\s\-]+", "_", n)
    n = re.sub(r"_+", "_", n).lower()
    pillar_key: str | None = None
    dim_key: str | None = None
    m = re.match(
        r"^(omni|tts|diffusion|diff)_(perf|acc|function|doc|stability)(?:_|$)",
        n,
    )
    if m:
        pillar_key, dim_key = m.group(1), m.group(2)
    else:
        m2 = re.match(
            r"^(perf|acc|function|doc|stability)_(omni|tts|diffusion|diff)(?:_|$)",
            n,
        )
        if m2:
            dim_key, pillar_key = m2.group(1), m2.group(2)
    if not pillar_key or not dim_key:
        return (None, None)
    if pillar_key == "omni":
        pillar = "Omni"
    elif pillar_key == "tts":
        pillar = "TTS"
    elif pillar_key in ("diffusion", "diff"):
        pillar = "Diffusion"
    else:
        return (None, None)
    dim_map = {
        "perf": "Perf",
        "acc": "Acc",
        "function": "Function",
        "doc": "doc",
        "stability": "stability",
    }
    dim_label = dim_map.get(dim_key)
    if not dim_label:
        return (None, None)
    return (pillar, dim_label)


def _classify_local_nightly_job_keywords(job_name: str) -> tuple[str | None, str | None]:
    """
    Infer pillar × dim from tokens in the job folder / file stem name
    (e.g. ``full_moon_Diffusion_X2I_A_T_Accuracy_Test`` → Diffusion / Acc).
    """
    name_lower = job_name.strip().lower()

    pillar: str | None = None
    best_pi = len(name_lower) + 1
    for pat, plabel in (
        ("diffusion", "Diffusion"),
        (r"(?<![a-z0-9])tts(?![a-z0-9])", "TTS"),
        (r"(?<![a-z0-9])omni(?![a-z0-9])", "Omni"),
    ):
        m = re.search(pat, name_lower)
        if m and m.start() < best_pi:
            best_pi = m.start()
            pillar = plabel

    dim: str | None = None
    best_di = len(name_lower) + 1
    # Longer / compound keywords first; leftmost match wins for dim
    for pat, dlabel in (
        (r"accuracy", "Acc"),
        (r"performance", "Perf"),
        (r"functional", "Function"),
        (r"(?<![a-z0-9])function(?![a-z0-9])", "Function"),
        (r"documentation", "doc"),
        (r"(?<![a-z0-9])docs(?![a-z0-9])", "doc"),
        (r"(?<![a-z0-9])doc(?![a-z0-9])", "doc"),
        (r"stability", "stability"),
        (r"(?<![a-z0-9])stable(?![a-z0-9])", "stability"),
        (r"(?<![a-z0-9])perf(?![a-z0-9])", "Perf"),
        (r"(?<![a-z0-9])acc(?![a-z0-9])", "Acc"),
    ):
        m = re.search(pat, name_lower)
        if m and m.start() < best_di:
            best_di = m.start()
            dim = dlabel

    if pillar and dim:
        return (pillar, dim)
    return (None, None)


def _classify_local_nightly_job(job_name: str) -> tuple[str | None, str | None]:
    """
    Map ``job_name`` (directory or flat file stem) to (pillar, dim).

    1. Strict prefix: ``<pillar>_<dim>`` or reverse (see `_classify_local_nightly_job_strict`).
    2. Keyword scan: ``diffusion`` / ``omni`` / ``tts`` and ``accuracy`` / ``perf`` / … anywhere in the name.
    """
    s = _classify_local_nightly_job_strict(job_name)
    if s[0] and s[1]:
        return s
    return _classify_local_nightly_job_keywords(job_name)


def _local_job_rows_with_info(
    groups: list[tuple[str, list[Path]]],
) -> list[tuple[str, list[Path], dict[str, Any]]]:
    out: list[tuple[str, list[Path], dict[str, Any]]] = []
    for job_name, paths in groups:
        text = read_job_text(paths)
        info = parse_pytest_log(text)
        out.append((job_name, paths, info))
    return out


def _render_local_summary_table_html(
    chunk: list[tuple[str, list[Path], dict[str, Any]]],
) -> str:
    summary_rows_loc: list[list[str]] = []
    summary_row_cls_loc: list[str] = []
    for job_name, paths, info in chunk:
        summary_rows_loc.append(_summary_row_for_job(job_name, paths, info))
        summary_row_cls_loc.append(
            f"summary-row summary-row--{_summary_row_kind(info)}"
        )
    return _table_wrap(
        render_html_table(
            [
                "Job",
                "Total",
                "Passed",
                "Failed",
                "Skipped",
                "Errors",
                "执行时间",
            ],
            summary_rows_loc,
            table_class="summary",
            row_classes=summary_row_cls_loc,
        )
    )


def _render_local_summary_grouped_html(
    job_rows: list[tuple[str, list[Path], dict[str, Any]]],
) -> str:
    buckets: dict[str, dict[str, list[tuple[str, list[Path], dict[str, Any]]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    uncat: list[tuple[str, list[Path], dict[str, Any]]] = []
    for job_name, paths, info in job_rows:
        pillar, dim = _classify_local_nightly_job(job_name)
        if pillar and dim:
            buckets[pillar][dim].append((job_name, paths, info))
        else:
            uncat.append((job_name, paths, info))

    parts: list[str] = []
    for pillar in _LOCAL_SUMMARY_PILLARS:
        dim_map = buckets.get(pillar) or {}
        if not any(dim_map.get(d) for d in _LOCAL_SUMMARY_DIMS):
            continue
        dim_blocks: list[str] = []
        for dim in _LOCAL_SUMMARY_DIMS:
            chunk = dim_map.get(dim) or []
            if not chunk:
                continue
            chunk.sort(key=lambda t: t[0].lower())
            tbl = _render_local_summary_table_html(chunk)
            dim_blocks.append(
                "\n".join(
                    [
                        '<details class="local-summary-dim">',
                        f'<summary class="local-summary-dim-summary">{html.escape(dim)}</summary>',
                        f'<div class="local-summary-dim-body">{tbl}</div>',
                        "</details>",
                    ]
                )
            )
        parts.append(
            "\n".join(
                [
                    '<details class="local-summary-pillar">',
                    f'<summary class="local-summary-pillar-summary">{html.escape(pillar)}</summary>',
                    '<div class="local-summary-pillar-body">',
                    "\n".join(dim_blocks),
                    "</div>",
                    "</details>",
                ]
            )
        )

    if uncat:
        uncat.sort(key=lambda t: t[0].lower())
        parts.append(
            "\n".join(
                [
                    '<details class="local-summary-pillar local-summary-pillar--other">',
                    '<summary class="local-summary-pillar-summary">其他</summary>',
                    '<div class="local-summary-pillar-body">',
                    _render_local_summary_table_html(uncat),
                    "</div>",
                    "</details>",
                ]
            )
        )

    tail_hints = [
        '<p class="hint">若存在失败，请在「失败分析」中按 Job 展开或折叠查看摘录。</p>',
        '<p class="hint summary-legend">行底色：<strong class="summary-legend--ok">绿</strong> = 本 Job 无失败/错误；'
        '<strong class="summary-legend--fail">红</strong> = 存在失败、错误或日志拉取失败；'
        '<strong class="summary-legend--unk">灰</strong> = 未识别到 pytest 结果摘要。</p>',
    ]
    return ("\n".join(parts + tail_hints)) if parts else "\n".join(tail_hints)


def _append_local_summary_grouped_markdown(
    lines: list[str],
    job_rows: list[tuple[str, list[Path], dict[str, Any]]],
) -> None:
    buckets: dict[str, dict[str, list[tuple[str, list[Path], dict[str, Any]]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    uncat: list[tuple[str, list[Path], dict[str, Any]]] = []
    for job_name, paths, info in job_rows:
        pillar, dim = _classify_local_nightly_job(job_name)
        if pillar and dim:
            buckets[pillar][dim].append((job_name, paths, info))
        else:
            uncat.append((job_name, paths, info))

    for pillar in _LOCAL_SUMMARY_PILLARS:
        dim_map = buckets.get(pillar) or {}
        if not any(dim_map.get(d) for d in _LOCAL_SUMMARY_DIMS):
            continue
        lines.append(f"#### {pillar}")
        lines.append("")
        for dim in _LOCAL_SUMMARY_DIMS:
            chunk = dim_map.get(dim) or []
            if not chunk:
                continue
            chunk.sort(key=lambda t: t[0].lower())
            lines.append(f"##### {dim}")
            lines.append("")
            summary_rows: list[list[str]] = [
                _summary_row_for_job(n, p, i) for n, p, i in chunk
            ]
            lines.append(
                render_markdown_table(
                    [
                        "Job",
                        "Total",
                        "Passed",
                        "Failed",
                        "Skipped",
                        "Errors",
                        "执行时间",
                    ],
                    summary_rows,
                )
            )
            lines.append("")

    if uncat:
        uncat.sort(key=lambda t: t[0].lower())
        lines.append("#### 其他")
        lines.append("")
        summary_rows_u = [_summary_row_for_job(n, p, i) for n, p, i in uncat]
        lines.append(
            render_markdown_table(
                [
                    "Job",
                    "Total",
                    "Passed",
                    "Failed",
                    "Skipped",
                    "Errors",
                    "执行时间",
                ],
                summary_rows_u,
            )
        )
        lines.append("")


def markdown_local_summary_from_log_dir(log_dir: Path) -> str:
    """
    Markdown block matching the **grouped Summary** under nightly **Local cluster** (pillar × dim tables).

    Used by ``compose_full_report.py`` for **Test Result → H200 / H800 / A100** when
    ``--log-dir-h*`` points at a ``nightly_jobs``-style tree.
    """
    groups = discover_job_logs(log_dir)
    lines: list[str] = [
        f"*日志根目录:* `{log_dir}`（布局见 [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md)）。",
        "",
        "与 **nightly** HTML/Markdown 报告中本地 **Summary** 相同的分组方式（Omni / TTS / Diffusion × Perf / Acc / …）：",
        "",
    ]
    if not groups:
        lines.append(
            f"*未找到可解析的 Job 日志。* 确认目录与 "
            f"[references/nightly-local-log-layout.md](references/nightly-local-log-layout.md) 一致。"
        )
        lines.append("")
        return "\n".join(lines)

    job_rows = _local_job_rows_with_info(groups)
    _append_local_summary_grouped_markdown(lines, job_rows)
    lines.append(
        "*失败 / 错误 Job 的逐条摘录仅在 **nightly** 完整报告中展开；此处仅保留汇总表。*"
    )
    lines.append("")
    return "\n".join(lines)


def read_job_text(paths: list[Path]) -> str:
    chunks: list[str] = []
    for p in paths:
        try:
            chunks.append(p.read_text(encoding="utf-8-sig", errors="replace"))
        except OSError as e:
            chunks.append(f"\n<<< read error {p}: {e} >>>\n")
    return "\n".join(chunks)


def _combined_job_log_disk_bytes(paths: list[Path]) -> int | None:
    """Return total on-disk size of ``paths`` in bytes, or ``None`` if ``stat`` fails."""
    total = 0
    for p in paths:
        try:
            total += p.stat().st_size
        except OSError:
            return None
    return total


def _read_combined_job_logs(paths: list[Path]) -> str:
    parts: list[str] = []
    for p in paths:
        parts.append(f"===== {p.name} =====\n")
        try:
            parts.append(p.read_text(encoding="utf-8-sig", errors="replace"))
        except OSError as e:
            parts.append(f"<<< read error {p}: {e} >>>\n")
        parts.append("\n")
    return "".join(parts)


def _render_full_log_panel_html(paths: list[Path], panel_id: str) -> str:
    """Button + hidden panel: full concatenated logs, or oversize / stat error notice."""
    if not paths:
        return ""
    tb = _combined_job_log_disk_bytes(paths)
    if tb is None:
        inner = '<p class="note full-log-oversize">无法读取日志文件信息。</p>'
    elif tb > FULL_LOG_EMBED_MAX_BYTES:
        mib = tb / (1024 * 1024)
        cap = FULL_LOG_EMBED_MAX_BYTES / (1024 * 1024)
        lis = "".join(
            f"<li><code>{html.escape(str(p.resolve()))}</code></li>" for p in paths
        )
        inner = (
            f'<p class="note full-log-oversize">合并日志约 <strong>{mib:.2f} MiB</strong>，超过报告嵌入上限 '
            f"(<strong>{cap:.1f} MiB</strong>)，未内嵌全文。请在本地打开：</p>"
            f'<ul class="full-log-paths">{lis}</ul>'
        )
    else:
        inner = f'<pre class="log-full">{html.escape(_read_combined_job_logs(paths))}</pre>'
    return (
        '<div class="full-log-wrap">'
        '<button type="button" class="btn-view-full-log" aria-expanded="false" '
        f'aria-controls="{panel_id}">查看完整日志</button>'
        f'<div id="{panel_id}" class="full-log-panel" hidden>{inner}</div>'
        "</div>"
    )


def _summary_row_for_job(job_name: str, paths: list[Path], info: dict[str, Any]) -> list[str]:
    counts = extract_pytest_counts(info["summary"])
    n_fail = len(info["failed_nodes"])
    n_err = len(info["error_nodes"])

    if info["summary"] is None and not info["failed_nodes"] and not n_err:
        total = ok = bad = skip = errc = ""
    else:
        fc = counts["failed"] if counts["failed"] else n_fail
        ec = counts["error"] if counts["error"] else n_err
        if counts["passed"] or counts["failed"] or counts["skipped"] or counts["error"]:
            total = str(
                counts["passed"] + counts["failed"] + counts["skipped"] + counts["error"]
            )
            ok = str(counts["passed"])
            bad = str(fc)
            skip = str(counts["skipped"])
            errc = str(ec)
        else:
            total = ""
            ok = "?"
            bad = str(fc)
            skip = str(counts["skipped"]) if counts["skipped"] else "?"
            errc = str(ec)

    dur = extract_pytest_duration_display(info.get("summary"))
    dur_cell = _md_cell(dur) if dur else "—"
    return [
        _md_cell(job_name),
        _md_cell(total),
        _md_cell(ok),
        _md_cell(bad),
        _md_cell(skip),
        _md_cell(errc),
        dur_cell,
    ]


def _summary_row_for_bk_rec(rec: dict[str, Any]) -> list[str]:
    name = rec["name"]
    if not rec.get("raw_url"):
        return [_md_cell(name), "", "", "", "", "", "no log URL"]
    if rec.get("log_error"):
        return [
            _md_cell(name),
            "",
            "",
            "",
            "",
            "",
            _md_cell(f"log fetch: {rec['log_error'][:200]}"),
        ]
    info = rec.get("info")
    if not info:
        return [_md_cell(name), "", "", "", "", "", "—"]
    return _summary_row_for_job(name, [], info)


def _perf_num(v: Any) -> str:
    if isinstance(v, (int, float)):
        s = f"{float(v):.4f}".rstrip("0").rstrip(".")
        return s or "0"
    return "N/A"


def _perf_pct(v: Any) -> str:
    if isinstance(v, (int, float)):
        sign = "+" if float(v) >= 0 else ""
        return f"{sign}{float(v):.2f}%"
    return "N/A"


def _as_num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _fmt_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return ""


def _resolve_kanban_raw_root(kanban_cfg: KanbanAssetsConfig) -> Path | None:
    if kanban_cfg.raw_root is not None:
        return kanban_cfg.raw_root.resolve()
    if kanban_cfg.repo_root is not None:
        return (kanban_cfg.repo_root / "data/buildkite_nightly_raw").resolve()
    return None


def _collect_kanban_raw_files(raw_root: Path | None) -> list[Path]:
    if raw_root is None or not raw_root.is_dir():
        return []
    files: dict[Path, None] = {}
    for pattern in KANBAN_RAW_PATTERNS:
        for path in raw_root.rglob(pattern):
            if path.is_file():
                files[path] = None
    return sorted(files)


def _build_ids_from_raw_files(raw_root: Path | None, paths: list[Path]) -> list[str]:
    if raw_root is None:
        return []
    ids: set[str] = set()
    for path in paths:
        try:
            rel = path.relative_to(raw_root)
        except ValueError:
            continue
        if not rel.parts:
            continue
        head = rel.parts[0]
        if head.isdigit():
            ids.add(head)
    return sorted(ids, key=lambda item: int(item))


def _kanban_raw_assets_diagnostic(
    kanban_cfg: KanbanAssetsConfig,
    summary: dict[str, Any],
) -> dict[str, Any]:
    assets_dir_txt = str(summary.get("assets_dir") or "")
    assets_dir = Path(assets_dir_txt) if assets_dir_txt else None
    history_files = sorted(assets_dir.glob("*_history.json")) if assets_dir and assets_dir.is_dir() else []
    raw_root = _resolve_kanban_raw_root(kanban_cfg)
    raw_files = _collect_kanban_raw_files(raw_root)
    build_ids = _build_ids_from_raw_files(raw_root, raw_files)

    latest_history = max(history_files, key=lambda p: p.stat().st_mtime) if history_files else None
    latest_raw = max(raw_files, key=lambda p: p.stat().st_mtime) if raw_files else None
    recommended = ""
    if kanban_cfg.repo_root:
        recommended = (
            "python scripts/nightly_local_log_report.py --kanban-repo-root "
            f"{kanban_cfg.repo_root} --kanban-refresh-from-raw ..."
        )

    return {
        "raw_root": str(raw_root or ""),
        "raw_exists": bool(raw_root and raw_root.is_dir()),
        "raw_file_count": len(raw_files),
        "raw_build_ids": build_ids[-5:],
        "raw_latest_mtime": _fmt_mtime(latest_raw) if latest_raw else "",
        "history_file_count": len(history_files),
        "history_latest_mtime": _fmt_mtime(latest_history) if latest_history else "",
        "recommended_command": recommended,
    }


def _kanban_repo_dirty(repo: Path) -> tuple[bool | None, str]:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return None, detail[:500]
    return bool(proc.stdout.strip()), proc.stdout.strip()[:500]


def _kanban_python(repo: Path) -> str:
    candidates = (
        repo / ".venv/bin/python",
        repo / ".venv/Scripts/python.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def _run_kanban_refresh_from_raw(
    kanban_repo_root: Path | None,
    raw_root: Path | None,
) -> tuple[str | None, list[str]]:
    if kanban_repo_root is None:
        return None, ["kanban raw refresh skipped: --kanban-repo-root is required."]
    repo = kanban_repo_root.resolve()
    if not repo.is_dir():
        return None, [f"kanban raw refresh skipped: repo root not found: {repo}"]
    sync_script = repo / "scripts/sync_buildkite_raw_model_results.py"
    gen_script = repo / "scripts/generate_charts.py"
    missing = [str(p) for p in (sync_script, gen_script) if not p.is_file()]
    if missing:
        return None, ["kanban raw refresh skipped: missing script(s): " + ", ".join(missing)]

    dirty, detail = _kanban_repo_dirty(repo)
    if dirty is None:
        return None, [
            "kanban raw refresh skipped: unable to verify clean git working tree"
            + (f"; {detail}" if detail else "")
        ]
    if dirty:
        return None, [
            "kanban raw refresh skipped: kanban checkout has uncommitted changes. "
            "Commit or clean that repo before regenerating assets."
            + (f" Changed entries: {detail}" if detail else "")
        ]

    warnings: list[str] = []
    synced_models = 0
    py = _kanban_python(repo)
    for model_name, model_keywords in KANBAN_RAW_MODEL_SYNCS:
        cmd = [
            py,
            str(sync_script),
            "--model-name",
            model_name,
            "--model-keywords",
            model_keywords,
        ]
        if raw_root is not None:
            cmd.extend(["--raw-root", str(raw_root.resolve())])
        proc = subprocess.run(
            cmd,
            cwd=str(repo),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            warnings.append(
                f"kanban raw sync failed for {model_name}: exit {proc.returncode}"
                + (f"; {detail[:500]}" if detail else "")
            )
            continue
        synced_models += 1

    proc = subprocess.run(
        [py, str(gen_script)],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        warnings.append(
            f"kanban generate_charts.py failed: exit {proc.returncode}"
            + (f"; {detail[:500]}" if detail else "")
        )
        return None, warnings

    note = f"kanban raw refresh completed: synced {synced_models} model group(s), regenerated chart history assets."
    return note, warnings


_PERF_TABLE_HEADERS = [
    "Type",
    "Config",
    "Test",
    "Metric",
    "latest",
    "baseline",
    "vs baseline",
    "Status",
]


def _render_perf_model_table_html(table_id: str, rows: list[list[str]]) -> str:
    """Render one model performance table with per-table dropdown filters."""
    tests = sorted({r[2] for r in rows if len(r) > 2 and r[2]})
    metrics = sorted({r[3] for r in rows if len(r) > 3 and r[3]})
    statuses = sorted({r[7] for r in rows if len(r) > 7 and r[7]})

    def _select_html(key: str, label: str, options: list[str]) -> str:
        opts = ['<option value="">All</option>']
        for value in options:
            val = html.escape(value, quote=True)
            txt = html.escape(value)
            opts.append(f'<option value="{val}">{txt}</option>')
        return (
            '<label class="perf-filter-label">'
            f"<span>{html.escape(label)}</span>"
            f'<select class="perf-filter-select" data-filter-key="{html.escape(key, quote=True)}">'
            + "".join(opts)
            + "</select></label>"
        )

    parts: list[str] = [
        f'<div class="perf-filter-scope" data-perf-filter-scope="{html.escape(table_id, quote=True)}">',
        '<div class="perf-filter-bar">',
        _select_html("test", "Test", tests),
        _select_html("metric", "Metric", metrics),
        _select_html("status", "Status", statuses),
        "</div>",
    ]
    parts.append('<div class="table-scroll">')
    parts.append('<table class="summary perf-filter-table">')
    parts.append("<thead><tr>")
    for h in _PERF_TABLE_HEADERS:
        parts.append(f"<th>{html.escape(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        test_v = html.escape((row[2] if len(row) > 2 else ""), quote=True)
        metric_v = html.escape((row[3] if len(row) > 3 else ""), quote=True)
        status_v = html.escape((row[7] if len(row) > 7 else ""), quote=True)
        parts.append(
            '<tr data-perf-row="1" '
            f'data-test="{test_v}" data-metric="{metric_v}" data-status="{status_v}">'
        )
        for cell in row:
            parts.append(f"<td>{html.escape(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    parts.append('<p class="note perf-filter-empty" data-perf-empty hidden>No rows match filters.</p>')
    parts.append("</div>")
    return "\n".join(parts)


def _raw_json_timestamp(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = None
    if payload is not None:
        records = payload if isinstance(payload, list) else [payload]
        timestamps: list[str] = []
        for item in records:
            if not isinstance(item, dict):
                continue
            raw = str(item.get("timestamp") or "").strip()
            if not raw:
                continue
            try:
                timestamps.append(datetime.strptime(raw, "%Y%m%d-%H%M%S").isoformat())
            except ValueError:
                timestamps.append(raw)
        if timestamps:
            return max(timestamps)

    match = re.search(r"(\d{8}-\d{6})", path.stem)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d-%H%M%S").isoformat()
        except ValueError:
            return ""
    return ""


def _local_perf_result_files(result_dir: Path) -> list[Path]:
    if not result_dir.is_dir():
        return []
    paths: dict[Path, None] = {}
    for pattern in KANBAN_RAW_PATTERNS:
        for path in result_dir.rglob(pattern):
            if path.is_file():
                paths[path] = None
    return sorted(paths)


def _pick_latest_local_perf_result_dir(result_root: Path) -> Path | None:
    if not result_root.is_dir():
        return None
    dirs = [path for path in result_root.iterdir() if path.is_dir()]
    if not dirs:
        return None
    def _created_at(path: Path) -> float:
        stat = path.stat()
        return float(getattr(stat, "st_birthtime", stat.st_mtime))
    return max(dirs, key=_created_at)


def _load_local_perf_result_payload(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], str(exc)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)], None
    if isinstance(payload, dict):
        if isinstance(payload.get("results"), list):
            return [item for item in payload["results"] if isinstance(item, dict)], None
        return [payload], None
    return [], "unsupported JSON payload: expected object, list, or object with results list"


def _local_perf_date(raw: dict[str, Any], source_file: Path) -> tuple[str, str]:
    ts = str(raw.get("timestamp") or "").strip()
    if ts:
        try:
            parsed = datetime.strptime(ts, "%Y%m%d-%H%M%S")
            return parsed.strftime("%Y-%m-%d %H:%M:%S"), parsed.isoformat()
        except ValueError:
            return ts, ts
    file_ts = _raw_json_timestamp(source_file)
    return file_ts, file_ts


def _set_scaled_metric(record: dict[str, Any], key: str, value: Any, scale: float = 1.0) -> None:
    num = _as_num(value)
    if num is not None:
        record[key] = num * scale


def _normalize_local_perf_result_record(raw: dict[str, Any], source_file: Path) -> dict[str, Any] | None:
    result = raw.get("result") if isinstance(raw.get("result"), dict) else raw
    bench = raw.get("benchmark_params") if isinstance(raw.get("benchmark_params"), dict) else {}
    server = raw.get("server_params") if isinstance(raw.get("server_params"), dict) else {}
    baseline = bench.get("baseline") if isinstance(bench.get("baseline"), dict) else raw.get("baseline")
    if not isinstance(result, dict) or not isinstance(baseline, dict):
        return None

    date, sort_timestamp = _local_perf_date(raw, source_file)
    model = server.get("model") or result.get("model") or raw.get("Model") or raw.get("model_id") or "unknown"
    record: dict[str, Any] = {
        "test_name": str(raw.get("test_name") or source_file.stem),
        "model_id": str(model),
        "benchmark_name": str(bench.get("name") or raw.get("benchmark_name") or ""),
        "dataset_name": str(bench.get("dataset") or result.get("dataset") or raw.get("Dataset") or ""),
        "task": str(bench.get("task") or result.get("task") or raw.get("Task") or ""),
        "max_concurrency": bench.get("max-concurrency", raw.get("max_concurrency")),
        "num_prompts": bench.get("num-prompts", raw.get("num_prompts")),
        "completed_requests": result.get("completed_requests", raw.get("completed")),
        "failed_requests": result.get("failed_requests", raw.get("failed")),
        "date": date,
        "sort_timestamp": sort_timestamp,
        "source_file": source_file.name,
    }
    record["config_key"] = " | ".join(
        str(record.get(field) or "")
        for field in ("benchmark_name", "dataset_name", "task", "max_concurrency", "num_prompts")
    )

    _set_scaled_metric(record, "throughput_qps", result.get("throughput_qps"))
    _set_scaled_metric(record, "e2e_latency_ms", result.get("latency_mean"), 1000.0)
    _set_scaled_metric(record, "e2e_latency_p99_ms", result.get("latency_p99"), 1000.0)
    _set_scaled_metric(record, "peak_memory_gb", result.get("peak_memory_mb_mean"), 1.0 / 1024.0)
    _set_scaled_metric(record, "baseline_throughput_qps", baseline.get("throughput_qps"))
    _set_scaled_metric(record, "baseline_e2e_latency_ms", baseline.get("latency_mean"), 1000.0)
    _set_scaled_metric(record, "baseline_e2e_latency_p99_ms", baseline.get("latency_p99"), 1000.0)
    _set_scaled_metric(record, "baseline_peak_memory_gb", baseline.get("peak_memory_mb_mean"), 1.0 / 1024.0)
    return record


def _local_perf_summary(
    local_perf_cfg: LocalPerfResultConfig,
) -> tuple[dict[str, Any], dict[str, list[list[str]]]]:
    if local_perf_cfg.result_root is None:
        return {
            "status": "missing",
            "message": "local perf result root is not configured. Pass --local-perf-result-root.",
            "result_root": "",
            "result_dir": "",
            "rows": [],
            "summary": {"pass": 0, "fail": 0, "n/a": 0},
        }, {}

    result_root = local_perf_cfg.result_root.resolve()
    result_dir = _pick_latest_local_perf_result_dir(result_root)
    if result_dir is None:
        return {
            "status": "missing",
            "message": f"No timestamped local perf result directories found under {result_root}.",
            "result_root": str(result_root),
            "result_dir": "",
            "rows": [],
            "summary": {"pass": 0, "fail": 0, "n/a": 0},
        }, {}

    result_files = _local_perf_result_files(result_dir)
    if not result_files:
        return {
            "status": "missing",
            "message": f"No perf benchmark result JSON files found under {result_dir}.",
            "result_root": str(result_root),
            "result_dir": str(result_dir),
            "rows": [],
            "summary": {"pass": 0, "fail": 0, "n/a": 0},
        }, {}

    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_path in result_files:
        payload, error = _load_local_perf_result_payload(raw_path)
        if error:
            errors.append(f"{raw_path.name}: {error}")
            continue
        records.extend(
            rec
            for item in payload
            if (rec := _normalize_local_perf_result_record(item, raw_path)) is not None
        )
    rows = _build_perf_rows(records)
    rows = [row for row in rows if row.baseline is not None]
    rows.sort(key=lambda row: (row.model, row.config_key, row.metric))
    counts = {"pass": 0, "fail": 0, "n/a": 0}
    grouped_rows: dict[str, list[list[str]]] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
        grouped_rows.setdefault(_md_cell(row.model or "unknown"), []).append(
            [
                _md_cell(row.model_type),
                _md_cell(row.config_view),
                _md_cell(row.test_name),
                _md_cell(row.metric),
                _perf_num(row.latest),
                _perf_num(row.baseline),
                _perf_pct(row.vs_baseline_pct),
                _md_cell(row.status),
            ]
        )
    return {
        "status": "ok" if rows else "empty",
        "message": "" if rows else "No baseline-backed rows found in local perf benchmark result JSON.",
        "result_root": str(result_root),
        "result_dir": str(result_dir),
        "file_count": len(result_files),
        "errors": errors,
        "latest_day": max((str(rec.get("date") or "")[:10] for rec in records), default=""),
        "rows": rows,
        "summary": counts,
    }, grouped_rows


def _buildkite_perf_rows(
    kanban_cfg: KanbanAssetsConfig,
) -> tuple[dict[str, Any], dict[str, list[list[str]]]]:
    summary = build_assets_perf_summary(
        assets_dir=kanban_cfg.assets_dir,
        kanban_repo_root=kanban_cfg.repo_root,
        expected_remote=kanban_cfg.expected_remote,
        expected_branch=kanban_cfg.expected_branch,
    )
    if kanban_cfg.refresh_note:
        summary.setdefault("warnings", []).append(kanban_cfg.refresh_note)
    for warning in kanban_cfg.refresh_warnings:
        summary.setdefault("warnings", []).append(warning)
    if summary.get("status") != "ok" or kanban_cfg.refresh_warnings:
        summary["raw_fallback"] = _kanban_raw_assets_diagnostic(kanban_cfg, summary)
    grouped_rows: dict[str, list[list[str]]] = {}
    for item in summary.get("rows", []):
        model = _md_cell(str(item.get("model") or "unknown"))
        grouped_rows.setdefault(model, []).append(
            [
                _md_cell(str(item.get("model_type") or "")),
                _md_cell(str(item.get("config_view") or "")),
                _md_cell(str(item.get("test_name") or "")),
                _md_cell(str(item.get("metric") or "")),
                _perf_num(item.get("latest")),
                _perf_num(item.get("baseline")),
                _perf_pct(item.get("vs_baseline_pct")),
                _md_cell(str(item.get("status") or "")),
            ]
        )
    return summary, grouped_rows


def _kanban_fallback_items(summary: dict[str, Any]) -> list[str]:
    diag = summary.get("raw_fallback") or {}
    if not isinstance(diag, dict):
        return []
    items = [
        "本地 nightly_jobs 只用于用例通过情况分析，nightly_perf_manual.xlsx 只用于详细 perf benchmark 表格；二者不参与 baseline 对比。",
    ]
    raw_root = str(diag.get("raw_root") or "")
    if raw_root:
        items.append(f"kanban raw root: {raw_root}")
    raw_count = int(diag.get("raw_file_count") or 0)
    if diag.get("raw_exists"):
        items.append(f"raw perf JSON files: {raw_count}")
    else:
        items.append("raw perf JSON root is missing or not a directory.")
    build_ids = diag.get("raw_build_ids") or []
    if build_ids:
        items.append("recent raw build ids: " + ", ".join(str(v) for v in build_ids))
    if diag.get("raw_latest_mtime"):
        items.append(f"latest raw mtime: {diag.get('raw_latest_mtime')}")
    items.append(f"history files: {int(diag.get('history_file_count') or 0)}")
    if diag.get("history_latest_mtime"):
        items.append(f"latest history mtime: {diag.get('history_latest_mtime')}")
    if raw_count:
        items.append("Raw data is present. Re-run with --kanban-refresh-from-raw to invoke kanban sync + generate_charts before rendering.")
    elif diag.get("recommended_command"):
        items.append(f"Refresh command pattern: {diag.get('recommended_command')}")
    return items


def _render_kanban_fallback_html(summary: dict[str, Any]) -> str:
    items = _kanban_fallback_items(summary)
    if not items:
        return ""
    return (
        '<div class="note"><strong>Raw data fallback 诊断:</strong><ul>'
        + "".join(f"<li>{html.escape(item)}</li>" for item in items)
        + "</ul></div>"
    )


def _append_kanban_fallback_markdown(lines: list[str], summary: dict[str, Any]) -> None:
    items = _kanban_fallback_items(summary)
    if not items:
        return
    lines.append("- **Raw data fallback 诊断:**")
    for item in items:
        lines.append(f"  - {_md_cell(item)}")


def _render_buildkite_perf_inner_html(kanban_cfg: KanbanAssetsConfig) -> str:
    summary, grouped_rows = _buildkite_perf_rows(kanban_cfg)
    parts: list[str] = [
        '<p class="meta"><strong>数据源:</strong> '
        f'<code>{html.escape(str(summary.get("assets_dir") or ""))}</code></p>'
    ]
    history = summary.get("history") or {}
    if history:
        file_count = len(history.get("files") or [])
        parts.append(
            '<p class="meta"><strong>History:</strong> '
            f"{file_count} files, "
            f"{int(history.get('group_count') or 0)} groups, "
            f"selection={html.escape(str(history.get('selection') or ''))}"
            + (
                f", generated_at=<code>{html.escape(str(history.get('generated_at') or ''))}</code>"
                if history.get("generated_at")
                else ""
            )
            + "</p>"
        )
    warnings = summary.get("warnings") or []
    if warnings:
        warn_html = "".join(
            f"<li>{html.escape(str(w))}</li>" for w in warnings
        )
        parts.append(f'<div class="note"><strong>源配置提示:</strong><ul>{warn_html}</ul></div>')
    if summary.get("status") != "ok":
        msg = summary.get("message") or "No performance rows available."
        parts.append(f'<p class="note">{html.escape(str(msg))}</p>')
        fallback_html = _render_kanban_fallback_html(summary)
        if fallback_html:
            parts.append(fallback_html)
        return "\n".join(parts)
    parts.append(
        "<p class=\"hint\">"
        f"仅展示最新一天（{html.escape(str(summary.get('latest_day') or 'N/A'))}）且包含 baseline 的模型记录。"
        "</p>"
    )
    stats = summary.get("summary", {})
    parts.append(
        '<p class="meta"><strong>统计:</strong> '
        f"pass={int(stats.get('pass', 0))}, "
        f"fail={int(stats.get('fail', 0))}, "
        f"n/a={int(stats.get('n/a', 0))}</p>"
    )
    for i, model_name in enumerate(sorted(grouped_rows.keys())):
        model_rows = grouped_rows[model_name]
        table_html = _render_perf_model_table_html(f"perf-model-{i}", model_rows)
        parts.append(
            _details_subcard(
                f"{model_name} ({len(model_rows)} rows)",
                table_html,
                open_default=False,
                details_class="report-subcard--bk-perf-model",
                icon_paths=_SVG_LIST,
            )
        )
    return "\n".join(parts)


def _append_buildkite_perf_markdown(lines: list[str], summary: dict[str, Any], grouped_rows: dict[str, list[list[str]]]) -> None:
    lines.append(f"- **数据源:** `{summary.get('assets_dir') or ''}`")
    history = summary.get("history") or {}
    if history:
        lines.append(
            f"- **History:** `{len(history.get('files') or [])}` files / "
            f"`{int(history.get('group_count') or 0)}` groups / "
            f"selection `{history.get('selection') or ''}`"
        )
        if history.get("generated_at"):
            lines.append(f"- **History generated_at:** `{history.get('generated_at')}`")
    for warning in summary.get("warnings") or []:
        lines.append(f"- **提示:** {_md_cell(str(warning))}")
    if summary.get("status") != "ok":
        lines.append(
            f"- **说明:** {_md_cell(str(summary.get('message') or 'No performance rows available.'))}"
        )
        _append_kanban_fallback_markdown(lines, summary)
        lines.append("")
        return
    stats = summary.get("summary", {})
    lines.append(f"- **最新日期:** `{summary.get('latest_day')}`")
    lines.append(
        f"- **统计:** pass `{int(stats.get('pass', 0))}` / fail `{int(stats.get('fail', 0))}` / n-a `{int(stats.get('n/a', 0))}`"
    )
    lines.append("")
    lines.append("*按模型分组展示（Markdown 无折叠能力）。*")
    lines.append("")
    for model_name in sorted(grouped_rows.keys()):
        lines.append(f"#### {model_name}")
        lines.append("")
        lines.append(
            render_markdown_table(
                _PERF_TABLE_HEADERS,
                grouped_rows[model_name],
            )
        )
        lines.append("")


def _render_local_perf_baseline_inner_html(local_perf_cfg: LocalPerfResultConfig) -> str:
    summary, grouped_rows = _local_perf_summary(local_perf_cfg)
    parts: list[str] = [
        '<p class="meta"><strong>数据源:</strong> '
        f'<code>{html.escape(str(summary.get("result_dir") or summary.get("result_root") or ""))}</code></p>'
    ]
    if summary.get("file_count"):
        parts.append(f'<p class="meta"><strong>文件数:</strong> {int(summary.get("file_count") or 0)}</p>')
    if summary.get("errors"):
        err_html = "".join(f"<li>{html.escape(str(err))}</li>" for err in summary.get("errors") or [])
        parts.append(f'<div class="note"><strong>读取提示:</strong><ul>{err_html}</ul></div>')
    if summary.get("status") != "ok":
        parts.append(
            f'<p class="note">{html.escape(str(summary.get("message") or "No local perf benchmark baseline rows available."))}</p>'
        )
        return "\n".join(parts)
    stats = summary.get("summary", {})
    parts.append(
        "<p class=\"hint\">"
        f"读取最新 local perf benchmark result JSON（{html.escape(str(summary.get('latest_day') or 'N/A'))}），仅展示包含 baseline 的指标。"
        "</p>"
    )
    parts.append(
        '<p class="meta"><strong>统计:</strong> '
        f"pass={int(stats.get('pass', 0))}, "
        f"fail={int(stats.get('fail', 0))}, "
        f"n/a={int(stats.get('n/a', 0))}</p>"
    )
    for i, model_name in enumerate(sorted(grouped_rows.keys())):
        model_rows = grouped_rows[model_name]
        table_html = _render_perf_model_table_html(f"local-perf-model-{i}", model_rows)
        parts.append(
            _details_subcard(
                f"{model_name} ({len(model_rows)} rows)",
                table_html,
                open_default=False,
                details_class="report-subcard--local-perf-model",
                icon_paths=_SVG_LIST,
            )
        )
    return "\n".join(parts)


def _append_local_perf_baseline_markdown(lines: list[str], local_perf_cfg: LocalPerfResultConfig) -> None:
    summary, grouped_rows = _local_perf_summary(local_perf_cfg)
    lines.append("## Local 性能基线对比")
    lines.append("")
    lines.append(f"- **数据源:** `{summary.get('result_dir') or summary.get('result_root') or ''}`")
    if summary.get("file_count"):
        lines.append(f"- **文件数:** `{int(summary.get('file_count') or 0)}`")
    for err in summary.get("errors") or []:
        lines.append(f"- **读取提示:** {_md_cell(str(err))}")
    if summary.get("status") != "ok":
        lines.append(f"- **说明:** {_md_cell(str(summary.get('message') or 'No local perf benchmark baseline rows available.'))}")
        lines.append("")
        return
    stats = summary.get("summary", {})
    lines.append(f"- **最新日期:** `{summary.get('latest_day')}`")
    lines.append(
        f"- **统计:** pass `{int(stats.get('pass', 0))}` / fail `{int(stats.get('fail', 0))}` / n-a `{int(stats.get('n/a', 0))}`"
    )
    lines.append("")
    for model_name in sorted(grouped_rows.keys()):
        lines.append(f"### {model_name}")
        lines.append("")
        lines.append(render_markdown_table(_PERF_TABLE_HEADERS, grouped_rows[model_name]))
        lines.append("")


def _append_buildkite_markdown(
    lines: list[str],
    bk_build: dict[str, Any] | None,
    bk_jobs: list[dict[str, Any]] | None,
    bk_note: str | None,
    kanban_cfg: KanbanAssetsConfig,
) -> None:
    lines.append("## Buildkite: latest scheduled nightly (main)")
    lines.append("")
    if bk_note:
        lines.append(bk_note)
        lines.append("")
        lines.append("### 性能基线对比")
        lines.append("")
        summary, grouped_rows = _buildkite_perf_rows(kanban_cfg)
        _append_buildkite_perf_markdown(lines, summary, grouped_rows)
        return
    if not bk_build or bk_jobs is None:
        lines.append("*(Buildkite section not available.)*")
        lines.append("")
        lines.append("### 性能基线对比")
        lines.append("")
        summary, grouped_rows = _buildkite_perf_rows(kanban_cfg)
        _append_buildkite_perf_markdown(lines, summary, grouped_rows)
        return
    bn = int(bk_build["number"])
    build_url = f"https://buildkite.com/{ORG}/{PIPELINE}/builds/{bn}"
    lines.append(f"- **Build:** [{bn}]({build_url})")
    lines.append(f"- **State:** `{bk_build.get('state') or ''}`")
    lines.append(f"- **Message:** {_md_cell((bk_build.get('message') or '')[:500])}")
    co = (bk_build.get("commit") or "")[:12]
    if co:
        lines.append(f"- **Commit:** `{co}`")
    lines.append("")
    sum_rows = [_summary_row_for_bk_rec(r) for r in bk_jobs]
    lines.append(
        render_markdown_table(
            ["Job", "Total", "Passed", "Failed", "Skipped", "Errors", "执行时间"],
            sum_rows,
        )
    )
    lines.append("")
    lines.append(
        "*Failed Buildkite steps only: detailed excerpts below. Passing steps are in the table only.*"
    )
    lines.append("")
    lines.append("### 性能基线对比")
    lines.append("")
    summary, grouped_rows = _buildkite_perf_rows(kanban_cfg)
    _append_buildkite_perf_markdown(lines, summary, grouped_rows)
    for rec in bk_jobs:
        info = rec.get("info")
        if rec.get("log_error"):
            lines.append(f"### Buildkite step: `{_md_cell(rec['name'])}` (log fetch failed)")
            lines.append("")
            lines.append(f"- **Step link:** {rec['step_link']}")
            lines.append(f"- **Error:** {_md_cell(rec['log_error'][:500])}")
            lines.append("")
            continue
        if not info or _job_is_clean(info):
            continue
        lines.append(f"### Buildkite step: `{_md_cell(rec['name'])}`")
        lines.append("")
        lines.append(f"- **Step link:** [{rec['step_link']}]({rec['step_link']})")
        lines.append("")
        fail_rows: list[list[str]] = []
        for node in info["failed_nodes"]:
            fail_rows.append(
                [
                    _md_cell(node),
                    _md_cell(info["failed_reasons"].get(node, "")),
                    _md_cell(info["failure_analyses"].get(node, "")),
                    _excerpt_md_cell(info["failure_excerpts"].get(node, "")),
                ]
            )
        for node in info["error_nodes"]:
            fail_rows.append(
                [
                    _md_cell(node) + " (ERROR)",
                    _md_cell(info["error_reasons"].get(node, "")),
                    _md_cell(info["error_analyses"].get(node, "")),
                    _excerpt_md_cell(info["error_excerpts"].get(node, "")),
                ]
            )
        lines.append("#### Failures & errors")
        lines.append("")
        lines.append(
            render_markdown_table(
                ["Test node", "Log reason", "Analysis", "Excerpt (truncated)"],
                fail_rows,
            )
        )
        lines.append("")


def _excerpt_md_cell(excerpt: str, limit: int = 900) -> str:
    t = (excerpt or "").replace("\n", " ").strip()
    if len(t) > limit:
        t = t[: limit - 1] + "…"
    return _md_cell(t)


def emit_report(
    *,
    title: str,
    repo_root: Path,
    log_dir: Path,
    out_fp: Any,
    bk_build: dict[str, Any] | None = None,
    bk_jobs: list[dict[str, Any]] | None = None,
    bk_note: str | None = None,
    kanban_cfg: KanbanAssetsConfig | None = None,
    local_perf_cfg: LocalPerfResultConfig | None = None,
) -> None:
    groups = discover_job_logs(log_dir)
    if kanban_cfg is None:
        kanban_cfg = KanbanAssetsConfig(
            assets_dir=DEFAULT_KANBAN_ASSETS_DIR,
            repo_root=DEFAULT_KANBAN_REPO_ROOT,
        )
    if local_perf_cfg is None:
        local_perf_cfg = LocalPerfResultConfig()

    lines: list[str] = [
        f"# {_md_cell(title)}",
        "",
    ]

    _append_buildkite_markdown(lines, bk_build, bk_jobs, bk_note, kanban_cfg)

    lines.append("## Local cluster (nightly_jobs)")
    lines.append("")

    if not groups:
        lines.append(
            f"*No job logs found under `{log_dir}`. "
            "Confirm nightly jobs ran, copy logs from the cluster "
            "(vllm-omni-nightly-local references/nightly-local-log-fetch.md), "
            "and match paths in references/nightly-local-log-layout.md.*"
        )
        lines.append("")
        _append_perf_manual_markdown(lines, log_dir)
        _append_local_perf_baseline_markdown(lines, local_perf_cfg)
        print("\n".join(lines), file=out_fp)
        return

    job_rows = _local_job_rows_with_info(groups)

    lines.append("### Summary")
    lines.append("")
    _append_local_summary_grouped_markdown(lines, job_rows)
    lines.append(
        "*Failed and errored jobs only: detailed excerpts below. Passing jobs appear in the summary table only.*"
    )
    lines.append("")
    _append_perf_manual_markdown(lines, log_dir)
    _append_local_perf_baseline_markdown(lines, local_perf_cfg)

    for job_name, paths, info in job_rows:
        if _job_is_clean(info):
            continue
        lines.append(f"### Local job: `{_md_cell(job_name)}`")
        lines.append("")
        lines.append(
            "*完整日志：在 HTML 报告中点击 **查看完整日志** 展开内嵌全文，或本地打开下列文件。*"
        )
        rel = ", ".join(f"`{p.name}`" for p in paths)
        lines.append(f"- {rel}")
        lines.append("")

        fail_rows: list[list[str]] = []
        for node in info["failed_nodes"]:
            fail_rows.append(
                [
                    _md_cell(node),
                    _md_cell(info["failed_reasons"].get(node, "")),
                    _md_cell(info["failure_analyses"].get(node, "")),
                    _excerpt_md_cell(info["failure_excerpts"].get(node, "")),
                ]
            )
        for node in info["error_nodes"]:
            fail_rows.append(
                [
                    _md_cell(node) + " (ERROR)",
                    _md_cell(info["error_reasons"].get(node, "")),
                    _md_cell(info["error_analyses"].get(node, "")),
                    _excerpt_md_cell(info["failure_excerpts"].get(node, "")),
                ]
            )

        lines.append("#### Failures & errors")
        lines.append("")
        lines.append(
            render_markdown_table(
                ["Test node", "Log reason", "Analysis", "Excerpt (truncated)"],
                fail_rows,
            )
        )
        lines.append("")

    print("\n".join(lines), file=out_fp)


def _excerpt_pre_html(excerpt: str, max_chars: int = 8000) -> str:
    t = (excerpt or "").strip()
    if len(t) > max_chars:
        t = t[:max_chars] + "\n... [truncated]"
    return f'<pre class="log-excerpt">{html.escape(t)}</pre>'


def _th_labeled(icon_paths: str, text: str) -> str:
    return (
        "<th scope=\"col\">"
        '<span class="th-lbl">'
        f'{_svg_icon(icon_paths, size=16, extra_class="th-ico")}'
        f"<span>{html.escape(text)}</span>"
        "</span></th>"
    )


def _issue_row_data_attrs(
    *,
    issue_env: str = "local",
    issue_vllm_version: str = "",
    issue_vllm_omni_version: str = "",
    issue_build_commit: str = "",
) -> str:
    def aq(s: str) -> str:
        return html.escape(s or "", quote=True)

    return (
        f'data-issue-env="{aq(issue_env)}" '
        f'data-vllm-version="{aq(issue_vllm_version)}" '
        f'data-vllm-omni-version="{aq(issue_vllm_omni_version)}" '
        f'data-build-commit="{aq(issue_build_commit)}"'
    )


def _render_failures_table_html(
    info: dict[str, Any],
    *,
    report_context: str = "",
    issue_env: str = "local",
    issue_vllm_version: str = "",
    issue_vllm_omni_version: str = "",
    issue_build_commit: str = "",
) -> str:
    ctx_attr = html.escape(report_context, quote=True)
    row_ex = _issue_row_data_attrs(
        issue_env=issue_env,
        issue_vllm_version=issue_vllm_version,
        issue_vllm_omni_version=issue_vllm_omni_version,
        issue_build_commit=issue_build_commit,
    )
    parts: list[str] = [
        '<table class="fail-table">',
        "<thead><tr>",
        _th_labeled(_SVG_CODE, "Test node"),
        _th_labeled(_SVG_MSG, "Log reason"),
        _th_labeled(_SVG_SPARK, "Analysis"),
        _th_labeled(_SVG_LOG, "Log excerpt"),
        _th_labeled(_SVG_PLUS_ISSUE, "GitHub Issue"),
        "</tr></thead>",
        "<tbody>",
    ]
    for node in info["failed_nodes"]:
        parts.extend(
            [
                f"<tr {row_ex} data-report-context=\"{ctx_attr}\">",
                f'<td class="mono">{html.escape(node)}</td>',
                f'<td class="reason">{html.escape(info["failed_reasons"].get(node, ""))}</td>',
                f'<td class="analysis">{html.escape(info["failure_analyses"].get(node, ""))}</td>',
                '<td class="excerpt-cell">'
                f'{_excerpt_pre_html(info["failure_excerpts"].get(node, ""))}'
                "</td>",
                _github_issue_button_cell(),
                "</tr>",
            ]
        )
    for node in info["error_nodes"]:
        parts.extend(
            [
                f"<tr class=\"row-error\" {row_ex} data-report-context=\"{ctx_attr}\">",
                f'<td class="mono">{html.escape(node)} (ERROR)</td>',
                f'<td class="reason">{html.escape(info["error_reasons"].get(node, ""))}</td>',
                f'<td class="analysis">{html.escape(info["error_analyses"].get(node, ""))}</td>',
                '<td class="excerpt-cell">'
                f'{_excerpt_pre_html(info["error_excerpts"].get(node, ""))}'
                "</td>",
                _github_issue_button_cell(),
                "</tr>",
            ]
        )
    parts.append("</tbody></table>")
    return _table_wrap("\n".join(parts))


def _render_buildkite_section_html(
    build: dict[str, Any] | None,
    job_records: list[dict[str, Any]] | None,
    *,
    note: str | None,
    kanban_cfg: KanbanAssetsConfig,
) -> str:
    summary_inner: list[str] = []
    fail_inner = '<p class="note">无数据：未加载 Buildkite 步骤日志。</p>'

    if note:
        summary_inner.append(f'<p class="note">{html.escape(note)}</p>')
    elif build is None or job_records is None:
        summary_inner.append('<p class="note">Buildkite section not available.</p>')
    else:
        bn = int(build["number"])
        build_url = f"https://buildkite.com/{ORG}/{PIPELINE}/builds/{bn}"
        meta_lines: list[str] = [
            '<div class="meta">',
            f'<div><strong>Build:</strong> <a href="{html.escape(build_url)}">#{bn}</a></div>',
            f'<div><strong>State:</strong> {html.escape(str(build.get("state") or ""))}</div>',
            f'<div><strong>Message:</strong> {html.escape((build.get("message") or "")[:500])}</div>',
        ]
        co = (build.get("commit") or "")[:12]
        if co:
            meta_lines.append(f'<div><strong>Commit:</strong> {html.escape(co)}</div>')
        meta_lines.append("</div>")
        summary_inner = ["".join(meta_lines)]
        sum_rows = [_summary_row_for_bk_rec(r) for r in job_records]
        sum_row_cls = [
            f"summary-row summary-row--{_summary_row_kind_bk(r)}" for r in job_records
        ]
        summary_inner.append(
            _table_wrap(
                render_html_table(
                    ["Job", "Total", "Passed", "Failed", "Skipped", "Errors", "执行时间"],
                    sum_rows,
                    table_class="summary",
                    row_classes=sum_row_cls,
                )
            )
        )

        fail_blocks: list[str] = []
        for rec in job_records:
            if rec.get("log_error"):
                bits_bk_err = [
                    '<details class="job-fail-details job-fail-details-bk">',
                    '<summary class="job-fail-details-summary job-fail-details-summary-bk">',
                    _heading_html(
                        "h2",
                        _SVG_ALERT,
                        html.escape(f"Buildkite step: {rec['name']}"),
                    ),
                    '<p class="meta"><strong>Step link:</strong> '
                    f'<a href="{html.escape(rec["step_link"])}">open</a></p>',
                    "</summary>",
                    '<div class="job-fail-details-body">',
                    "<p class=\"note\"><strong>Log fetch failed:</strong> "
                    f"{html.escape(rec['log_error'][:600])}</p>",
                    "</div></details>",
                ]
                fail_blocks.append("\n".join(bits_bk_err))
                continue
            info = rec.get("info")
            if not info or _job_is_clean(info):
                continue
            bits_bk = [
                '<details class="job-fail-details job-fail-details-bk">',
                '<summary class="job-fail-details-summary job-fail-details-summary-bk">',
                _heading_html(
                    "h2",
                    _SVG_ALERT,
                    html.escape(f"Buildkite step: {rec['name']}"),
                ),
                '<p class="meta"><strong>Step link:</strong> '
                f'<a href="{html.escape(rec["step_link"])}">open</a></p>',
                "</summary>",
                '<div class="job-fail-details-body">',
                _heading_html(
                    "h3",
                    _SVG_LIST,
                    html.escape("Failures & errors"),
                    klass="section-failures",
                ),
                _render_failures_table_html(
                    info,
                    report_context=(
                        f"Buildkite scheduled nightly (main) · build #{bn} · step: {rec['name']}"
                    ),
                    issue_env="ci",
                    issue_vllm_version=(rec.get("ci_versions") or {}).get("vllm", ""),
                    issue_vllm_omni_version=(rec.get("ci_versions") or {}).get(
                        "vllm_omni", ""
                    ),
                    issue_build_commit=(rec.get("build_commit_short") or ""),
                ),
                "</div></details>",
            ]
            fail_blocks.append("\n".join(bits_bk))

        if fail_blocks:
            fail_inner = (
                '<p class="hint">点击各步骤标题可展开或折叠失败详情与日志摘录。</p>\n'
                + "\n".join(fail_blocks)
            )
        else:
            fail_inner = '<p class="note">当前无失败步骤，或各 Job 均无失败/错误摘录。</p>'

    return "\n".join(
        [
            '<section class="panel nightly-root nightly-root--buildkite">',
            _heading_html(
                "h2",
                _SVG_CLOUD,
                html.escape("Buildkite Test"),
                sub=html.escape("Latest scheduled nightly (main)"),
            ),
            _details_subcard(
                "Summary（各 Job 执行情况）",
                "\n".join(summary_inner),
                open_default=False,
                details_class="report-subcard--bk",
                icon_paths=_SVG_LIST,
            ),
            _details_subcard(
                "性能基线对比",
                _render_buildkite_perf_inner_html(kanban_cfg),
                open_default=False,
                details_class="report-subcard--bk-perf",
                icon_paths=_SVG_CHART_BARS,
            ),
            _details_subcard(
                "失败分析",
                fail_inner,
                open_default=False,
                details_class="report-subcard--bk-fail",
                icon_paths=_SVG_ALERT,
            ),
            "</section>",
        ]
    )


def _perf_rows_with_delta_markdown(sh: dict[str, Any]) -> list[list[str]]:
    rows = sh["rows"]
    drows: list[list[str]] | None = sh.get("delta_rows")
    if not drows:
        return rows
    out: list[list[str]] = []
    for i, row in enumerate(rows):
        dr = drows[i] if i < len(drows) else []
        out.append(
            [
                row[j] + (f" {dr[j]}" if j < len(dr) and (dr[j] or "").strip() else "")
                for j in range(len(row))
            ]
        )
    return out


def _append_perf_manual_markdown(lines: list[str], log_dir: Path) -> None:
    data = load_perf_manual_with_compare(log_dir)
    lines.append(f"## 性能测试结果 (`{PERF_MANUAL_FILENAME}`)")
    lines.append("")
    lines.append(f"- **路径:** `{data['path']}`")
    if data.get("compare_path"):
        lines.append(f"- **对比 (上一版):** `{data['compare_path']}`")
    lines.append("")
    st = data["status"]
    if st == "missing":
        lines.append(
            "*未找到该文件。同步日志时请一并复制（见 "
            "[../vllm-omni-nightly-local/references/nightly-local-log-fetch.md](../vllm-omni-nightly-local/references/nightly-local-log-fetch.md)）。*"
        )
        lines.append("")
        return
    if st == "no_openpyxl":
        lines.append("无法读取 .xlsx：请先安装 **openpyxl**（`pip install openpyxl`）。")
        lines.append("")
        return
    if st == "error":
        lines.append(f"*读取失败: {data['message']}*")
        lines.append("")
        return
    if data.get("message"):
        lines.append(f"*{data['message']}*")
        lines.append("")
    if not data["sheets"]:
        lines.append("*工作簿中无可用表格数据。*")
        lines.append("")
        return
    for sh in data["sheets"]:
        lines.append(f"### Sheet: `{_md_cell(sh['title'])}`")
        lines.append("")
        if sh.get("truncated_rows"):
            lines.append("*（行数过多，已截断。）*")
            lines.append("")
        lines.append(
            render_markdown_table(
                sh["headers"],
                _perf_rows_with_delta_markdown(sh),
            )
        )
        lines.append("")


def _perf_manual_inner_html(log_dir: Path) -> str:
    """Workbook path + tables for the Local · 性能分析 subcard (no outer panel)."""
    data = load_perf_manual_with_compare(log_dir)
    parts: list[str] = [
        '<p class="meta"><strong>文件:</strong> '
        f'<code>{html.escape(data["path"])}</code>'
        + (
            f' · <strong>对比:</strong> <code>{html.escape(data["compare_path"])}</code>'
            if data.get("compare_path")
            else ""
        )
        + "</p>"
    ]
    st = data["status"]
    if st == "missing":
        parts.append(
            '<p class="note">未找到该文件。同步集群日志时请一并复制 '
            "<code>nightly_perf_manual.xlsx</code> "
            "（见 vllm-omni-nightly-local <code>nightly-local-log-fetch</code>）。</p>"
        )
    elif st == "no_openpyxl":
        parts.append(
            '<p class="note">无法读取 .xlsx：请先安装 <code>openpyxl</code> '
            "（<code>pip install openpyxl</code>）。</p>"
        )
    elif st == "error":
        parts.append(f'<p class="note">读取失败：{html.escape(data["message"])}</p>')
    else:
        if data.get("message"):
            parts.append(f'<p class="hint">{html.escape(data["message"])}</p>')
        if not data["sheets"]:
            parts.append('<p class="note">工作簿中无可用表格数据。</p>')
        else:
            for sh in data["sheets"]:
                parts.append(
                    f'<h3 class="perf-sheet-title">{html.escape(sh["title"])}</h3>'
                )
                if sh.get("truncated_rows"):
                    parts.append(
                        '<p class="hint perf-truncate-hint">行数过多，仅显示前若干行。</p>'
                    )
                parts.append(
                    _table_wrap(
                        render_html_table(
                            sh["headers"],
                            sh["rows"],
                            table_class="perf-manual",
                            cell_suffixes=sh.get("delta_rows"),
                        )
                    )
                )
    return "\n".join(parts)


def _render_buildkite_note_html(note: str) -> str:
    inner = f'<p class="note">{html.escape(note)}</p>'
    return "\n".join(
        [
            '<section class="panel nightly-root nightly-root--buildkite">',
            _heading_html(
                "h2",
                _SVG_CLOUD,
                html.escape("Buildkite Test"),
                sub=html.escape("Latest scheduled nightly (main)"),
            ),
            _details_subcard(
                "Summary（各 Job 执行情况）",
                inner,
                open_default=False,
                details_class="report-subcard--bk",
                icon_paths=_SVG_LIST,
            ),
            _details_subcard(
                "失败分析",
                '<p class="note">无数据：未加载 Buildkite 步骤日志。</p>',
                open_default=False,
                details_class="report-subcard--bk-fail",
                icon_paths=_SVG_ALERT,
            ),
            "</section>",
        ]
    )


def emit_report_html(
    *,
    title: str,
    repo_root: Path,
    log_dir: Path,
    out_fp: Any,
    bk_build: dict[str, Any] | None = None,
    bk_jobs: list[dict[str, Any]] | None = None,
    bk_note: str | None = None,
    kanban_cfg: KanbanAssetsConfig | None = None,
    local_perf_cfg: LocalPerfResultConfig | None = None,
) -> None:
    groups = discover_job_logs(log_dir)
    if kanban_cfg is None:
        kanban_cfg = KanbanAssetsConfig(
            assets_dir=DEFAULT_KANBAN_ASSETS_DIR,
            repo_root=DEFAULT_KANBAN_REPO_ROOT,
        )
    if local_perf_cfg is None:
        local_perf_cfg = LocalPerfResultConfig()

    css = EDITORIAL_THEME_CSS

    body_parts: list[str] = [
        '<div class="top-bar"><div class="shell top-bar-inner">'
        '<div class="brand">'
        f'<div class="brand-mark">{_svg_icon(_SVG_CLIPBOARD, size=30, extra_class="brand-ico")}</div>'
        '<div class="brand-copy">'
        f"<h1>{html.escape(title)}</h1>"
        '<p class="tagline">Nightly test report</p>'
        "</div></div></div></div>",
        '<div class="shell">',
    ]

    body_parts.append(
        _render_buildkite_section_html(
            bk_build,
            bk_jobs,
            note=bk_note,
            kanban_cfg=kanban_cfg,
        )
    )

    local_chunks: list[str] = [
        '<section class="panel nightly-root nightly-root--local">',
        _heading_html(
            "h2",
            _SVG_SERVER,
            html.escape("Local Test"),
        ),
    ]
    job_rows: list[tuple[str, list[Path], dict[str, Any]]] = []
    if not groups:
        summary_body = (
            "<p class=\"note\">No job logs found under this directory. Confirm nightly jobs ran, copy logs "
            "(see vllm-omni-nightly-local references/nightly-local-log-fetch.md), "
            "and match references/nightly-local-log-layout.md.</p>"
        )
    else:
        job_rows = _local_job_rows_with_info(groups)
        summary_body = _render_local_summary_grouped_html(job_rows)
    local_chunks.append(
        _details_subcard(
            "Summary",
            summary_body,
            open_default=False,
            details_class="",
            icon_paths=_SVG_LIST,
        )
    )
    local_chunks.append(
        _details_subcard(
            "性能分析",
            _perf_manual_inner_html(log_dir),
            open_default=False,
            details_class="report-subcard--perf",
            icon_paths=_SVG_CHART_BARS,
        )
    )
    local_chunks.append(
        _details_subcard(
            "性能基线对比",
            _render_local_perf_baseline_inner_html(local_perf_cfg),
            open_default=False,
            details_class="report-subcard--local-perf-baseline",
            icon_paths=_SVG_CHART_BARS,
        )
    )

    fail_local_parts: list[str] = []
    if job_rows:
        full_log_i = 0
        for job_name, paths, info in job_rows:
            if _job_is_clean(info):
                continue
            log_files = ", ".join(p.name for p in paths)
            bits = [
                '<details class="job-fail-details">',
                '<summary class="job-fail-details-summary">',
                _heading_html(
                    "h2",
                    _SVG_ALERT,
                    html.escape(f"Failed local job: {job_name}"),
                ),
                _render_full_log_panel_html(paths, f"local-full-log-{full_log_i}"),
                "</summary>",
                '<div class="job-fail-details-body">',
                _heading_html(
                    "h3",
                    _SVG_LIST,
                    html.escape("Failures & errors"),
                    klass="section-failures",
                ),
                _render_failures_table_html(
                    info,
                    report_context=(
                        f"Local nightly_jobs · job: {job_name} · logs: {log_files}"
                    ),
                ),
                "</div></details>",
            ]
            fail_local_parts.append("\n".join(bits))
            full_log_i += 1
    if fail_local_parts:
        fail_inner_loc = (
            '<p class="hint">点击各 Job 标题可展开或折叠失败测试列表与日志摘录。</p>\n'
            + "\n".join(fail_local_parts)
        )
    else:
        fail_inner_loc = '<p class="note">当前无失败或错误需逐项分析。</p>'
    local_chunks.append(
        _details_subcard(
            "失败分析",
            fail_inner_loc,
            open_default=False,
            details_class="report-subcard--local-fail",
            icon_paths=_SVG_ALERT,
        )
    )
    local_chunks.append("</section>")
    body_parts.append("\n".join(local_chunks))

    body_parts.append("</div>")
    doc = _html_document(
        title,
        css,
        "\n".join(body_parts),
        tail=_github_issue_modal_and_script(),
    )
    print(doc, file=out_fp)


def _html_document(title: str, css: str, body: str, *, tail: str = "") -> str:
    t = html.escape(title)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<style>
{css}
</style>
</head>
<body>
{body}
{tail}
</body>
</html>
"""


def _resolve_buildkite_for_report(
    include: bool,
    build_no: int | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]] | None, str | None]:
    """Return ``(build, job_records, note)``. ``note`` set when section skipped or errored."""
    if not include:
        return None, None, None
    tok = _buildkite_token()
    if not tok:
        return None, None, (
            "Buildkite section skipped: set BUILDKITE_TOKEN or BUILDKITE_API_TOKEN "
            "to fetch the latest scheduled nightly on main (vllm/vllm-omni)."
        )
    try:
        bk_build = fetch_nightly_build(tok, build_no)
        bk_jobs = collect_nightly_job_log_analyses(bk_build, tok)
        return bk_build, bk_jobs, None
    except Exception as e:
        return None, None, f"Buildkite section failed: {e}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit HTML by default (use --html-report or stdout). "
        "Use Markdown only when explicitly requested (--markdown-report / --to-stdout markdown). "
        "Local nightly job logs plus optional Buildkite latest scheduled nightly (needs token).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root: default log dir is <repo-root>/logs/nightly_jobs; "
        "also shown in the report header (default: $REPO_ROOT env or cwd).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Log directory (default: <repo-root>/logs/nightly_jobs; "
        "repo-root from --repo-root, $REPO_ROOT, or cwd).",
    )
    parser.add_argument(
        "--html-report",
        type=Path,
        default=None,
        help="Write HTML report to this file.",
    )
    parser.add_argument(
        "--markdown-report",
        type=Path,
        default=None,
        help="Write Markdown report to this file (optional).",
    )
    parser.add_argument(
        "--to-stdout",
        choices=("html", "markdown"),
        default="html",
        help="Format when printing to stdout and no --html-report/--markdown-report (default: html).",
    )
    parser.add_argument(
        "--no-buildkite",
        action="store_true",
        help="Do not call Buildkite API (local logs only).",
    )
    parser.add_argument(
        "--buildkite-build",
        type=int,
        default=None,
        help="Pin Buildkite build number (default: latest scheduled nightly on main).",
    )
    parser.add_argument(
        "--kanban-assets-dir",
        type=Path,
        default=DEFAULT_KANBAN_ASSETS_DIR,
        help="Path to vllm-omni-kanban docs/assets/charts for Buildkite performance summary.",
    )
    parser.add_argument(
        "--kanban-repo-root",
        type=Path,
        default=DEFAULT_KANBAN_REPO_ROOT,
        help="Path to vllm-omni-kanban repo root; resolves docs/assets/charts and enables source validation.",
    )
    parser.add_argument(
        "--kanban-expected-remote",
        default=None,
        help="Expected kanban upstream remote name (for warning only), e.g. upstream.",
    )
    parser.add_argument(
        "--kanban-expected-branch",
        default=None,
        help="Expected kanban branch name (for warning only), e.g. main.",
    )
    parser.add_argument(
        "--kanban-raw-root",
        type=Path,
        default=None,
        help="Optional kanban raw perf artifact root (default: <kanban-repo-root>/data/buildkite_nightly_raw).",
    )
    parser.add_argument(
        "--kanban-refresh-from-raw",
        action="store_true",
        help="Opt-in: run kanban raw sync + generate_charts before reading docs/assets/charts history.",
    )
    parser.add_argument(
        "--local-perf-result-root",
        type=Path,
        default=None,
        help="Root directory containing timestamped local perf benchmark result directories "
        "(default: <kanban-repo-root>/data/local_nightly_raw when it exists).",
    )
    parser.add_argument(
        "--title",
        default="Nightly local test report",
        help="Report title.",
    )
    args = parser.parse_args()

    if args.html_report and args.markdown_report:
        print("Use only one of --html-report or --markdown-report.", file=sys.stderr)
        sys.exit(2)

    r_txt = os.environ.get("REPO_ROOT", "").strip()
    if args.repo_root is not None:
        repo = args.repo_root.resolve()
    elif r_txt:
        repo = Path(r_txt).resolve()
    else:
        repo = Path.cwd().resolve()

    log_dir = args.log_dir.resolve() if args.log_dir else default_log_dir(repo)

    bk_build, bk_jobs, bk_note = _resolve_buildkite_for_report(
        include=not args.no_buildkite,
        build_no=args.buildkite_build,
    )
    kanban_cfg = KanbanAssetsConfig(
        assets_dir=args.kanban_assets_dir.resolve() if args.kanban_assets_dir else None,
        repo_root=args.kanban_repo_root.resolve() if args.kanban_repo_root else None,
        expected_remote=(args.kanban_expected_remote or "").strip() or None,
        expected_branch=(args.kanban_expected_branch or "").strip() or None,
        raw_root=args.kanban_raw_root.resolve() if args.kanban_raw_root else None,
        refresh_from_raw=bool(args.kanban_refresh_from_raw),
    )
    if kanban_cfg.refresh_from_raw:
        refresh_note, refresh_warnings = _run_kanban_refresh_from_raw(
            kanban_cfg.repo_root,
            _resolve_kanban_raw_root(kanban_cfg),
        )
        kanban_cfg.refresh_note = refresh_note
        kanban_cfg.refresh_warnings = refresh_warnings
    local_perf_cfg = LocalPerfResultConfig(
        result_root=(
            args.local_perf_result_root.resolve()
            if args.local_perf_result_root
            else _default_local_perf_result_root(kanban_cfg.repo_root)
        ),
    )

    if args.html_report:
        out = args.html_report
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fp:
            emit_report_html(
                title=args.title,
                repo_root=repo,
                log_dir=log_dir,
                out_fp=fp,
                bk_build=bk_build,
                bk_jobs=bk_jobs,
                bk_note=bk_note,
                kanban_cfg=kanban_cfg,
                local_perf_cfg=local_perf_cfg,
            )
    elif args.markdown_report:
        out = args.markdown_report
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fp:
            emit_report(
                title=args.title,
                repo_root=repo,
                log_dir=log_dir,
                out_fp=fp,
                bk_build=bk_build,
                bk_jobs=bk_jobs,
                bk_note=bk_note,
                kanban_cfg=kanban_cfg,
                local_perf_cfg=local_perf_cfg,
            )
    else:
        if args.to_stdout == "markdown":
            emit_report(
                title=args.title,
                repo_root=repo,
                log_dir=log_dir,
                out_fp=sys.stdout,
                bk_build=bk_build,
                bk_jobs=bk_jobs,
                bk_note=bk_note,
                kanban_cfg=kanban_cfg,
                local_perf_cfg=local_perf_cfg,
            )
        else:
            emit_report_html(
                title=args.title,
                repo_root=repo,
                log_dir=log_dir,
                out_fp=sys.stdout,
                bk_build=bk_build,
                bk_jobs=bk_jobs,
                bk_note=bk_note,
                kanban_cfg=kanban_cfg,
                local_perf_cfg=local_perf_cfg,
            )


if __name__ == "__main__":
    main()
