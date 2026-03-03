# Ray Execution Engine

## Overview

vLLM-Omni uses Ray as its distributed execution backend for multi-node inference. Ray handles worker placement, communication, and fault tolerance.

## Setup

### Install Ray

```bash
pip install ray[default]
```

### Start Head Node

```bash
ray start --head --port=6379 --dashboard-host=0.0.0.0
```

Access the Ray dashboard at `http://<head-ip>:8265`.

### Add Worker Nodes

```bash
ray start --address=<head-ip>:6379
```

### Verify Cluster

```bash
ray status
```

Or programmatically:

```python
import ray
ray.init(address="auto")
print(f"Nodes: {len(ray.nodes())}")
print(f"GPUs: {ray.cluster_resources().get('GPU', 0)}")
```

## Launching vLLM-Omni on Ray

```bash
vllm serve <model> --omni \
  --tensor-parallel-size <total-gpus> \
  --port 8091
```

Ray automatically distributes tensor parallel workers across available nodes.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `RAY_ADDRESS` | Ray cluster address | `auto` |
| `VLLM_WORKER_MULTIPROC_METHOD` | Worker spawn method | `spawn` |
| `RAY_DEDUP_LOGS` | Deduplicate Ray logs | `1` |

## Resource Management

### GPU Allocation

Each vLLM worker claims 1 GPU. For tensor_parallel_size=4, Ray allocates 4 GPU resources:

```python
# Check available GPUs
import ray
ray.init(address="auto")
print(ray.available_resources().get("GPU"))
```

### Memory Management

Monitor Ray memory usage:

```bash
ray memory --stats-only
```

## Fault Tolerance

If a worker node goes down:
- Ray detects the failure via heartbeat timeout
- Affected actors are marked as dead
- vLLM-Omni currently requires a server restart for recovery

## Performance Tips

- Use InfiniBand for cross-node GPU-to-GPU communication
- Co-locate tensor parallel groups on the same node when possible
- Set `NCCL_SOCKET_IFNAME` to the correct network interface
- Monitor with `ray dashboard` for resource utilization
