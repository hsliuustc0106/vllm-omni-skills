---
name: vllm-omni-distributed
description: "Scale vLLM-Omni across multiple GPUs and nodes using tensor parallelism, pipeline parallelism, OmniConnector disaggregation, connector backends, and Ray. Use when setting up multi-GPU inference, distributing model execution across machines, deploying disaggregated execution, developing OmniConnector backends, or scaling inference horizontally."
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

## OmniConnector Development

Use this skill for connector implementation work as well as connector usage.

- Refer to `SharedMemoryConnector`, `MooncakeStoreConnector`, `YuanrongConnector`, and `MooncakeTransferEngineConnector` as implementation references before adding a new backend
- Keep connector edge config role-neutral in YAML; let runtime inject sender or receiver details
- Validate connector changes from the smallest contract outward: basic `put/get`, config loading, stage flow, then KV cache flow
- Support both metadata-driven and key-only retrieval paths when designing connector behavior

### OmniConnector Validation Workflow

```bash
# 1. Verify basic put/get contract
python -c "
from vllm_omni.omni_connector import create_connector
conn = create_connector('shared_memory', config={})
conn.put('test_key', b'test_data')
assert conn.get('test_key') == b'test_data', 'Basic put/get failed'
print('OK: put/get contract passes')
"

# 2. Verify config loading from stage YAML
python -c "
import yaml
with open('stage_config.yaml') as f:
    cfg = yaml.safe_load(f)
assert 'connector' in cfg, 'Missing connector config'
print(f'OK: connector type = {cfg[\"connector\"][\"type\"]}')
"

# 3. Test stage flow end-to-end (start stages, send one request, verify output)
```

## Multi-Node with Ray

For models that exceed single-node GPU capacity:

### Step 1: Start Ray Cluster

```bash
# Head node
ray start --head --port=6379

# Worker nodes (run on each additional machine)
ray start --address=<head-node-ip>:6379
```

### Step 2: Verify Cluster Before Launching

```python
import ray
ray.init(address="auto")
resources = ray.cluster_resources()
num_gpus = resources.get("GPU", 0)
assert num_gpus >= 8, f"Need 8 GPUs, found {num_gpus}"
print(f"OK: cluster has {num_gpus} GPUs across {resources.get('node:__internal_head__', 0) + 1} nodes")
```

### Step 3: Launch Server

```bash
vllm serve <model> --omni \
  --tensor-parallel-size 8 \
  --port 8091
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
- For OmniConnector backend contract, config wiring, and validation, see [references/connector-development.md](references/connector-development.md)
- For Ray execution setup, see [references/ray-execution.md](references/ray-execution.md)
