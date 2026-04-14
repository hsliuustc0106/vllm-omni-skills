---
name: vllm-omni-hardware
description: Configure vLLM-Omni for different hardware backends including NVIDIA CUDA, AMD ROCm, Huawei NPU, and Intel XPU. Use when selecting a hardware backend, troubleshooting GPU issues, configuring device placement, or optimizing for specific accelerators.
---

# vLLM-Omni Hardware Configuration

## Overview

vLLM-Omni supports four hardware backends: NVIDIA CUDA (default), AMD ROCm, Huawei NPU (Ascend), and Intel XPU. Each backend has specific installation steps and configuration options.

## Supported Backends

| Backend | Accelerators | Install Method | Maturity |
|---------|-------------|----------------|----------|
| CUDA | NVIDIA A100/H100/L40/RTX | `uv pip install vllm==$VLLM_VERSION` | Production |
| ROCm | AMD MI300X/MI250X | `uv pip install vllm==$VLLM_VERSION --extra-index-url ...` | Production |
| NPU | Huawei Ascend 910B | Source build with CANN | Supported |
| XPU | Intel Data Center GPU Max | Source build with oneAPI | Experimental |

## Backend Selection Workflow

### Step 1: Identify Hardware

```bash
# NVIDIA GPU
nvidia-smi

# AMD GPU
rocm-smi

# Huawei NPU
npu-smi info

# Intel XPU
xpu-smi discovery
```

### Step 2: Install for Backend

**CUDA (NVIDIA):**
```bash
uv pip install vllm==$VLLM_VERSION --torch-backend=auto
```

**ROCm (AMD):**
```bash
uv pip install vllm==$VLLM_VERSION --extra-index-url https://wheels.vllm.ai/rocm/$VLLM_VERSION/rocm700
```

**NPU (Huawei):**
```bash
# Requires CANN toolkit pre-installed
git clone https://github.com/vllm-project/vllm-omni.git
cd vllm-omni
pip install -e ".[npu]"
```

**XPU (Intel):**
```bash
# Requires oneAPI toolkit pre-installed
git clone https://github.com/vllm-project/vllm-omni.git
cd vllm-omni
pip install -e ".[xpu]"
```

### Step 3: Verify Backend

```python
import torch

# CUDA
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")

# ROCm (same API as CUDA via HIP)
print(f"ROCm/HIP available: {torch.cuda.is_available()}")

# XPU
print(f"XPU available: {torch.xpu.is_available()}")
```

## Device Selection

Control which devices vLLM-Omni uses:

```bash
# CUDA: Select specific GPUs
CUDA_VISIBLE_DEVICES=0,1 vllm serve <model> --omni

# ROCm: Select specific GPUs
HIP_VISIBLE_DEVICES=0,1 vllm serve <model> --omni

# NPU: Select specific devices
ASCEND_RT_VISIBLE_DEVICES=0,1 vllm serve <model> --omni
```

## Model Support by Backend

Not all models are supported on every backend. Check the support matrix:

| Model | CUDA | ROCm | NPU | XPU |
|-------|------|------|-----|-----|
| Qwen3-Omni | Yes | Yes | Yes | No |
| Qwen2.5-Omni | Yes | Yes | Yes | No |
| Qwen-Image | Yes | Yes | Yes | No |
| Z-Image | Yes | Yes | Yes | No |
| BAGEL | Yes | Yes | No | No |
| Wan2.2 | Yes | Yes | Yes | No |
| FLUX | Yes | Yes | Yes | No |
| Qwen3-TTS | Yes | Yes | Yes | No |
| Stable-Diffusion-3 | Yes | Yes | No | No |
| Stable-Audio | Yes | No | No | No |

## Troubleshooting

**CUDA out of memory**: Reduce `--gpu-memory-utilization` or use tensor parallelism across multiple GPUs.

**ROCm kernel compilation slow**: First launch compiles kernels for your GPU. Subsequent launches reuse cached kernels. Set `MIOPEN_USER_DB_PATH` for persistent kernel cache.

**NPU operator not supported**: Some operations fall back to CPU on NPU. Check logs for fallback warnings and update CANN to the latest version.

**NPU LaserAttention unsupported error**: On Ascend NPU with mindiesd, selecting `FLASH_ATTN` as the diffusion attention backend (`--diffusion-attn-backend FLASH_ATTN`) auto-imports `mindiesd` to configure `ASCEND_CUSTOM_OPP_PATH`. The internal environment variable `MINDIE_SD_FA_TYPE` is set to `ascend_laser_attention` automatically. Fixed in #2674.

## References

- For CUDA-specific optimization, see [references/cuda.md](references/cuda.md)
- For ROCm setup details, see [references/rocm.md](references/rocm.md)
- For NPU configuration, see [references/npu.md](references/npu.md)
- For XPU setup, see [references/xpu.md](references/xpu.md)
