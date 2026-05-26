---
name: vllm-omni-quantization
description: Use when working on vLLM-Omni quantization for autoregressive, diffusion, or multi-stage omni models, choosing methods such as `awq`, `gptq`, `fp8`, `int8`, `gguf`, or ModelOpt checkpoints, adding quantized model support, or debugging memory, loader, quality, or performance issues.
---

# vLLM-Omni Quantization

## Overview

Use this skill for `vllm-omni` quantization work. The current codebase has a unified quantization framework centered on `vllm_omni.quantization.build_quant_config()`, but the runtime integration still splits into distinct patterns:

- AR and general quantization inherited from upstream `vllm`
- diffusion quantization for DiT models in `vllm-omni`, currently `fp8`, `int8`, and `gguf`
- multi-stage omni quantization using scoped pre-quantized checkpoints such as Qwen3-Omni thinker ModelOpt checkpoints

Core principle: keep generic quantization infrastructure in upstream `vllm`. Keep `vllm-omni` focused on unified config routing, component scoping, diffusion-specific model wiring, adapter logic, and verification.

## Quick Decision

| Task | Use |
|------|-----|
| Quantize Qwen-Omni, Qwen-TTS, or another AR-backed model | `references/methods.md` and `references/modality-compat.md` |
| Use `build_quant_config()` or per-component quantization | `references/methods.md` |
| Quantize diffusion transformer weights with `fp8`, `int8`, or `gguf` | `references/diffusion.md` |
| Add quantization support to a new diffusion model | `references/adding-models.md` |
| Add a new quantization method such as `nvfp4` or a new ModelOpt path | `references/diffusion.md` and `references/adding-models.md` |
| Unsure whether a change belongs in `vllm` or `vllm-omni` | `references/diffusion.md` |

## When to Use

- Choosing a quantization method for memory or throughput
- Checking whether a modality or model family actually supports quantization
- Using the unified `build_quant_config()` entrypoint or per-component config dicts
- Enabling diffusion `fp8`, `int8`, or `gguf`
- Adding a new diffusion quantization method or a pre-quantized multi-stage model path
- Debugging quantized loading, tensor-name mapping, shape mismatch, quality drift, or performance regressions

## AR vs Diffusion Boundary

- AR and general quantization usually mean upstream `vllm` methods such as `awq`, `gptq`, `fp8`, and KV-cache FP8.
- Diffusion quantization means `vllm-omni` DiT-specific integration on top of the unified framework and should not duplicate upstream `vllm` kernels or config semantics.
- Multi-stage omni quantization often means pre-quantized checkpoints whose scope must be constrained to the intended component, such as the thinker `language_model`.

Rule: if a new method is missing generic kernels, loader behavior, or config classes, fix upstream `vllm` first. `vllm-omni` should add thin wrappers, component routing, and model-specific wiring, not a private quantization stack.

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
| unified config behaves unexpectedly | per-component dict, default routing, or method override is misunderstood | check `references/methods.md` and `references/diffusion.md` |
| AR model quality drops too much | aggressive 4-bit setup or wrong method | check calibration and method tradeoffs in `references/methods.md` |
| diffusion method works on one image only | no baseline comparison, no LPIPS gate, or no `ignored_layers` tuning | use the verification flow in `references/diffusion.md` and `references/adding-models.md` |
| GGUF mapping fails | missing architecture-specific adapter | add explicit adapter logic, do not rely on generic fallback |
| new quantization method design keeps growing | unified framework boundary is unclear | re-check ownership before touching model code |
| multi-stage omni checkpoint loads but wrong stages get quantized | component scope is not constrained correctly | check component routing and model config normalization |
| diffusion FA uses wrong KV-cache dtype when `--kv-cache-dtype` is passed | vLLM's `--kv-cache-dtype` leaked into diffusion config | use `--diffusion-kv-cache-dtype` instead (#3596) |
| offline text_to_image fails | quantization config conflicts with diffusion pipeline init | fixed in #1515, update vllm-omni |
| OmniDiffusion init crash | `pipeline_class` variable not initialized during quantized load | fixed in #1562, update vllm-omni |
| HunyuanImage3.0 load_weights error | weight loading fails with quantized HunyuanImage3.0 | fixed in #1598, update vllm-omni |

## References

- AR and general methods: [references/methods.md](references/methods.md)
- Model and modality support matrix: [references/modality-compat.md](references/modality-compat.md)
- Diffusion `fp8`, `int8`, `gguf`, and unified-framework workflow: [references/diffusion.md](references/diffusion.md)
- Adding quantization support to a new model: [references/adding-models.md](references/adding-models.md)
