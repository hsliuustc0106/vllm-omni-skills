---
name: vllm-omni-quantization
description: Use when working on vLLM-Omni quantization for autoregressive or diffusion models, choosing methods such as `awq`, `gptq`, `fp8`, or `gguf`, adding diffusion methods like `int8` or `nvfp4`, or debugging memory, loader, quality, or performance issues.
---

# vLLM-Omni Quantization

## Overview

Use this skill for `vllm-omni` quantization work. Quantization work in this codebase splits into two distinct paths:

- AR and omni-model quantization inherited from upstream `vllm`
- diffusion quantization for DiT models in `vllm-omni`, currently `fp8` and `gguf`

Core principle: keep generic quantization infrastructure in upstream `vllm`. Keep `vllm-omni` focused on diffusion-specific config glue, model wiring, adapter logic, and verification.

## Quick Decision

| Task | Use |
|------|-----|
| Quantize Qwen-Omni, Qwen-TTS, or another AR-backed model | `references/methods.md` and `references/modality-compat.md` |
| Reduce KV cache memory | `references/methods.md` |
| Quantize diffusion transformer weights with `fp8` or `gguf` | `references/diffusion.md` |
| Add a diffusion method such as `int8` or `nvfp4` | `references/diffusion.md` |
| Unsure whether a change belongs in `vllm` or `vllm-omni` | `references/diffusion.md` |

## When to Use

- Choosing a quantization method for memory or throughput
- Checking whether a modality or model family actually supports quantization
- Enabling diffusion `fp8` or `gguf`
- Adding a new diffusion quantization method
- Debugging quantized loading, tensor-name mapping, shape mismatch, quality drift, or performance regressions

## AR vs Diffusion Boundary

- AR quantization usually means upstream `vllm` methods such as `awq`, `gptq`, `fp8`, and KV-cache FP8.
- Diffusion quantization means `vllm-omni` DiT-specific integration and should not duplicate upstream `vllm` kernels or config semantics.

Rule: if a new method is missing generic kernels, loader behavior, or config classes, fix upstream `vllm` first. Only add a thin diffusion wrapper in `vllm-omni`.

## Example: Enable FP8 for a Diffusion Model

```bash
# 1. Start server with fp8 quantization
vllm serve black-forest-labs/FLUX.1-dev --omni \
  --quantization fp8 --tensor-parallel-size 2

# 2. Verify quantized model loaded correctly
curl -s http://localhost:8091/v1/models | python3 -c "
import sys, json
models = json.load(sys.stdin)['data']
print(f'Loaded: {models[0][\"id\"]}') if models else print('ERROR: No models loaded')
"

# 3. Generate test image with fixed seed for quality comparison
curl -s http://localhost:8091/v1/images/generations \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"a cat","seed":42}' -o test_fp8.json

# 4. Compare against BF16 baseline (run separately without --quantization)
# If PSNR < 25 dB or visual artifacts appear, check references/diffusion.md
```

## Common Mistakes

| Symptom | Likely Cause | Fix |
|--------|--------------|-----|
| `quantization` flag has no visible effect | wrong model stage or unsupported modality | check `references/modality-compat.md` |
| AR model quality drops too much | aggressive 4-bit setup or wrong method | check calibration and method tradeoffs in `references/methods.md` |
| diffusion method works on one image only | no baseline comparison or controlled verification | use fixed-seed BF16 comparison from `references/diffusion.md` |
| GGUF mapping fails | missing architecture-specific adapter | add explicit adapter logic, do not rely on generic fallback |
| new diffusion method design keeps growing | upstream/downstream boundary is unclear | re-check ownership before touching model code |

## References

- AR and general methods: [references/methods.md](references/methods.md)
- Model and modality support matrix: [references/modality-compat.md](references/modality-compat.md)
- Diffusion `fp8`, `gguf`, and new-method workflow: [references/diffusion.md](references/diffusion.md)
