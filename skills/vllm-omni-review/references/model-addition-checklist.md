# New Model Addition Review Checklist

Quick-reference checklist for PRs that add a new omni model (TTS, audio, multimodal pipeline). Use after reading the PR diff and body. Complements [diffusion-checklist.md](diffusion-checklist.md) (which covers diffusion/image/video models specifically).

---

## Blocking Gate: Profiling + Baseline Comparison

**New model PRs MUST include two pieces of evidence before approval. Missing either is a REQUEST_CHANGES blocker.**

### A. Detailed Profiling (implementation bug detection)

"It runs" is not enough. The contributor must run a profiler against the implementation to surface hidden bugs — kernels that silently fail, memory patterns that waste VRAM, or ops that fall back to CPU.

**Required profiling dimensions:**

| Dimension | Tool | What to check |
|-----------|------|---------------|
| **Kernel execution** | `torch.profiler.profile()` + Chrome trace, or `nsys` | All ops execute on the expected device (no silent CPU fallback). No `aten::copy` storms between CPU/GPU. No unexplained CPU time in the hot path. |
| **Memory** | `torch.cuda.memory_stats()`, `nvidia-smi`, or `torch.cuda.memory_summary()` | Peak VRAM at rest and under load. No memory leaks across repeated inferences. No `torch.cuda.empty_cache()` calls in the hot path (a sign of fragmentation workarounds). |
| **CUDA kernel launch** | `torch.profiler.profile()` (CUDA time) | No excessive kernel launch overhead (many tiny ops). Kernels achieve reasonable GPU utilization. |
| **Precision** | Manual inspection of intermediate tensors | No unexpected `NaN`/`inf` values in hidden states. fp16/bf16 paths produce values within tolerance of fp32. |

**What to flag as potential bugs from profiling:**

- `aten::copy` or `aten::to` in the forward pass (unintended device/host transfers)
- `CUDA kernel launch` time >> `CUDA kernel` time (kernel launch bottleneck)
- `cudaMalloc`/`cudaFree` inside the forward pass (dynamic allocation in hot path)
- `cudaStreamSynchronize` or `cudaDeviceSynchronize` calls (unintended sync points)
- Any op taking >20% of total step time when it shouldn't be on the critical path
- GPU utilization < 60% for compute-bound models
- `cpu_self` time > 10% of `cuda_self` time in the forward pass

**Format:** The contributor must include:
1. A Chrome trace screenshot or timeline summary showing the top 10 ops by CUDA time
2. Peak VRAM measurement (at rest + under load with batch_size=1)
3. A brief statement confirming no anomalies or listing anomalies found + explained

### B. Baseline Performance Comparison

The new implementation must be compared against the canonical upstream implementation on the same hardware with the same inputs.

**Acceptable baselines (in priority order):**
1. Official model repo (e.g. GitHub release from the model author)
2. HuggingFace transformers/diffusers pipeline
3. Another established vLLM implementation (for model upgrades)

**Required comparison metrics:**

| Metric | Minimum | Preferred |
|--------|---------|-----------|
| End-to-end wall time | batch_size=1, same prompt | batch_size=1,4,8 |
| Peak VRAM | Single measurement | Before/after warmup, batch_size=1,4 |
| Output quality | Visual/audio comparison for identical inputs | Quantitative metric (PSNR, SSIM, MCD, WER, etc.) |
| TTFT / RTF | Single measurement | At 3+ concurrency levels |

**Format:** A comparison table with at minimum three columns: Metric, Baseline, This PR. Example:

| Metric | Official Repo (HF diffusers) | This PR (vllm-omni) | Delta |
|--------|------------------------------|----------------------|-------|
| Wall time (bs=1) | 12.3s | 11.8s | -4% |
| Peak VRAM | 8.2 GB | 7.9 GB | -4% |
| Output PSNR | 31.2 dB | 31.1 dB | -0.1 dB |

**Regression rules:**
- **Latency regression > 10%** → must be explained and justified (e.g., "vLLM scheduler overhead amortized at higher batch sizes")
- **VRAM regression > 5%** → flagged as blocking unless justified
- **Output quality regression** (any visible/audible degradation) → blocking
- **Any concurrency level with throughput regression** → must be explained

**Graceful degradation for baseline comparison:**
- If the upstream code doesn't compile or run on the available hardware: document the attempt, explain the blocker, and fall back to measuring against a known-good vllm-omni main branch
- If the model has no upstream implementation: state this explicitly and provide the profiling evidence (Gate A) at minimum

---

## Quick Red Flags (scan first)

