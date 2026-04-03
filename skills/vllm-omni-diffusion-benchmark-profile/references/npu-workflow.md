# NPU Profiling Workflow for vLLM-Omni Diffusion

## Entry Point

Standalone diffusion examples enable profiling with:

```bash
--profiler-dir <dir>
```

This becomes:

```python
{
  "profiler": "torch",
  "torch_profiler_dir": <dir>,
}
```

The NPU implementation is in:
- `vllm_omni/platforms/npu/profiler.py`

It uses:
- `torch_npu.profiler.profile(...)`
- `torch_npu.profiler.tensorboard_trace_handler(...)`

Unlike CUDA `torch.profiler`, NPU does not rely on `key_averages()` for the main workflow. It should be parsed offline with:

```python
from torch_npu.profiler.profiler import analyse
analyse("<trace_dir>")
```

## Files To Read First

### `step_trace_time.csv`

Use this first. It gives the highest-signal stage breakdown:

- `Computing`
- `Communication(Not Overlapped)`
- `Communication`
- `Stage`
- `Preparing`
- `Free`

Interpretation:
- High `Communication(Not Overlapped)` usually means collective wait is dominating.
- High `Free` often indicates heavy memory churn, deallocation overhead, or profiler bucketing artifacts after layout-heavy code.

### `op_statistic.csv`

Use this second. It gives top operator totals by type.

Important operators to watch:
- `FlashAttentionScore`
- `MatMulV3`
- `Conv3DV2`
- `ViewCopy`
- `TransData`
- `Transpose`
- `PadV3`
- `alltoallAicpuKernel`
- `allgatherAicpuKernel`
- `broadcastAicpuKernel`

Do not stop at this table. It shows **what** is expensive, not **why**.

### `communication.json`

Use this to separate:
- real transit time
- wait time
- synchronization time

If `Wait Time Ratio` is near `1.0`, the problem is usually not raw bandwidth but rank skew / stream sync / collective placement.

### `operator_details.csv`

Use this for call-stack attribution.

This is often the file that identifies the real source of:
- `ViewCopy`
- `InplaceCopy`
- `Convolution`
- collective wrappers

The `Name` column typically contains backend op names such as:
- `HcclAlltoAll`
- `HcclAllGather`
- `aclnnInplaceCopy`
- `aclnnConvolution`
- `aclnnFlashAttentionScore`

The `Call Stack` column is the most useful field when mapping runtime cost back to code.

## Recommended Read Order

1. `step_trace_time.csv`
2. `op_statistic.csv`
3. `communication.json`
4. `operator_details.csv`
5. `trace_view.json` only when you need timeline-level sequencing

## Comparison Method

When comparing two runs, use the same shape, steps, and parallel config.

For each run, capture:

- `Stage`
- `Computing`
- `Communication(Not Overlapped)`
- top operators from `op_statistic.csv`
- `Total Op Info` from `communication.json`
- top call stacks from `operator_details.csv`

## Common Interpretation Patterns

### `alltoallAicpuKernel` drops a lot, but total communication barely drops

Interpretation:
- wrapper-level all-to-all overhead decreased
- underlying HCCL wait is still dominant

Action:
- inspect `communication.json`
- look for `HcclAlltoAll` wait time
- review SP strategy and collective placement

### `Conv3DV2` is high

Interpretation:
- often VAE, not DiT patch embedding

Action:
- inspect `operator_details.csv`
- look for call stacks under `autoencoder_kl_wan.py` or equivalent VAE code

### `ViewCopy` / `InplaceCopy` is high

Interpretation:
- usually layout transform, strided writes, or tensor rebinding overhead

Action:
- inspect call stacks
- look for:
  - RoPE writeback
  - offload placeholder/materialization
  - `permute/transpose/reshape/contiguous` chains

### `TransData` is high

Interpretation:
- dtype/layout conversion overhead

Action:
- inspect call stacks around:
  - communication wrappers
  - attention backends
  - VAE
  - pipeline dtype conversions

