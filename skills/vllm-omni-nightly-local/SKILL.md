---
name: vllm-omni-nightly-local
description: On HK - SSH, Slurm, non-interactive docker exec (bash -lc): **`source /rebase/.venv/bin/activate`** inside the container before repo commands, then run `tools/nightly/run_nightly_jobs.sh` and write logs under logs/nightly_jobs. Sync logs and optional logs/nightly_perf_manual.xlsx to your laptop, then use vllm-omni-test-report report kind nightly + scripts/nightly_local_log_report.py — **default output HTML** (`--html-report`) unless the user explicitly asks for Markdown. Use when allocating GPUs, running cluster nightly jobs, or fetching nightly_jobs before offline analysis.
---

# vLLM-Omni Nightly Local (cluster run & log sync)

## Overview

1. **Login** - SSH, `squeue` / `srun --overlap`, `docker exec` without `-it` (see sections below).
2. **Run cases** — In the same container shell as the script: **`source /rebase/.venv/bin/activate`** (see [references/nightly-local-environment.md](references/nightly-local-environment.md)), then set **Hugging Face / vLLM** env (see below and that reference), optionally **`nvidia-smi`** → **`CUDA_VISIBLE_DEVICES`**, then **`bash tools/nightly/run_nightly_jobs.sh`** with **`LOG_DIR="$REPO_ROOT/logs/nightly_jobs"`**。**Long runs:** run inside **`tmux`** / **`screen`** on the cluster, or start the script with **`nohup`** and redirect stdout/stderr to a log file under **`$REPO_ROOT/logs/`**, so an **SSH disconnect does not stop** the workload (details: [references/nightly-local-environment.md](references/nightly-local-environment.md) — **Long runs / SSH disconnect**).
3. **Sync logs** — On your laptop, **(1)** if **`$REPO_ROOT/logs/nightly_perf_manual.xlsx`** exists from the last run, copy it to **`nightly_perf_manual.prev.xlsx`** (baseline for report ↑/↓). **(2)** **Remove the local** **`$REPO_ROOT/logs/nightly_jobs`** tree (`rm -rf`) so the new pull does not mix old job folders with the latest run. **(3)** Copy `nightly_jobs` and **`nightly_perf_manual.xlsx`** into **`$REPO_ROOT/logs/`**: [references/nightly-local-log-fetch.md](references/nightly-local-log-fetch.md).

**Analyze and write the HTML test report** in **[vllm-omni-test-report](../vllm-omni-test-report/SKILL.md)** (**report kind nightly**): `export REPO_ROOT=/path/to/local/vllm-omni` then `python scripts/nightly_local_log_report.py --html-report ...` (defaults to **`$REPO_ROOT/logs/nightly_jobs`**; pass **`--log-dir`** only if you used a different tree).

## Required user inputs

| Input | Meaning |
|-------|---------|
| **SSH connection name** | `Host` alias or `user@host`. |
| **Slurm username** | For `squeue -u ...`. |
| **Docker container name** | For `docker exec`. |
| **Empty GPU count** | Optional but recommended before **`run_nightly_jobs.sh`**: how many **free** GPUs to use (**`X`**). The agent runs **`nvidia-smi`**, picks **`X`** indices with **no** (or minimal) load, and **`export CUDA_VISIBLE_DEVICES=…`** in the **same** shell / **`docker exec bash -lc`** as the script. See **§2** and the section **`CUDA_VISIBLE_DEVICES` — empty GPUs** in [references/nightly-local-environment.md](references/nightly-local-environment.md). |

Optional: **`REPO_ROOT`** inside the container.

---

## 1. Login environment

### 1.1 SSH

```bash
ssh -v "<SSH_CONNECTION_NAME>"
```

Load **`module load slurm`** (or site equivalent) before **`srun`** if needed.

### 1.2 Find JOBID

```bash
SLURM_USER="<username>"
squeue -u "$SLURM_USER" -t RUNNING -h -o "%i"
```

Confirm **JOBID** when multiple rows exist.

### 1.3 Run in container (no TTY)

```bash
JOBID="<chosen_jobid>"
srun --jobid="$JOBID" --overlap docker exec "<CONTAINER_NAME>" bash -lc '<commands>'
```

Nightly one-liner:

```bash
srun --jobid="$JOBID" --overlap docker exec "<CONTAINER_NAME>" bash -lc 'source /rebase/.venv/bin/activate && export REPO_ROOT=/path/to/vllm-omni && cd "$REPO_ROOT" && bash tools/nightly/run_nightly_jobs.sh'
```

### 1.4 New allocation if no JOBID

```bash
srun -p q-fq9hpsac -w hk01dgx006 --gres=gpu:0 --mem-per-cpu=8G --pty  --job-name=ci_local_test
```

Then `docker exec "<CONTAINER_NAME>" bash -lc '<commands>'`.

### 1.5 Optional: `docker exec -it` for debugging only

### 1.6 Agent: BatchMode SSH

```bash
ssh -o BatchMode=yes -o ConnectTimeout=30 "<SSH_CONNECTION_NAME>" \
  "bash -lc 'type module >/dev/null 2>&1 && module load slurm 2>/dev/null; squeue -u \"<SLURM_USER>\" -t RUNNING -h -o \"%i\"'"

ssh -o BatchMode=yes -o ConnectTimeout=120 "<SSH_CONNECTION_NAME>" \
  "bash -lc 'type module >/dev/null 2>&1 && module load slurm 2>/dev/null; srun --jobid=\"<JOBID>\" --overlap docker exec \"<CONTAINER_NAME>\" bash -lc \"<INNER_CMD>\"'"
```

