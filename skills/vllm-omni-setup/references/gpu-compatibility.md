# GPU Compatibility Matrix

## NVIDIA GPU (CUDA)

| GPU Generation | Compute Capability | CUDA Version | Status |
|----------------|--------------------|--------------|--------|
| A100 / A800 | 8.0 | 12.x | Fully supported |
| H100 / H800 | 9.0 | 12.x | Fully supported |
| L40 / L40S | 8.9 | 12.x | Fully supported |
| RTX 4090 | 8.9 | 12.x | Supported (consumer) |
| RTX 3090 | 8.6 | 11.8+ | Supported (consumer) |
| V100 | 7.0 | 11.8+ | Limited (older arch) |

**Driver requirements**: NVIDIA driver >= 525.60 for CUDA 12.x.

## AMD GPU (ROCm)

| GPU | ROCm Version | Status |
|-----|-------------|--------|
| MI300X | 6.0+ | Fully supported |
| MI250X | 5.7+ | Supported |
| MI210 | 5.7+ | Supported |

**Install with**:
```bash
uv pip install vllm==$VLLM_VERSION --extra-index-url https://wheels.vllm.ai/rocm/$VLLM_VERSION/rocm700
```

## Huawei NPU (Ascend)

| Accelerator | CANN Version | Status |
|-------------|-------------|--------|
| Ascend 910B | 8.0+ | Supported |
| Ascend 910A | 7.0+ | Limited |

Requires Ascend CANN toolkit and mindspore backend. See upstream vllm-omni NPU docs for installation.

## Intel XPU

| GPU | oneAPI Version | Status |
|-----|---------------|--------|
| Data Center GPU Max (Ponte Vecchio) | 2024.x | Supported |
| Arc A-series | 2024.x | Experimental |

Requires Intel oneAPI toolkit and IPEX backend.

## Memory Requirements by Model

| Model | Parameters | Min GPU Memory |
|-------|-----------|----------------|
| Z-Image-Turbo | ~2B | 8 GB |
| Qwen-Image | ~8B | 24 GB |
| Qwen2.5-Omni-7B | 7B | 24 GB |
| Qwen3-Omni-30B-A3B | 30B (3B active) | 48 GB |
| BAGEL-7B-MoT | 7B | 24 GB |
| Wan2.2-T2V-A14B | 14B | 48 GB |
| FLUX.1-dev | ~12B | 40 GB |
| Stable-Diffusion-3.5-medium | ~2.5B | 12 GB |
