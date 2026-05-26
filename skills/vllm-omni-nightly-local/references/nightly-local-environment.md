# Nightly local - cluster & container environment

## `REPO_ROOT`

- Export **`REPO_ROOT`** to the absolute path of the vLLM-Omni repository root **inside the Docker container**, or pass **`cd "$REPO_ROOT"`** inside **`bash -lc '...'`** when using **`docker exec`**.
- Paths are resolved from the container filesystem; bind-mount your checkout if the image does not include the repo.

## Python venv inside the container

On this HK/cluster setup, activate the project virtualenv **before** any repo commands (**`run_nightly_jobs.sh`**, pytest, or other tooling) inside **`docker exec … bash -lc '…'`** (or an interactive shell in the same container):

```bash
source /rebase/.venv/bin/activate
```

Use the **same** inner shell as **`cd "$REPO_ROOT"`** and the Hugging Face / vLLM exports in the next section.

## Hugging Face cache and vLLM

Before **`run_nightly_jobs.sh`** (or any local vLLM-Omni test script) in the **same** shell / **`docker exec bash -lc`**:

```bash
export HF_HOME="/home/models/"
unset HF_HUB_CACHE
unset TRANSFORMERS_CACHE
export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
```

- **`HF_HOME`** — root for HF datasets/cache layout on this cluster; must exist and match where **shared weights** are mounted (change only if the user or **`run_nightly_jobs.sh`** documents a different path).
- **`unset HF_HUB_CACHE`** / **`unset TRANSFORMERS_CACHE`** — drop inherited values so **`HF_HOME`** is not overridden by stale per-user cache paths.
- **`VLLM_ALLOW_LONG_MAX_MODEL_LEN`** — vLLM flag for long **`max_model_len`** in tests that need it.