| # | Red Flag | Action |
|---|----------|--------|
| 1 | No profiling data or baseline comparison in PR body | **Blocking.** Request profiling trace + baseline table before further review |
| 2 | PR body lists files/architectures not present in diff | Request PR description update; flag as incomplete |
| 3 | `__all__` re-exports private `_`-prefixed functions | These shouldn't be public API |
| 4 | Same string constant defined in 3+ files | Consolidate to single source |
| 5 | "backward-compat alias" comment in brand-new code | Drop the alias |
| 6 | `del unused_param` inside function body | Remove the parameter from the signature |

---

## Dimension 1: PR Description vs Diff Integrity

The most common issue in new-model PRs is the description claiming more than the diff delivers.

- [ ] **PR body file list matches `git diff --name-only`.** Every file path mentioned in the description must appear in the diff. Common mismatches: missing model variants (e.g. 2.6 mentioned but only 4.5 present), missing stage configs, missing stage input processors.
- [ ] **Claimed architecture count matches registry entries.** If the body says "8 architectures registered," count the actual `_OMNI_MODELS` entries added in `registry.py`.
- [ ] **Stage config YAMLs reference existing files.** Any `custom_process_input_func` paths, `pipeline:` keys, and model arch strings must resolve to files/entries in the diff.
- [ ] **Example README modes match implemented code.** If the README documents 15 modes but `run_curl.sh` implements 3, flag it.

---

## Dimension 2: Dead Code Scan (model-addition specific)

### 2.1 Dead `forward()` in Stage Modules

When a model uses a custom generation path (e.g. `FlowLoss.sample()`, `CFM.sample()`), the `nn.Module.forward()` may be left over from training code.

```python
# DEAD: only self.flowloss.sample() is called, never self.flowloss(...)
class FlowLoss(nn.Module):
    def forward(self, cond, target, latent_history, mask, patch_size):
        return self.cfm(...)  # never invoked at inference
```

**Scan for:** Any `nn.Module` subclass where only a non-`forward` method is called.

### 2.2 Dead Factory / Builder Functions

```python
# DEAD: ming_tts_llm.py constructs Aggregator(...) directly
def build_ming_aggregator(cfg: MingTTSConfig) -> Aggregator:
    return Aggregator(in_channels=cfg.latent_dim, ...)
```

**Scan for:** Functions in `__all__` with zero call sites in the diff.

### 2.3 Dead Wrapper Methods

```python
# DEAD: CustomProcessMixin already registered self.preprocess
def preprocess_input(self, input_ids, input_embeds, **info_dict):
    return self.preprocess(input_ids, input_embeds, **info_dict)
```

**Scan for:** Methods whose body is a single delegation to another method with identical signature.

### 2.4 Dead Branch Guards (key never set)

```python
# DEAD: _ming_payload_stripped is never set to True anywhere in the diff
stripped = bool(info.get("_ming_payload_stripped", False))
if stripped:
    raise RuntimeError(...)  # unreachable
```

**Scan for:** Dictionary keys checked in `if` branches that are never assigned.

### 2.5 Unused Parameters

```python
def pad_prompt_waveform(waveform, *, patch_size, sample_rate, frame_hop):
    del frame_hop  # parameter accepted but immediately discarded
```

**Scan for:** `del <param_name>` at the top of a function body, or parameters never read.

---

## Dimension 3: Copy-Paste Detection

### 3.1 String Constants Defined in Multiple Files

The most frequent copy-paste issue in multi-stage pipelines: the same string key is defined independently in each stage's file instead of being imported from a shared source.

```
MING_STOP_REASON_KEY = "ming_stop_reason"
  ├── patch_emission.py (canonical)
  ├── ming_tts.py (duplicate)
  ├── ming_tts_audio_vae.py (duplicate)
  └── stage_input_processors/ming_tts.py (duplicate)
```

**Scan for:** `grep -n "^[A-Z_]+ = \"" <diff>` and check for repeated RHS string values across files.

### 3.2 Cross-Module Validation Duplication

```python
# Same geometry check in both AudioVAE.__init__ and validate_ming_tts_config()
# modeling_audio_vae.py:
if enc_kwargs["input_dim"] != hop_size: raise ValueError(...)
# validation.py:
if enc_input_dim != enc_hop_size: raise ValueError(...)
```

**Scan for:** Similar assertions with similar error messages in both a model `__init__` and a `validate_*` function.

### 3.3 Near-Identical Shape Coercion Functions

