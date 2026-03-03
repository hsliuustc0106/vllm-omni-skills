# Quantization Methods

## Overview

Quantization reduces model precision to lower memory usage and increase inference speed. vLLM-Omni supports several quantization methods through the upstream vLLM engine.

## Supported Methods

| Method | Precision | Speed | Quality | Memory Savings |
|--------|-----------|-------|---------|----------------|
| BF16 | 16-bit brain float | Baseline | Best | Baseline |
| FP16 | 16-bit float | Baseline | Best | Baseline |
| AWQ | 4-bit weights | 1.2-1.5x | Good | ~4x |
| GPTQ | 4-bit weights | 1.2-1.4x | Good | ~4x |
| SqueezeLLM | Mixed precision | 1.1-1.3x | Good | ~2-3x |

## Usage

### Default Precision (BF16)

```bash
vllm serve <model> --omni --dtype bfloat16
```

### AWQ Quantization

Requires a pre-quantized model:

```bash
vllm serve <model-awq> --omni --quantization awq
```

### GPTQ Quantization

```bash
vllm serve <model-gptq> --omni --quantization gptq
```

## Applicability

Quantization primarily applies to the autoregressive components:
- Language model backbone in omni models
- AR stage in multi-stage pipelines

Diffusion model components (DiT) typically run in BF16/FP16 and have limited quantization support.

## Quality Considerations

- AWQ 4-bit typically preserves 95%+ of BF16 quality for text tasks
- Image/video generation quality is more sensitive to quantization
- Test with representative prompts before deploying quantized models in production
- Voice cloning (TTS) quality may degrade with aggressive quantization

## Memory Estimation

| Model Size | BF16 VRAM | AWQ 4-bit VRAM |
|------------|-----------|----------------|
| 3B | 6 GB | 2 GB |
| 7B | 14 GB | 4 GB |
| 14B | 28 GB | 8 GB |
| 30B | 60 GB | 16 GB |

Actual VRAM includes KV cache, activations, and framework overhead beyond weight storage.
