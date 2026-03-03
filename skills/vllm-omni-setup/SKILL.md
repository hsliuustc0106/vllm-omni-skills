---
name: vllm-omni-setup
description: Install and configure vLLM-Omni for omni-modality model inference. Use when setting up vllm-omni, configuring the environment, installing dependencies, resolving GPU driver issues, or preparing a machine for model serving.
---

# vLLM-Omni Setup

## Overview

vLLM-Omni extends vLLM to support omni-modality model inference (text, image, video, audio) with both autoregressive and diffusion architectures. This skill covers installation from source and environment configuration.

## Prerequisites

- Linux OS (Ubuntu 20.04+ recommended)
- Python 3.12
- GPU with appropriate drivers (NVIDIA CUDA, AMD ROCm, Huawei NPU, or Intel XPU)
- `uv` package manager (recommended) or `pip`
- Git

## Installation Workflow

### Step 1: Create Python Environment

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
```

### Step 2: Install vLLM Base

Select the command matching your hardware:

**NVIDIA GPU (CUDA):**
```bash
uv pip install vllm==0.16.0 --torch-backend=auto
```

**AMD GPU (ROCm):**
```bash
uv pip install vllm==0.16.0 --extra-index-url https://wheels.vllm.ai/rocm/0.16.0/rocm700
```

### Step 3: Install vLLM-Omni

```bash
git clone https://github.com/vllm-project/vllm-omni.git
cd vllm-omni
uv pip install -e .
```

### Step 4: Verify Installation

```python
from vllm_omni.entrypoints.omni import Omni
print("vLLM-Omni installed successfully")
```

## Quick Smoke Test

Run a minimal text-to-image generation to verify the full stack:

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Tongyi-MAI/Z-Image-Turbo")
outputs = omni.generate("a red circle on white background")
outputs[0].request_output[0].images[0].save("test.png")
print("Setup verified - test.png generated")
```

## Docker Installation

For containerized deployment:

```bash
docker pull vllm/vllm-omni:v0.16.0
docker run --gpus all -p 8091:8091 vllm/vllm-omni:v0.16.0 \
  vllm serve Tongyi-MAI/Z-Image-Turbo --omni --port 8091
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `VLLM_OMNI_LOG_LEVEL` | Logging verbosity | `INFO` |
| `HF_HOME` | Hugging Face cache directory | `~/.cache/huggingface` |
| `CUDA_VISIBLE_DEVICES` | GPU device selection | all GPUs |
| `VLLM_WORKER_MULTIPROC_METHOD` | Worker process method | `spawn` |

## Troubleshooting

**CUDA version mismatch**: Ensure your CUDA toolkit version matches the PyTorch build. Check with `nvidia-smi` and `python -c "import torch; print(torch.version.cuda)"`.

**Out of memory on model load**: Use `gpu_memory_utilization` parameter to limit memory. Start with 0.8 and adjust:
```python
omni = Omni(model="...", gpu_memory_utilization=0.8)
```

**Model download failures**: Set `HF_HOME` to a directory with sufficient disk space. Large models (e.g., Qwen3-Omni-30B) require 60GB+ of disk.

## References

- For GPU compatibility matrix and driver requirements, see [references/gpu-compatibility.md](references/gpu-compatibility.md)
