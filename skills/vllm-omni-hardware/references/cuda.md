# NVIDIA CUDA Backend

## Requirements

- NVIDIA GPU with compute capability >= 7.0 (V100+)
- NVIDIA Driver >= 525.60
- CUDA Toolkit 12.x (bundled with PyTorch)

## Installation

```bash
uv pip install vllm==$VLLM_VERSION --torch-backend=auto
git clone https://github.com/vllm-project/vllm-omni.git && cd vllm-omni
uv pip install -e .
```

## Optimization Options

### Flash Attention

Enabled by default on Ampere+ GPUs (A100, H100, L40, RTX 30/40 series). No configuration needed.

### Memory Management

```bash
# Set GPU memory fraction
vllm serve <model> --omni --gpu-memory-utilization 0.9

# Enable CPU offloading for large models
vllm serve <model> --omni --cpu-offload-gb 10
```

### Multi-GPU with NVLink

NVLink provides high-bandwidth GPU-to-GPU communication. Tensor parallelism automatically uses NVLink when available:

```bash
# Check NVLink topology
nvidia-smi topo -m

# Use all NVLink-connected GPUs
vllm serve <model> --omni --tensor-parallel-size 4
```

### CUDA Graphs

vLLM uses CUDA graphs to reduce kernel launch overhead for AR models. Enabled by default. For diffusion models, CUDA graphs apply to the denoising loop.

## Monitoring

```bash
# Real-time GPU utilization
nvidia-smi dmon -s pucvmet -d 1

# Memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

## Supported GPUs

| GPU | VRAM | Compute Capability | Notes |
|-----|------|--------------------|-------|
| H100 SXM | 80 GB | 9.0 | Best performance |
| A100 SXM | 80 GB | 8.0 | Production standard |
| A100 PCIe | 40/80 GB | 8.0 | Good performance |
| L40S | 48 GB | 8.9 | Ada Lovelace |
| RTX 4090 | 24 GB | 8.9 | Consumer, good for small models |
| RTX 3090 | 24 GB | 8.6 | Consumer, Ampere |
| V100 | 16/32 GB | 7.0 | Legacy, limited model support |