Apply these **before** optional **`CUDA_VISIBLE_DEVICES`** selection and **before** **`cd "$REPO_ROOT" && bash tools/nightly/run_nightly_jobs.sh`**. (Ensure **`source /rebase/.venv/bin/activate`** has already run in that shell; see [Python venv inside the container](#python-venv-inside-the-container).)

## Default log location

- **`$REPO_ROOT/logs/nightly_jobs`** is the default **`LOG_DIR`** for runs and for the report script.
- Optional manual perf workbook on the same tree: **`$REPO_ROOT/logs/nightly_perf_manual.xlsx`** — copy it with the logs when syncing off-cluster (see [nightly-local-log-fetch.md](nightly-local-log-fetch.md)).
- If `tools/nightly/run_nightly_jobs.sh` writes elsewhere, sync that directory or symlink into `logs/nightly_jobs`, then pass **`--log-dir`** when running **`vllm-omni-test-report`** `nightly_local_log_report.py`.

## SSH connection name

- The **connection name** is whatever you pass to `ssh`: a **`Host`** entry in `~/.ssh/config` (e.g. `my-hk`) or `user@login.example.com`.
- Use `ssh -v` when diagnosing host key or proxy issues.

## Finding `JOBID` for `--overlap`

- List running jobs: `squeue -u YOUR_USER -t RUNNING` or `squeue -u YOUR_USER -t R`.
- **`srun --jobid=ID --overlap docker exec ...`** attaches a step and runs a container command **without** needing **`docker -it`**.
- **`srun --jobid=ID --overlap --pty bash`** is optional for debugging only when you need an interactive shell on the allocation.
- If multiple jobs are running, pick the correct **JOBID**; ask the operator when ambiguous.

## Fallback `srun` (no attach)

When no job id is used:

`srun -p q-fq9hpsac -w hk01dgx006 --gres=gpu:0 --mem-per-cpu=8G --pty  --job-name=ci_local_test`

- Adjust **partition**, **node** (`-w`), **gres**, and **mem** per site policy.
- After this step, use **`docker exec "<container>" bash -lc '...'`** (no **`-it`**) for normal commands.

## Docker

- **Default:** **`docker exec <container> bash -lc '<command>'`** or **`docker exec <container> <argv0> ...`** - no TTY required.
- **`docker exec -it`** only for debugging when you need an interactive shell.
- Requires access to the Docker socket (or rootless equivalent) on the host where **`srun`** / your shell runs.

## Non-interactive SSH

- Prefer **`ssh -o BatchMode=yes`** for automation so missing keys fail fast instead of hanging on a password prompt.
- Remote commands often need **`bash -lc '...'`** so **`module load slurm`** runs before **`squeue`** / **`srun`**.

## Long runs / SSH disconnect

Interactive **`ssh`** sessions send **SIGHUP** on disconnect; anything tied to that shell (including a foreground **`docker exec` → `run_nightly_jobs.sh`**) can exit. For **long local/cluster tests**, use one of the following.

### tmux or screen (recommended)

1. **`ssh`** to the cluster, then **`tmux new -s nightly`** (or **`screen -S nightly`**).
2. Run **`module load slurm`** (if needed), **`srun --jobid=… --overlap docker exec … bash -lc '…'`**, and **`run_nightly_jobs.sh`** **inside** that session.
3. **Detach** (tmux: `Ctrl-b` then `d`). The workload keeps running even if **`ssh`** closes.
4. Later: **`tmux attach -t nightly`** to monitor; **`tmux ls`** lists sessions.

`screen` equivalents: detach `Ctrl-a` `d`; reattach **`screen -r nightly`**.

### nohup inside the container

When you cannot use tmux (e.g. automation-only **`ssh` `BatchMode`** one-shot), start the script detached from the **inner** shell and capture output:

```bash
# Inside docker exec bash -lc ' ... ', after source /rebase/.venv/bin/activate, HF / vLLM / CUDA exports and cd "$REPO_ROOT":
mkdir -p "$REPO_ROOT/logs/nightly_jobs"
LOG="$REPO_ROOT/logs/nightly_jobs/nightly_runner.nohup.log"
nohup bash tools/nightly/run_nightly_jobs.sh >>"$LOG" 2>&1 &
echo "nightly jobs PID=$! log=$LOG"
```

- **PID** and **`tail -f "$LOG"`** (from a new **`docker exec`** or after re-**`ssh`**) are how you monitor progress.
- Ensure **`LOG_DIR`** for job artifacts still matches your reporting workflow (defaults under **`logs/nightly_jobs`**; see [Default log location](#default-log-location)).

### Caveats

- **Slurm / Kubernetes:** job lifetime is still bounded by the allocation — background only helps with **SSH/client** drops, not **`scancel`** or walltime expiry.
- **Docker:** avoid **`docker exec -it`** for long unattended runs; it expects a TTY.

## `run_nightly_jobs.sh`

- Path: **`tools/nightly/run_nightly_jobs.sh`** relative to the repo root. Forks or branches may differ.

<a id="cuda_visible_devices-empty-gpus"></a>

## `CUDA_VISIBLE_DEVICES` — empty GPUs via `nvidia-smi`

Run this on the **same machine** that will execute the tests (**inside `docker exec`**, after **`source /rebase/.venv/bin/activate`**, if the job runs in the container). The user specifies **`X`** = how many cards should be **free**.

**Idle (“empty”)** here means **`memory.used == 0`** and **`utilization.gpu == 0`** in `nvidia-smi`’s CSV query (some sites reserve a few MiB on “idle” GPUs — adjust the checks if needed).

Pick **`X`** indices, then export (comma‑separated, **no spaces** unless you intend multiple vars):

```bash
NUM_GPUS=2   # X — set from user input

empty=()
while IFS=',' read -r idx mem util; do
  idx="${idx// /}"
  mem="${mem// /}"
  util="${util// /}"
  m="${mem%%.*}"
  u="${util%%.*}"
  [[ "$m" =~ ^[0-9]+$ ]] || continue
  [[ "$u" =~ ^[0-9]+$ ]] || continue
  if (( m == 0 && u == 0 )); then
    empty+=("$idx")
  fi
done < <(nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits)

if (( ${#empty[@]} >= NUM_GPUS )); then
  chosen=("${empty[@]:0:NUM_GPUS}")
else
  echo "WARN: only ${#empty[@]} strictly empty GPU(s); falling back to lowest memory.use / util" >&2
  mapfile -t chosen < <(nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits \
    | sed 's/[[:space:]]*//g' | sort -t, -k2,2n -k3,3n | head -n "$NUM_GPUS" | cut -d, -f1)
fi

CUDA_VISIBLE_DEVICES=$(IFS=','; echo "${chosen[*]}")
export CUDA_VISIBLE_DEVICES
echo "Using CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
```

Then run the workload in **that shell** (after **`HF_HOME` / vLLM** exports from [Hugging Face cache and vLLM](#hugging-face-cache-and-vllm), e.g. same `bash -lc '…'` string):

```bash
export HF_HOME="/home/models/"
unset HF_HUB_CACHE
unset TRANSFORMERS_CACHE
export VLLM_ALLOW_LONG_MAX_MODEL_LEN="1"
cd "$REPO_ROOT" && bash tools/nightly/run_nightly_jobs.sh
```

(If **`CUDA_VISIBLE_DEVICES`** was set in the steps above, it remains in effect; if you already exported **HF / vLLM** vars in the same shell, omit duplicates.)

**Notes**

- If **Slurm** binds **`CUDA_VISIBLE_DEVICES`** for the step, merge site policy: either rely on the allocation or override only when allowed.
- **`nvidia-smi` inside the container** shows the GPUs **visible to that container** (may already be filtered).
- **MIG**, **multi-tenant** nodes, or **persistence mode** can show non‑zero `memory.used` on “empty” cards — prefer your cluster’s convention or raise thresholds after checking `nvidia-smi` once.
