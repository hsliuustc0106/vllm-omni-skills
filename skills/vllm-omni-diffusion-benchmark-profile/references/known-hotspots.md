# Known vLLM-Omni Diffusion Hotspots and Tuning Patterns

This file captures recurring optimization patterns found while tuning diffusion models in vLLM-Omni, especially Wan2.2 on NPU.

## 1. Sequence Parallel Strategy

### Symptom

- Very high `alltoallAicpuKernel`
- Very high `HcclAlltoAll`
- `Communication(Not Overlapped)` dominates stage time

### Common Root Cause

- SP applied too broadly
- cross-attention incorrectly using the same SP path as self-attention
- shard/gather boundaries too fine-grained

### Typical Fixes

- Skip sequence parallel on cross-attention when K/V are encoder-side replicated states
- Move sequence shard/gather to the model level instead of per-attention hook boundaries
- Reduce the number of collectives before trying to micro-optimize a single collective wrapper

## 2. Layerwise Offload

### Symptom

- Wall clock increases when offload is enabled
- `ViewCopy` or memory churn is high
- communication/copy wait appears between adjacent layers

### Common Root Cause

- prefetch event waited in the wrong place
- copy not overlapped with current-layer compute
- frequent placeholder/materialization churn

### Typical Fixes

- Wait for prefetched weights in the current layer `pre_forward`, not the previous layer `post_forward`
- Reuse empty placeholders
- Avoid redundant prefetch if the next layer is already materialized

## 3. VAE Bottlenecks

### Symptom

- `Conv3DV2` dominates
- `PadV3` and `TransData` are also high
- operator call stacks point to `autoencoder_kl_wan.py` or equivalent VAE code

### Common Root Cause

- VAE encode/decode not using parallel path
- full-resolution serial 3D conv path

### Typical Fixes

- Enable VAE patch/tile parallelism
- Ensure both decode and encode paths are parallelized
- Re-benchmark after VAE changes because bottleneck often shifts back to DiT

## 4. RoPE / Rotary Embedding

### Symptom

- `aclnnInplaceCopy` or `ViewCopy` is high
- call stacks point to RoPE application code

### Common Root Cause

- strided slice writeback such as:
  - `out[..., 0::2] = ...`
  - `out[..., 1::2] = ...`

### Typical Fixes

- Replace slice writeback with regularized tensor construction such as `stack + flatten`
- Consider fused/custom backend path only after verifying the unfused path is still a hotspot

## 5. Data Transform / Layout Overhead

### Symptom

- `TransData`, `Transpose`, `ViewCopy`, `ConcatD` are high

### Common Root Cause

- too many `permute/transpose/reshape/contiguous` chains
- layout mismatch around communication wrappers or attention backends
- dtype conversions in pipeline boundaries

### Typical Fixes

- inspect `operator_details.csv` call stacks first
- simplify layout changes around `comm.py`
- avoid full-tensor work before local shard

## 6. How To Prioritize

When several hotspots exist, this order usually works well:

1. Remove unnecessary communication
2. Fix overlap and synchronization placement
3. Parallelize VAE if it is still serial
4. Eliminate hot-path copy/layout pathologies
5. Only then micro-optimize individual wrappers or kernels

## 7. Principle

The highest-yield diffusion perf fixes are often not “make one kernel 5% faster”.

They are usually:
- removing work that should not happen
- moving work to a better boundary
- fixing a tiny hot-path function that runs thousands of times

