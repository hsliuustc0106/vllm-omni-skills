---
name: vllm-omni-quantization
description: Quantize vLLM-Omni models to reduce GPU memory usage and improve inference speed. Use when reducing VRAM requirements, fitting larger models on fewer GPUs, lowering serving costs, applying AWQ or GPTQ quantization, configuring FP8 KV cache, or verifying quality after quantization.
---

# vLLM-Omni Quantization

## Overview

Quantization reduces model precision to decrease memory usage and increase throughput. vLLM-Omni inherits quantization support from vLLM for autoregressive (AR) model components. Diffusion (DiT) components have limited quantization support and typically remain in BF16/FP16.

## When to Quantize

| Situation | Recommendation |
|-----------|---------------|
| Model doesn't fit in GPU VRAM | AWQ or GPTQ 4-bit |
| Need faster AR decode | AWQ or FP8 |
| Diffusion model is slow | Use TeaCache/Cache-DiT instead (see vllm-omni-perf) |
| Already have quantized model on HF | Serve directly with `--quantization` flag |

## Method Selection Guide

| Method | Precision | VRAM vs BF16 | Speed | Best For |
|--------|-----------|--------------|-------|----------|
| BF16 | 16-bit | 1x (baseline) | Baseline | Default, best quality |
| FP16 | 16-bit | 1x | Baseline | Older GPUs without BF16 |
| AWQ | 4-bit weights | ~0.25x | 1.2-1.5x faster | Production, minimal quality loss |
| GPTQ | 4-bit weights | ~0.25x | 1.2-1.4x faster | Production, offline calibration |
| FP8 | 8-bit weights | ~0.5x | 1.1-1.3x faster | H100/H200 with FP8 hardware |

## Serving a Pre-Quantized Model

The fastest path: find a pre-quantized model on HuggingFace and serve it directly.

**Search on HuggingFace**: append `-AWQ`, `-GPTQ`, or `-fp8` to the base model name, e.g.:
- `Qwen/Qwen2.5-Omni-7B-AWQ`
- `Qwen/Qwen2.5-Omni-7B-GPTQ-Int4`

```bash
# AWQ
vllm serve Qwen/Qwen2.5-Omni-7B-AWQ --omni --quantization awq --port 8091

# GPTQ
vllm serve Qwen/Qwen2.5-Omni-7B-GPTQ-Int4 --omni --quantization gptq --port 8091

# FP8 (H100/H200 only)
vllm serve Qwen/Qwen2.5-Omni-7B-FP8 --omni --quantization fp8 --port 8091
```

## Applying AWQ Quantization Yourself

If no pre-quantized version exists, quantize with [AutoAWQ](https://github.com/casper-hansen/AutoAWQ):

### Step 1: Install AutoAWQ

```bash
pip install autoawq
```

### Step 2: Quantize

```python
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

model_path = "Qwen/Qwen2.5-Omni-7B"
quant_path = "Qwen2.5-Omni-7B-AWQ"

model = AutoAWQForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

quant_config = {"zero_point": True, "q_group_size": 128, "w_bit": 4, "version": "GEMM"}
model.quantize(tokenizer, quant_config=quant_config)

model.save_quantized(quant_path)
tokenizer.save_pretrained(quant_path)
```

### Step 3: Serve

```bash
vllm serve ./Qwen2.5-Omni-7B-AWQ --omni --quantization awq --port 8091
```

## Applying GPTQ Quantization Yourself

Using [AutoGPTQ](https://github.com/AutoGPTQ/AutoGPTQ):

```python
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
from transformers import AutoTokenizer

model_path = "Qwen/Qwen2.5-Omni-7B"
quant_path = "Qwen2.5-Omni-7B-GPTQ-4bit"

tokenizer = AutoTokenizer.from_pretrained(model_path)
quantize_config = BaseQuantizeConfig(bits=4, group_size=128)

model = AutoGPTQForCausalLM.from_pretrained(model_path, quantize_config)
examples = [tokenizer("Quantization calibration text", return_tensors="pt")]
model.quantize(examples)
model.save_quantized(quant_path)
```

## KV Cache Quantization

Independently from weight quantization, reduce KV cache memory with FP8:

```bash
vllm serve <model> --omni --kv-cache-dtype fp8
```

Compatible with any weight dtype. Reduces KV cache memory by ~50% with minimal quality impact on long-context requests.

## Dtype-Only (No Weight Quantization)

For a quick memory reduction without full quantization:

```bash
# BF16 (default on Ampere+, recommended)
vllm serve <model> --omni --dtype bfloat16

# FP16 (for older GPUs)
vllm serve <model> --omni --dtype float16
```

## Quality Verification

After applying quantization, compare outputs against BF16 baseline:

```python
from vllm_omni.entrypoints.omni import Omni

test_prompts = [
    "a red circle on white background",
    "a sunset over mountains",
    "a cartoon cat",
]

omni_baseline = Omni(model="<base-model>")
omni_quantized = Omni(model="<quantized-model>", quantization="awq")

for prompt in test_prompts:
    base_out = omni_baseline.generate(prompt)
    quant_out = omni_quantized.generate(prompt)
    base_out[0].request_output[0].images[0].save(f"base_{prompt[:10]}.png")
    quant_out[0].request_output[0].images[0].save(f"quant_{prompt[:10]}.png")
```

Visually inspect outputs. For text tasks, compare perplexity or run task-specific evals.

## Memory Estimation

| Model | BF16 | AWQ 4-bit | FP8 |
|-------|------|-----------|-----|
| 3B | 6 GB | 2 GB | 3 GB |
| 7B | 14 GB | 4 GB | 7 GB |
| 14B | 28 GB | 8 GB | 14 GB |
| 30B | 60 GB | 16 GB | 30 GB |

Values are weight-only estimates. Add ~20-30% for KV cache, activations, and framework overhead.

## Troubleshooting

**`quantization` flag has no effect**: Ensure the loaded model was actually quantized. Check HF model card for quantization details.

**Lower quality than expected**: AWQ and GPTQ are calibrated on text data -- image/video/TTS quality is more sensitive. Use a larger group size (`q_group_size=64` instead of 128) for better quality at slight memory cost.

**FP8 not supported**: FP8 weight quantization requires H100/H200 (compute capability 9.0+). FP8 KV cache works on A100/A800 as well.

**OOM despite quantization**: KV cache is not reduced by weight quantization alone. Add `--kv-cache-dtype fp8` to also compress KV cache, or reduce `--max-model-len`.

## References

- For detailed method comparisons and calibration options, see [references/methods.md](references/methods.md)
- For per-modality quantization compatibility, see [references/modality-compat.md](references/modality-compat.md)


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix load_weights error when loading HunyuanImage3.0](https://github.com/vllm-project/vllm-omni/pull/1598)

### Changes
- Bug fix: [BugFix] Fix load_weights error when loading HunyuanImage3.0

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix unexpected crash when init OmniDiffusion](https://github.com/vllm-project/vllm-omni/pull/1562)

### Changes
- Bug fix: [BugFix] Fix unexpected crash when init OmniDiffusion

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Debug] Enable curl retry aligned with openai](https://github.com/vllm-project/vllm-omni/pull/1539)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] fix offline text_to_image error from #1009](https://github.com/vllm-project/vllm-omni/pull/1515)

### Changes
- Bug fix: [Bugfix] fix offline text_to_image error from #1009

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Doc] Update installation instructions for vllm 0.16.0](https://github.com/vllm-project/vllm-omni/pull/1505)


*Updated: 2026-03-04*
