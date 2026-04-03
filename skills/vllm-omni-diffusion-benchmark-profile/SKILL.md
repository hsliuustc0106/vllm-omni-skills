---
name: vllm-omni-diffusion-benchmark-profile
description: "Benchmark, profile, and tune vLLM-Omni diffusion models, especially Wan/Qwen/Helios style pipelines on GPU or NPU. Use this when measuring denoise latency, collecting torch or torch_npu profiler traces, reading ASCEND_PROFILER_OUTPUT artifacts, comparing before/after performance, or diagnosing bottlenecks such as SP communication, VAE convs, data transforms, offload overlap, and RoPE overhead."
---

# vLLM-Omni Diffusion Benchmark and Profile

Use this skill when the task is to benchmark, profile, compare, or optimize a vLLM-Omni diffusion model.

Primary target:
- **Denoise latency / DiT hot path**

Secondary targets:
- End-to-end latency
- VAE encode/decode cost
- Communication overhead
- Data transform / copy overhead
- Offload overlap quality

Correctness rule:
- Do not accept a perf improvement if output quality or generation correctness regresses.

## When To Use

Use this skill for:
- `image_to_video.py`, `text_to_video.py`, `text_to_image.py`, image edit, or other standalone diffusion examples
- Diffusion serving runs started with `vllm serve ... --profiler-config ...`
- GPU `torch.profiler` analysis
- NPU `torch_npu.profiler` / `ASCEND_PROFILER_OUTPUT` analysis
- Before/after perf comparison for PRs

Do not use this skill for:
- Autoregressive-only LLM profiling
- Audio/tokenizer-only perf work unless the model actually uses the diffusion stack

## Core Workflow

1. Reproduce with a fixed command, fixed seed, fixed resolution, fixed frame count, and fixed steps.
2. Record an end-to-end baseline first.
3. For profiling, reduce `num_inference_steps` to `2` unless the task specifically needs long-run behavior.
4. Keep the same shape and parallel config across before/after runs.
5. Profile one thing at a time:
   - end-to-end wall clock
   - pipeline stage timing
   - operator/top kernel view
   - communication view
   - call-stack attribution
6. After each change, re-run:
   - correctness check
   - same benchmark command
   - same profiler setup

## Key Metric Hierarchy

1. **Denoise / DiT latency**: main optimization target
2. **End-to-end latency**: sanity check and user-facing metric
3. **Communication wait**: critical for SP/Ulysses on multi-device runs
4. **Data transform/copy cost**: often hidden inside `ViewCopy`, `TransData`, `Transpose`, `InplaceCopy`
5. **VAE encode/decode cost**: especially important for video models

## Benchmarking Rules

- Always compare with the same:
  - model
  - prompt / image input
  - seed
  - height / width
  - num_frames
  - num_inference_steps
  - guidance scale
  - parallel config
- For profiling, prefer `2` steps.
- For end-to-end reporting, use the real target steps.
- If using NPU and the model is close to memory limits, note whether:
  - `--enable-layerwise-offload`
  - `--vae-patch-parallel-size`
  - `--vae-use-tiling`
  are enabled, because these materially change the bottleneck mix.

## vLLM-Omni Profiling Entry Points

### Standalone diffusion examples

Use `--profiler-dir` to enable torch/torch_npu profiler output.

Common examples:
- `examples/offline_inference/image_to_video/image_to_video.py`
- `examples/offline_inference/text_to_video/text_to_video.py`
- `examples/offline_inference/text_to_image/text_to_image.py`

Typical NPU Wan2.2 I2V profile command:

```bash
cd /root/vllm-workspace/vllm-omni/examples/offline_inference/image_to_video

python image_to_video.py \
  --model Wan-AI/Wan2.2-I2V-A14B-Diffusers \
  --image cherry_blossom.jpg \
  --prompt "Cherry blossoms swaying gently in the breeze, petals falling, smooth motion" \
  --negative-prompt "<optional quality filter>" \
  --height 512 \
  --width 768 \
  --num-frames 49 \
  --guidance-scale 4.0 \
  --num-inference-steps 2 \
  --flow-shift 12.0 \
  --fps 16 \
  --output i2v_output.mp4 \
  --enable-layerwise-offload \
  --ulysses-degree 8 \
  --vae-patch-parallel-size 8 \
  --vae-use-tiling \
  --profiler-dir ./wan22_step2_profile
```

### Serving mode

Use:

```bash
vllm serve Wan-AI/Wan2.2-I2V-A14B-Diffusers \
  --omni \
  --port 8091 \
  --profiler-config '{"profiler": "torch", "torch_profiler_dir": "./vllm_profile"}'
```

Then control profiling with `/start_profile` and `/stop_profile`.

## Analysis Workflow

### GPU

- Read `.json.gz` trace in Perfetto or `chrome://tracing`
- If available, use `key_averages()` tables or exported tables
- Attribute time to:
  - attention kernels
  - GEMMs
  - norm / activation
  - copies / layout transforms

### NPU

NPU profiling uses `torch_npu.profiler.tensorboard_trace_handler(...)` and must be parsed offline.

Core files after `analyse(<trace_dir>)`:
- `step_trace_time.csv`
- `op_statistic.csv`
- `operator_details.csv`
- `communication.json`
- `kernel_details.csv`
- `trace_view.json`

Use:

```python
from torch_npu.profiler.profiler import analyse
analyse("./wan22_step2_profile/diffusion_worker_0")
```

Or adapt:
- `/root/vllm-workspace/analyze_profiling.py`
- `examples/offline_inference/image_to_video/analyse.py`

For NPU artifact interpretation, read:
- `references/npu-workflow.md`

For common bottlenecks and likely fixes, read:
- `references/known-hotspots.md`

## Fast Diagnostic Questions

When reading a profile, answer these in order:

1. Is the bottleneck mainly **DiT**, **VAE**, or **communication**?
2. Is the time in **real compute**, or mostly **wait/synchronization**?
3. Are the expensive ops on the hot path repeated per step / per block / per CFG branch?
4. Is the model paying for work that should be skipped?
   - unnecessary SP on cross-attn
   - full-shape work before local shard
   - serial VAE encode/decode instead of parallel path
5. Is the backend spending time on memory movement instead of math?

## Before/After Comparison

Always summarize changes using the same fields:

- End-to-end latency
- Stage time
- Compute vs Communication(Not Overlapped)
- Top 10 operators by time
- Top communication ops
- Most important call-stack attribution changes

For NPU, prefer comparing:
- `step_trace_time.csv`
- `op_statistic.csv`
- `communication.json`
- `operator_details.csv`

## Diffusion Perf Tuning Principles

- Prefer removing unnecessary work over micro-optimizing already-necessary work.
- Sequence-parallel strategy matters more than optimizing a single `all_to_all_*` wrapper.
- For video models, VAE can be a first-order bottleneck, not just DiT.
- On NPU, strided writes and layout transforms can dominate hot paths.
- Offload only helps if copy is actually overlapped with compute.
- Small hot-path functions called thousands of times can outweigh large isolated kernels.

## Deliverables

A good perf investigation should usually produce:

1. The exact benchmark command used
2. The exact profiling command used
3. A short table of before/after metrics
4. A root-cause statement tied to code paths
5. A concrete next optimization candidate

## Final Check Before Claiming Improvement

- Same inputs and same settings as baseline
- No correctness regression
- Improvement reproduced at least once
- Improvement explained by profiler evidence, not just wall-clock noise