Details: [references/nightly-local-environment.md](references/nightly-local-environment.md).

---

## 2. Run test cases

**Before** `bash tools/nightly/run_nightly_jobs.sh` (inside the same **`docker exec … bash -lc '…'`** or interactive shell on the node):

0. **Python venv** (required inside the container) — run first in that inner shell:

   ```bash
   source /rebase/.venv/bin/activate
   ```

   Details: [references/nightly-local-environment.md](references/nightly-local-environment.md) (**Python venv inside the container**).

1. **Model / HF / vLLM environment** (required unless the user gives a different site policy) — same shell as the script:

   ```bash
   export HF_HOME="/home/models/"
   unset HF_HUB_CACHE
   unset TRANSFORMERS_CACHE
   export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
   ```

   Details: [references/nightly-local-environment.md](references/nightly-local-environment.md) (**Hugging Face cache and vLLM**).

2. Ask the user for **`X`** = number of **empty / free** GPUs to use (or use a value they already gave in **Required user inputs**).
3. Run **`nvidia-smi`**, select **`X`** GPU indices that are **idle** (typically **0 MiB** used and **0%** util — site-specific thresholds in the reference), then set:
   ```bash
   export CUDA_VISIBLE_DEVICES='<comma-separated GPU indices>'
   ```
4. **In that same environment**, `cd` to **`$REPO_ROOT`** and run **`bash tools/nightly/run_nightly_jobs.sh`** (or your local test entrypoint).

Copy-paste patterns and fallback when fewer than **`X`** GPUs are strictly empty: [references/nightly-local-environment.md](references/nightly-local-environment.md) (**`CUDA_VISIBLE_DEVICES` — empty GPUs**).

Example inner command (replace placeholders; **`X`** and device list come from **`nvidia-smi`** selection):

```bash
srun --jobid="$JOBID" --overlap docker exec "$CONTAINER_NAME" bash -lc '
  source /rebase/.venv/bin/activate
  export REPO_ROOT=/path/to/vllm-omni
  export HF_HOME="/home/models/"
  unset HF_HUB_CACHE
  unset TRANSFORMERS_CACHE
  export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
  export CUDA_VISIBLE_DEVICES="0,1"
  cd "$REPO_ROOT" && bash tools/nightly/run_nightly_jobs.sh
'
```

(`CUDA_VISIBLE_DEVICES` shown as `"0,1"` only for illustration — **derive from `nvidia-smi`, do not hardcode** unless the user insists. **`HF_HOME`** must match the cluster mount for shared models; if the user specifies another path, use that instead.)

### 2.1 Background / resilient shell (recommended when tests run for a long time)

- **Preferred:** open **`tmux new -s nightly`** (or **`screen`**) *before* **`srun` / `docker exec`**, run the full **`§2`** command inside that session, then **detach** (`Ctrl-b` `d` in tmux). Re-attach later with **`tmux attach -t nightly`** to watch progress.
- **Alternative:** inside **`docker exec … bash -lc '…'`**, start the nightly script with **`nohup`** and append logs to a file under **`$REPO_ROOT/logs/`** (see copy-paste in [references/nightly-local-environment.md](references/nightly-local-environment.md)).

## 3. Sync logs off-cluster

Follow **[references/nightly-local-log-fetch.md](references/nightly-local-log-fetch.md)** (scp / rsync / tarball). Include **`logs/nightly_perf_manual.xlsx`** when it exists on the server.

---

## Agent workflow

1. Collect SSH name, Slurm user, container name, and **optional `X` empty GPUs** for **`CUDA_VISIBLE_DEVICES`**; do not guess **JOBID** when ambiguous.
2. Run sections **1–2**; **inside the container**, run **`source /rebase/.venv/bin/activate`** first; **before** the nightly/local test script, set **HF / vLLM** env vars (**§2 step 1**). Then, if **`X`** is set (or the user asks for GPU selection), run **`nvidia-smi`**, **`export CUDA_VISIBLE_DEVICES`**, and run the script in the **same** environment. For multi-hour jobs, use **`§2.1`** (**tmux** / **`nohup`**) so a dropped SSH session does not kill the run.
3. Verify files under `logs/nightly_jobs` (and `logs/nightly_perf_manual.xlsx` when your workflow produces it).
4. For **fetch** to a laptop: **(a)** copy **`nightly_perf_manual.xlsx` → `nightly_perf_manual.prev.xlsx`** when baselines are needed; **(b)** **`rm -rf` local `logs/nightly_jobs`** before sync (see [references/nightly-local-log-fetch.md](references/nightly-local-log-fetch.md)); **(c)** then pull. For **HTML report**, point to **vllm-omni-test-report** `nightly_local_log_report.py` and layout [../vllm-omni-test-report/references/nightly-local-log-layout.md](../vllm-omni-test-report/references/nightly-local-log-layout.md).

## References

- Fetch logs (scp / rsync / tar): [references/nightly-local-log-fetch.md](references/nightly-local-log-fetch.md)
- Environment notes: [references/nightly-local-environment.md](references/nightly-local-environment.md)
