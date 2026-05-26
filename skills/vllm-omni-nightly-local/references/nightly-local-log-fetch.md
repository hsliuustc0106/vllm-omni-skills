# Fetch nightly logs to your laptop

Part of **vllm-omni-nightly-local**. Pull **`nightly_jobs`** (and, when present, **`nightly_perf_manual.xlsx`**) from the cluster/container **before** running **`vllm-omni-test-report`** `scripts/nightly_local_log_report.py` on your machine.

**Default destination on your laptop:** write into **`$REPO_ROOT/logs/`** (same layout as on the cluster: **`nightly_jobs/`** + optional **`nightly_perf_manual.xlsx`**). Here **`REPO_ROOT`** is the root of your **local** vLLM-Omni checkout. That matches **`nightly_local_log_report.py`** defaults: it uses **`$REPO_ROOT/logs/nightly_jobs`** when **`REPO_ROOT`** is set, otherwise **`logs/nightly_jobs`** under the current working directory — so you can omit **`--log-dir`** after a fetch into that tree.

## Performance workbook: snapshot before pull (for ↑/↓ in the report)

If **`$REPO_ROOT/logs/nightly_perf_manual.xlsx`** is already on your laptop from the **last** fetch, copy it to **`$REPO_ROOT/logs/nightly_perf_manual.prev.xlsx`** in the same `logs/` directory **before** you remove old job logs or run `scp`, `rsync`, or the tarball step below. After the pull, the new `nightly_perf_manual.xlsx` overwrites the current file; `.prev` stays as the comparison baseline (see [../vllm-omni-test-report/references/nightly-local-log-layout.md](../vllm-omni-test-report/references/nightly-local-log-layout.md)). Skip if you do not have a prior workbook yet.

## Clear local `nightly_jobs` before pull (recommended)

**Delete the existing *local* job log tree** before the new sync so you do not **mix historical job directories** with the latest cluster run (avoids duplicate or stale jobs in **`nightly_local_log_report.py`**).

```bash
REPO_ROOT="${REPO_ROOT:-/path/to/local/vllm-omni}"
rm -rf "$REPO_ROOT/logs/nightly_jobs"
```

- **Scope:** your **laptop** checkout only; nothing on the cluster/container is removed.
- **Optional keep:** rename instead of delete, e.g. `mv "$REPO_ROOT/logs/nightly_jobs" "$REPO_ROOT/logs/nightly_jobs.bak.$(date +%Y%m%d%H%M)"`, if you need an archive.

Run this **after** saving **`nightly_perf_manual.prev.xlsx`** when applicable (see above), and **before** `scp` / `rsync` / tarball **extract**. You should still clear **`nightly_jobs`** even when you skip the workbook snapshot (no prior `.xlsx`).

## What to copy

- Remote path (inside container): **`$REPO_ROOT/logs/nightly_jobs`** (layout: [../vllm-omni-test-report/references/nightly-local-log-layout.md](../vllm-omni-test-report/references/nightly-local-log-layout.md)).
- Same `logs/` directory, optional spreadsheet: **`$REPO_ROOT/logs/nightly_perf_manual.xlsx`** (pull it together with the job logs so local offline analysis has the same artifact).
- If your site bind-mounts that tree on the host, sync **that host path** instead.

## scp (recursive)

```bash
# Local checkout root — same as REPO_ROOT for nightly_local_log_report.py (adjust path if unset).
REPO_ROOT="${REPO_ROOT:-/path/to/local/vllm-omni}"
# REMOTE_LOGS = remote repo's `logs/` directory (host or container bind-mount).
REMOTE_LOGS="user@remote_host:/path/on/host/repo/logs"
mkdir -p "$REPO_ROOT/logs"
# After .prev.xlsx (if used) and rm -rf nightly_jobs — see sections above.
rm -rf "$REPO_ROOT/logs/nightly_jobs"
scp -r "${REMOTE_LOGS}/nightly_jobs" "$REPO_ROOT/logs/"
scp "${REMOTE_LOGS}/nightly_perf_manual.xlsx" "$REPO_ROOT/logs/"
```

If `nightly_perf_manual.xlsx` does not exist yet on the server, the second `scp` will fail; re-run it after the file is generated.

## rsync

```bash
REPO_ROOT="${REPO_ROOT:-/path/to/local/vllm-omni}"
REMOTE_LOGS="user@remote_host:/path/on/host/repo/logs"
# After .prev.xlsx (if used) and clearing old tree — see sections above.
rm -rf "$REPO_ROOT/logs/nightly_jobs"
mkdir -p "$REPO_ROOT/logs/nightly_jobs"
rsync -avz -e ssh "${REMOTE_LOGS}/nightly_jobs/" "$REPO_ROOT/logs/nightly_jobs/"
rsync -avz -e ssh "${REMOTE_LOGS}/nightly_perf_manual.xlsx" "$REPO_ROOT/logs/"
```

## Tarball via SSH + srun + docker

Pack both the job log tree and the spreadsheet in one archive. On **GNU tar** (typical in Linux containers), missing `nightly_perf_manual.xlsx` does not abort the archive:

```bash
ssh -o BatchMode=yes "<SSH_CONNECTION_NAME>" \
  "bash -lc 'type module >/dev/null 2>&1 && module load slurm 2>/dev/null; srun --jobid=\"<JOBID>\" --overlap docker exec \"<CONTAINER_NAME>\" tar czf - --ignore-failed-read -C \"<REPO_ROOT_IN_CONTAINER>\" logs/nightly_jobs logs/nightly_perf_manual.xlsx'" \
  > nightly_perf_logs.tgz
REPO_ROOT="${REPO_ROOT:-/path/to/local/vllm-omni}"
# After .prev.xlsx (if used): drop stale local job tree so the archive does not merge with old runs.
rm -rf "$REPO_ROOT/logs/nightly_jobs"
mkdir -p "$REPO_ROOT" && tar xzf nightly_perf_logs.tgz -C "$REPO_ROOT"
```

- After extract: job logs are **`$REPO_ROOT/logs/nightly_jobs`** (same default **`--log-dir`** target as **`nightly_local_log_report.py`** when **`REPO_ROOT`** is set).
- The spreadsheet (if it was present on the server) lands at **`$REPO_ROOT/logs/nightly_perf_manual.xlsx`**.

## Generate report (after logs are local)

From **`skills/vllm-omni-test-report/`** (see [../vllm-omni-test-report/SKILL.md](../vllm-omni-test-report/SKILL.md), report kind **nightly**):

```bash
export REPO_ROOT="/path/to/local/vllm-omni"   # must match the tree you synced into
python scripts/nightly_local_log_report.py --html-report ./nightly-report.html
# Same as: --log-dir "$REPO_ROOT/logs/nightly_jobs"
```