```python
# patch_emission.py
def _coerce_latent_history(value, *, device, dtype, cfg): ...
# ming_tts_audio_vae.py
def _coerce_latent_chunk(latent, *, device, dtype, latent_dim, patch_size): ...
```

Both reshape 2D→3D with dimension validation. One can call the other or they can share a helper.

---

## Dimension 4: Registry and Config Consistency

- [ ] **Pipeline registry model_type matches deploy YAML `pipeline:` key.** If a deploy YAML declares `pipeline: minicpmo_4_5`, the pipeline registry must have a `"minicpmo_4_5"` entry.
- [ ] **Every architecture in `_OMNI_MODELS` has a corresponding file.** E.g. `"MingLLMModel": ("ming_tts", "ming_tts_llm", ...)` means `ming_tts/ming_tts_llm.py` must exist and export `MingLLMModel`.
- [ ] **Deploy YAML consistency.** If 3 deploy variants exist, all 3 should either declare `pipeline:` or all should rely on auto-detection. Mixed conventions are fragile.
- [ ] **`hf_config_predicate` is correct for sibling model generations.** If an older generation (e.g. 2.6) shares `architectures=["MiniCPMO"]` with a newer one (e.g. 4.5), the predicate must reliably disambiguate them (e.g. via `version` field).

---

## Dimension 5: Import Hygiene

- [ ] **Imports used only for `__all__` re-export.** Constants imported into `config_<model>.py` solely to list in `__all__` should be noted. Prefer importing from the canonical source directly.
- [ ] **Module-level side effects.** `_install_torchaudio_soundfile_shim()` called at import time — acceptable for deployment-critical shims but should be documented.
- [ ] **No redundant `import os` (or similar) inside function bodies when already at module top.**

---

## Dimension 6: Examples and Shell Scripts

- [ ] **Shell script modes match documentation.** `run_curl.sh` / `run_server.sh` should support every mode the README documents.
- [ ] **`os.environ` access in inline Python heredocs.** Shell variables must be `export`ed before a `python <<'PY'` heredoc can read them via `os.environ`.
- [ ] **Hardcoded `/tmp/` paths use unique names** or `mktemp` to avoid concurrent-invocation collisions.

---

## Dimension 7: Accuracy Testing

Output correctness is the highest bar for any model PR. "It runs" is not enough.

### 7.1 Output Validation

- [ ] At least one test compares generated output against a known-good reference
- [ ] For audio/speech models: output is valid WAV/PCM, non-empty, at the correct sample rate
- [ ] For image/video models: output dimensions match expectations, no blank/black frames
- [ ] Every test has at least one assertion on response content (not just crash-smoke)

### 7.2 Determinism

- [ ] If the model is expected to be deterministic, seeds are fixed and verified
- [ ] `torch.backends.cudnn.deterministic` or equivalent is set if required
- [ ] At least two runs with the same seed produce identical output
- [ ] Non-deterministic ops are documented as such (especially on NPU/ROCm)

### 7.3 Tolerance and Numeric Stability

- [ ] Numeric tolerances (`atol`, `rtol`) are explicitly stated, not just defaulted
- [ ] No `NaN` or `inf` values in intermediate tensors (check `non-finite` guards exist)
- [ ] Mixed-precision paths (fp16, bf16) produce output within tolerance of fp32 baseline
- [ ] For TTS models: RTF (real-time factor) is measured and stated

### 7.4 Upstream Parity

- [ ] If an upstream implementation exists (diffusers, HF transformers, original repo):
  - Output compared side-by-side with the upstream at same seed/inputs
  - Differences are documented and justified (precision, kernel choice, etc.)
  - Any known quality regressions are listed as "known limitations"

---

## Dimension 8: Performance Comparison (Detailed Checklist)

**The blocking gate above is the minimum bar.** This dimension provides the detailed checklist for evaluating the quality of submitted performance data. Use it to assess whether the contributor's baseline comparison and profiling meet the required standard.

### 8.1 Measurement Methodology

- [ ] Hardware is fully specified: GPU model, GPU count, VRAM per GPU, CPU, RAM
- [ ] Software versions documented: torch, CUDA, vllm, vllm-omni
- [ ] Warmup: at least 1 warmup run excluded from measurements
- [ ] Measured runs: at least 3 measurements, reported as mean ± stddev (not just best single run)
- [ ] Environment variables documented (`PYTORCH_CUDA_ALLOC_CONF`, etc.)

**Good example — PR #3882** ([VoxCPM2] Batch CFM decode):
> Online serving benchmark on 1x H20, `openbmb/VoxCPM2`, same prompt and `max_num_seqs=8`.
> Values below are the average of two steady-state measurement rounds.

