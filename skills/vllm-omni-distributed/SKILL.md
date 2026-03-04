---
name: vllm-omni-distributed
description: Configure distributed inference with vLLM-Omni using tensor parallelism, pipeline parallelism, OmniConnector disaggregation, and Ray. Use when deploying models across multiple GPUs or nodes, setting up disaggregated execution, or scaling inference horizontally.
---

# vLLM-Omni Distributed Inference

## Overview

vLLM-Omni supports distributed execution through multiple strategies: tensor parallelism (TP), pipeline parallelism (PP), expert parallelism (EP), and fully disaggregated execution via OmniConnector. These can be combined for optimal throughput and latency.

## Parallelism Strategies

| Strategy | Splits | Best For | Trade-off |
|----------|--------|----------|-----------|
| Tensor Parallel (TP) | Model layers across GPUs | Latency reduction | Requires fast GPU interconnect |
| Pipeline Parallel (PP) | Model stages across GPU groups | Throughput increase | Adds latency per stage |
| Expert Parallel (EP) | MoE experts across GPUs | MoE models | Requires MoE architecture |
| Disaggregation | Entire pipeline stages | Independent scaling | Network overhead between stages |

## Tensor Parallelism

Split model weights across GPUs on a single node:

```bash
# 2-GPU tensor parallelism
vllm serve Qwen/Qwen2.5-Omni-7B --omni --tensor-parallel-size 2

# 4-GPU tensor parallelism
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni --tensor-parallel-size 4
```

**Requirements:**
- GPUs must be on the same node
- NVLink/NVSwitch preferred for NVIDIA GPUs
- TP size must evenly divide attention heads
- Total GPUs = TP size x PP size

## Pipeline Parallelism

Split model stages across sequential GPU groups:

```bash
vllm serve <model> --omni \
  --tensor-parallel-size 2 \
  --pipeline-parallel-size 2
```

This uses 4 GPUs total: 2 groups of 2 GPUs each. Each group handles a portion of the model layers.

## Disaggregated Execution (OmniConnector)

vLLM-Omni's OmniConnector enables fully disaggregated serving, where different pipeline stages (Encode, Prefill, Decode, Generate) run on separate GPU pools:

```
Request → [E] Encode → [P] Prefill → [D] Decode → [G] Generate → Response
```

Each stage can be scaled independently:

- **Encode (E)**: Processes multi-modal inputs (images, audio, video)
- **Prefill (P)**: Runs initial forward pass to populate KV cache
- **Decode (D)**: Autoregressive token generation
- **Generate (G)**: Diffusion or audio generation

### Benefits

- Scale each stage based on its bottleneck independently
- Mix GPU types (e.g., cheaper GPUs for encoding, premium GPUs for generation)
- Better GPU utilization by matching capacity to demand per stage

## Multi-Node with Ray

For models that exceed single-node GPU capacity:

### Step 1: Start Ray Cluster

```bash
# Head node
ray start --head --port=6379

# Worker nodes (run on each additional machine)
ray start --address=<head-node-ip>:6379
```

### Step 2: Launch Server

```bash
vllm serve <model> --omni \
  --tensor-parallel-size 8 \
  --port 8091
```

Ray automatically distributes workers across the cluster.

### Step 3: Verify Cluster

```python
import ray
ray.init(address="auto")
print(ray.cluster_resources())
```

## Sequence Parallelism for Diffusion

For DiT models, sequence parallelism splits the denoising sequence across GPUs:

```bash
vllm serve Wan-AI/Wan2.2-T2V-A14B-Diffusers --omni \
  --tensor-parallel-size 4
```

This accelerates video/image generation by parallelizing the diffusion computation.

## Configuration Examples

### Small model, single GPU
```bash
vllm serve Tongyi-MAI/Z-Image-Turbo --omni
```

### Medium model, dual GPU
```bash
vllm serve Qwen/Qwen2.5-Omni-7B --omni --tensor-parallel-size 2
```

### Large MoE model, quad GPU
```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni --tensor-parallel-size 4
```

### Very large model, multi-node
```bash
ray start --head
vllm serve <model> --omni --tensor-parallel-size 8
```

## Troubleshooting

**NCCL timeout**: GPU-to-GPU communication is timing out. Check NVLink/InfiniBand connectivity. Increase timeout with `NCCL_TIMEOUT=1800`.

**Uneven GPU utilization**: Common with pipeline parallelism. Adjust stage placement to balance load.

**Ray worker disconnected**: Check network connectivity between nodes and ensure Ray dashboard shows all workers.

## References

- For disaggregation architecture details, see [references/disaggregation.md](references/disaggregation.md)
- For Ray execution setup, see [references/ray-execution.md](references/ray-execution.md)


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix load_weights error when loading HunyuanImage3.0](https://github.com/vllm-project/vllm-omni/pull/1598)

### Changes
- Bug fix: [BugFix] Fix load_weights error when loading HunyuanImage3.0

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix unexpected crash when init OmniDiffusion](https://github.com/vllm-project/vllm-omni/pull/1562)

### Changes
- Bug fix: [BugFix] Fix unexpected crash when init OmniDiffusion

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [Fix no embed text spk tokens](https://github.com/vllm-project/vllm-omni/pull/1540)

### Changes
- Bug fix: Fix no embed text spk tokens

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Debug] Enable curl retry aligned with openai](https://github.com/vllm-project/vllm-omni/pull/1539)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Restore talker's config](https://github.com/vllm-project/vllm-omni/pull/1524)

### Changes
- Bug fix: [BugFix] Restore talker's config

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] fix offline text_to_image error from #1009](https://github.com/vllm-project/vllm-omni/pull/1515)

### Changes
- Bug fix: [Bugfix] fix offline text_to_image error from #1009

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Doc] Update installation instructions for vllm 0.16.0](https://github.com/vllm-project/vllm-omni/pull/1505)


*Updated: 2026-03-04*
