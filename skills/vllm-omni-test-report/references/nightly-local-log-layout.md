# `nightly_jobs` log layout

## Default path

- On disk: **`.../logs/nightly_jobs`** (copy from cluster per [../vllm-omni-nightly-local/references/nightly-local-log-fetch.md](../vllm-omni-nightly-local/references/nightly-local-log-fetch.md)).
- **On your laptop**, `...` should be **`$REPO_ROOT`** (local vLLM-Omni checkout) so the tree is **`$REPO_ROOT/logs/nightly_jobs`** — the same path **`nightly_local_log_report.py`** uses by default when **`REPO_ROOT`** is set.

Sister artifact (same `logs/` directory): **`.../logs/nightly_perf_manual.xlsx`** — pull it together when syncing logs ([fetch steps](../vllm-omni-nightly-local/references/nightly-local-log-fetch.md)).

**Before pulling logs for the next run:** if you already have **`nightly_perf_manual.xlsx`** locally from the **previous** sync, copy it to **`nightly_perf_manual.prev.xlsx`** in the same `logs/` folder. That file becomes the baseline so the nightly report can show **↑/↓** percentages after the new `nightly_perf_manual.xlsx` arrives. If you skip this step, deltas are omitted until a `.prev` file exists.

Then **delete the local `nightly_jobs` directory** on your laptop (`rm -rf "$REPO_ROOT/logs/nightly_jobs"`) **before** `scp` / `rsync` / tarball extract, so old job folders are not merged with the new sync (details: [fetch steps](../vllm-omni-nightly-local/references/nightly-local-log-fetch.md)).

- **Nightly HTML / Markdown** (`scripts/nightly_local_log_report.py`): if the file is present, a **性能测试结果** section renders each worksheet as a table (requires **`pip install openpyxl`**). Pytest log discovery below still uses only `nightly_jobs/`.

## Discovery rules (`scripts/nightly_local_log_report.py`)

1. **Job subdirectories (preferred)**  
   If `LOG_DIR` contains **subdirectories**, each name is the **job name**. Concatenate all `*.log`, `*.out`, `*.txt` in that directory (sorted by name).

2. **Flat log files**  
   If `LOG_DIR` has **no** subdirectories, each `*.log` / `*.out` / `*.txt` at the top level is **one job** (stem = job name).

3. **Hidden** names (leading `.`) are ignored.

4. **HTML Summary grouping** — jobs are placed under **Omni / TTS / Diffusion** × **Perf, Acc, Function, doc, stability** when the name matches either:
   - **Prefix:** ``<omni|tts|diffusion|diff>_<perf|acc|function|doc|stability>`` (or the same two tokens in reverse order), case-insensitive, with spaces/hyphens like underscores; or
   - **Keywords** anywhere in the folder / stem: pillar substrings **diffusion**, word **omni**, word **tts**; dimension **accuracy** / **acc**, **performance** / **perf**, **function** / **functional**, **documentation** / **docs** / **doc**, **stability** / **stable** (see ``_classify_local_nightly_job`` in `scripts/nightly_local_log_report.py`).  
   Example: ``full_moon_Diffusion_X2I_A_T_Accuracy_Test`` → **Diffusion · Acc**. Names that do not resolve to both a pillar and a dimension appear under **其他**.

## Pytest parsing

- Expect `FAILED ...`, `ERROR ...`, and a session footer with `N passed`, `N failed`, etc.

## `run_nightly_jobs.sh`

If logs live elsewhere, pass `--log-dir` to the report script or symlink into `logs/nightly_jobs`.