Specifies hardware (H20), model, config, and measurement method. **Still missing:** torch/CUDA versions, stddev.

**Good example — PR #3878** ([Perf] Qwen3-Omni optimization):
> RTF and req/s tables across 5 concurrency levels (1, 4, 8, 16, 32).

Covers the full concurrency range so scaling behavior is visible. **Still missing:** hardware spec, software versions, warmup count.

### 8.2 Comparison Baseline (see blocking gate for requirements)

- [ ] If replacing an existing model: before/after on same hardware, same inputs
- [ ] If new model: comparison against original upstream repo on same hardware
- [ ] Baseline numbers are from the same measurement methodology (not cherry-picked)
- [ ] Any regression at any concurrency level is explained, not ignored

**Example — PR #3878:** Reports req/s drops at concurrency=1 (-20%) without explanation. If a metric regresses at any level, explain why or fix it.

### 8.3 Metrics to Report

- [ ] **Latency:** TTFT (time to first token) for AR models, end-to-end wall time
- [ ] **Throughput:** tokens/s or requests/s at batch=1 and at saturation
- [ ] **VRAM:** peak GPU memory (e.g. `torch.cuda.max_memory_allocated()` or `nvidia-smi`)
- [ ] **RTF** for audio models: real-time factor (processing time / audio duration)
- [ ] **Memory bandwidth** if relevant: HBM usage, KV cache size

**Example — PR #3882:**

| Concurrency | Baseline RPS | This PR RPS | Throughput change | Baseline avg latency | This PR avg latency |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.83 | 1.89 | +3% | 0.55s | 0.53s |
| 4 | 2.35 | 4.03 | +72% | 1.64s | 0.95s |

Reports both RPS and latency at each concurrency level. **Still missing:** VRAM at each level.

**Example — PR #3878:**

| concurrency | RTF(main) | RTF(PR 3878) | delta |
|---:|---:|---:|---:|
| 1 | 0.14 | 0.13 | -7.14% |
| 32 | 0.67 | 0.50 | -25.37% |

Shows RTF improvement grows with concurrency — a strong signal the optimization is sound. **Still missing:** peak VRAM, latency.

### 8.4 Graceful Degradation

- [ ] Performance on minimum-spec hardware is measured (not just A100/H100)
- [ ] Memory behavior at `max_model_len` is tested (does it OOM or degrade cleanly?)
- [ ] Streaming vs non-streaming paths both measured (if both exist)

---

## Dimension 9: Benchmark Settings

Benchmarks without settings are irreproducible — the reviewer can't verify the claim.

### 9.1 Model Configuration

- [ ] Tensor parallel size, pipeline parallel size stated
- [ ] `max_model_len` / `max_num_batched_tokens` stated
- [ ] `enforce_eager` vs CUDA graph mode stated
- [ ] Quantization (none, FP8, AWQ, GPTQ) stated
- [ ] `gpu_memory_utilization` stated
- [ ] `max_num_seqs` stated (especially if changed from default)

**Example — PR #3882:** Explicitly documents `max_num_seqs` changed from 4 to 8 in the deploy YAML. Good: the reviewer knows both the old and new values and why.

### 9.2 Runtime Configuration

- [ ] Batch size and concurrency level stated
- [ ] Input specification: prompt length, audio duration, image resolution, generation steps
- [ ] Output specification: max_tokens, target duration, target resolution
- [ ] Streaming vs non-streaming stated
- [ ] `--async-chunk` vs sequential mode stated (if applicable)

### 9.3 Environment

- [ ] `torch.__version__`, CUDA version, vllm version, vllm-omni version stated
- [ ] FlashAttention version if relevant (especially for custom kernels)
- [ ] Any `PYTORCH_CUDA_ALLOC_CONF` or similar env vars stated

**What #3878 and #3882 both miss:** Neither reports software versions. The reviewer can't know if the improvement is real or due to a different torch/CUDA combination.

### 9.4 Reproducibility

- [ ] Benchmark script is checked in (under `examples/` or `tests/`)
- [ ] Script is self-contained: sets seeds, logs versions, prints results
- [ ] README includes the exact command line used, not pseudocode
- [ ] Results include the test run summary (e.g. pytest output, not just cherry-picked numbers)

**Example — PR #3878:** Includes exact `pytest` command plus run summary: `36 passed, 3 skipped, 17 warnings in 2897.66s`. Reviewer can verify the full test pass.

**Example — PR #3882:** Includes `python3 -m pytest ... -q` output: `7 passed, 17 warnings in 0.86s`. Clean and verifiable.
