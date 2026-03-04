# Huawei NPU (Ascend) Backend

## Requirements

- Huawei Ascend 910B accelerator
- CANN (Compute Architecture for Neural Networks) 8.0+
- MindSpore or PyTorch-NPU backend
- Linux (EulerOS or Ubuntu 20.04+)

## Installation

```bash
# Ensure CANN toolkit is installed and sourced
source /usr/local/Ascend/ascend-toolkit/set_env.sh

uv venv --python $PYTHON_VERSION --seed
source .venv/bin/activate

# Install PyTorch with NPU support
pip install torch-npu

git clone https://github.com/vllm-project/vllm-omni.git
cd vllm-omni
pip install -e ".[npu]"
```

## Configuration

### Device Selection

```bash
ASCEND_RT_VISIBLE_DEVICES=0,1 vllm serve <model> --omni --port 8091
```

### Multi-NPU

```bash
vllm serve <model> --omni --tensor-parallel-size 8
```

## Monitoring

```bash
npu-smi info
npu-smi info -t usages
```

## Supported Models on NPU

- Qwen3-Omni, Qwen2.5-Omni
- Qwen-Image, Qwen-Image-Edit, Qwen-Image-Layered
- Z-Image
- Wan2.2 (T2V, I2V, TI2V)
- FLUX.2-klein
- Qwen3-TTS
- LongCat-Image

## Known Limitations

- Not all models from the CUDA model list are supported
- Operator coverage depends on CANN version
- Performance tuning may require CANN-specific graph optimization flags
