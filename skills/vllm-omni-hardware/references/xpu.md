# Intel XPU Backend

## Requirements

- Intel Data Center GPU Max (Ponte Vecchio) or Arc A-series
- Intel oneAPI 2024.x+
- IPEX (Intel Extension for PyTorch)
- Linux

## Installation

```bash
# Source oneAPI environment
source /opt/intel/oneapi/setvars.sh

uv venv --python 3.12 --seed
source .venv/bin/activate

# Install PyTorch with XPU support
pip install torch intel-extension-for-pytorch

git clone https://github.com/vllm-project/vllm-omni.git
cd vllm-omni
pip install -e ".[xpu]"
```

## Configuration

### Device Selection

```bash
ZE_AFFINITY_MASK=0,1 vllm serve <model> --omni --port 8091
```

## Monitoring

```bash
xpu-smi discovery
xpu-smi stats -d 0
```

## Status

XPU backend is experimental. Model coverage is limited compared to CUDA and ROCm. Check the upstream vllm-omni repository for the latest XPU-supported models.

## Known Limitations

- Limited model support
- Performance may not match CUDA equivalents
- Some diffusion pipeline optimizations are not yet ported
