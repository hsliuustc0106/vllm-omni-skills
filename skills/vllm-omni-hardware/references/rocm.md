# AMD ROCm Backend

## Requirements

- AMD Instinct GPU (MI300X, MI250X, MI210)
- ROCm 6.0+ (recommended 7.0 for latest features)
- Linux kernel 5.15+

## Installation

```bash
uv venv --python $PYTHON_VERSION --seed
source .venv/bin/activate

uv pip install vllm==$VLLM_VERSION --extra-index-url https://wheels.vllm.ai/rocm/$VLLM_VERSION/rocm700

git clone https://github.com/vllm-project/vllm-omni.git
cd vllm-omni
uv pip install -e .
```

## Configuration

### Device Selection

```bash
HIP_VISIBLE_DEVICES=0,1 vllm serve <model> --omni --port 8091
```

### Kernel Caching

First launch compiles HIP kernels for your GPU architecture. Cache them for faster subsequent starts:

```bash
export MIOPEN_USER_DB_PATH=/persistent/path/miopen_cache
export MIOPEN_CUSTOM_CACHE_DIR=/persistent/path/miopen_cache
```

### Tensor Parallelism

```bash
vllm serve <model> --omni --tensor-parallel-size 4
```

ROCm uses RCCL for GPU-to-GPU communication (equivalent to NCCL on CUDA).

## Monitoring

```bash
rocm-smi --showuse --showmeminfo vram
rocm-smi --showtemp --showpower
```

## Supported GPUs

| GPU | VRAM | ROCm Version | Notes |
|-----|------|-------------|-------|
| MI300X | 192 GB | 6.0+ | Best ROCm performance |
| MI250X | 128 GB | 5.7+ | Production capable |
| MI210 | 64 GB | 5.7+ | Supported |

## Known Limitations

- Some custom CUDA kernels may not have ROCm equivalents; fallback to generic implementations
- Kernel compilation on first run can take several minutes
- Flash Attention support requires ROCm 6.0+ with composable kernel backend
