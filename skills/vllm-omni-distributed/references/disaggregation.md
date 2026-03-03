# OmniConnector Disaggregation

## Architecture

OmniConnector is vLLM-Omni's disaggregation framework that decouples the inference pipeline into independent stages connected via high-performance communication channels.

## Pipeline Stages

```
┌────────┐    ┌─────────┐    ┌────────┐    ┌──────────┐
│ Encode │───>│ Prefill  │───>│ Decode │───>│ Generate │
│  (E)   │    │   (P)    │    │  (D)   │    │   (G)    │
└────────┘    └─────────┘    └────────┘    └──────────┘
  GPU Pool 1   GPU Pool 2    GPU Pool 3    GPU Pool 4
```

### Encode (E)
- Processes multi-modal inputs
- Runs vision encoders, audio encoders
- Compute-bound for image/video inputs
- Can use cheaper GPUs

### Prefill (P)
- Runs the initial forward pass through the language model
- Populates the KV cache
- Memory and compute intensive
- Benefits from high-memory GPUs

### Decode (D)
- Autoregressive token generation
- Memory-bandwidth bound
- Benefits from high-bandwidth GPUs

### Generate (G)
- Diffusion generation (images, video) or audio synthesis
- Compute intensive and long-running
- Benefits from independent scaling

## Benefits of Disaggregation

1. **Independent scaling**: Scale encode pool for image-heavy workloads, generate pool for diffusion-heavy workloads
2. **Hardware heterogeneity**: Use different GPU types per stage
3. **Resource efficiency**: No idle GPUs waiting for other stages
4. **Fault isolation**: A failure in one stage doesn't crash the entire pipeline

## Inter-Stage Communication

OmniConnector uses:
- Shared memory for co-located stages (same node)
- RDMA/InfiniBand for cross-node communication
- Efficient tensor serialization for minimal overhead

## When to Use Disaggregation

| Scenario | Recommendation |
|----------|---------------|
| Single model, single GPU | No disaggregation needed |
| Multi-GPU, latency-sensitive | Tensor parallelism |
| High throughput, mixed workloads | Disaggregation |
| Multi-model serving | Disaggregation per model |
| Production at scale | Full disaggregation |
