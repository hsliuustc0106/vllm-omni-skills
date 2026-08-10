# Diffusion Quantization Reference

The local `vllm-omni` diffusion quantization methods are:

- `fp8`
- `int8`
- `gguf`

Use this file when working on DiT quantization, the unified quantization framework, adding a new method such as `nvfp4`, or debugging loader, mapping, quality, or performance issues.

## Ownership Boundary

- Upstream `vllm`: `QuantizationConfig`, quant methods, kernels, generic loader behavior, generic post-load processing, non-diffusion hardware rules
- `vllm-omni`: `build_quant_config()` integration, `ComponentQuantizationConfig`, diffusion model wiring, GGUF adapters, pre-quantized model scoping, docs and tests

Rule: if a method is missing generic kernels, loader semantics, or config classes, fix upstream `vllm` first. `vllm-omni` should add a thin diffusion wrapper, not a private quantization stack.

## Unified Framework

Prefer the unified entrypoint:

```python
from vllm_omni.quantization import build_quant_config
```

Supported shapes:

- `"fp8"` / `"int8"` / other method strings
- `{"method": "fp8", ...}`
- per-component dicts such as `{"transformer": {"method": "fp8"}, "vae": None}`
- already-built `QuantizationConfig`

Use per-component configs when only part of a model should be quantized or when multi-stage pipelines need explicit scoping.

## Existing Methods

### FP8

- Online quantization from BF16 or FP16 weights
- Reuses upstream `vllm` FP8 infrastructure
- Flow: user config -> `build_quant_config()` -> quant config routed into transformer linear layers and other components
- `DiffusersPipelineLoader` must still run `process_weights_after_loading()` for modules with quant methods

Starting points:

- `Qwen-Image`, `Qwen-Image-2512`: begin with `ignored_layers=["img_mlp"]`
- `Tongyi-MAI/Z-Image-Turbo`: start with all layers quantized
- `FLUX.1-dev`, `HunyuanImage-3`, `HunyuanVideo-1.5`: documented in current FP8 support tables
- `MiniMax H3`: `--quantization fp8` with structured `--diffusion-quantization-config` for component-scoped ignore (#5737). Transformer uses per-module `prefix` strings; QKV reorder and gate/up split happen in `load_weights` (not module constructors), so online FP8's `process_weights_after_loading` sees correct sharding. Incompatible with layerwise offload. Quality baseline: LPIPS 0.1156, PSNR 23.63 dB at 384×672 107-frame 10-step, 22% memory reduction.

Prefer dynamic activation scaling unless static calibration is explicitly required.

### Int8

- Online or serialized Int8 path for diffusion transformers
- CUDA and NPU aware implementation exists in `DiffusionInt8Config`
- Uses `ignored_layers` in the same way as FP8

Starting points:

- `Qwen-Image`, `Qwen-Image-2512`: documented Int8 support
- `Tongyi-MAI/Z-Image-Turbo`: documented Int8 support

Int8 is more likely than FP8 to require layer-level tuning for quality.

**NPU (Ascend) Int8**: `--quantization int8` on NPU uses the INT8 online path. Layers wider than 65535 output dims per rank stay unquantized automatically. Supports `offload_after_quant` to cap load-time device footprint by returning quantized layers to CPU. Use `--dlo-no-use-allgather` with distributed layerwise offload (AllGather + INT8 incompatible on NPU). RainFusion attention (`--diffusion-attention-backend RAINFUSION_ATTN`) is required for video diffusion with INT8 on NPU (#5706).

### GGUF

- Native quantized transformer-weight loading
- Requires `quantization_config.gguf_model`
- Resolve GGUF as a local file, `repo/file.gguf`, or `repo:quant_type`
- If the GGUF repo lacks `model_index.json`, use the base HF repo for config and use GGUF only for transformer weights

Implementation rules:

- Do not use `state_dict()` to discover GGUF loadable names; use `named_parameters()` and `named_buffers()`
- Tensor-name mapping must be explicit per architecture
- Do not rely on a fake generic fallback adapter
- Guard fused QKV and KV rewrites so `to_qkv` or `add_kv_proj` are not rewritten twice
- GGUF linear methods expect 2D input; flatten and restore shape around matmul
- Prefer eager mode and `fp16` unless measurement says otherwise

## Adding a New Method

Follow this order:

1. Record the exact date context and current repo behavior.
2. Confirm the method type: online quantization, native quantized checkpoint, GGUF-like external transformer weights, or pre-quantized scoped omni checkpoint.
3. Check upstream `vllm` for config class, kernel path, loader path, and hardware rules.
4. If upstream support exists, integrate it through `build_quant_config()` and add only the required `vllm-omni` override or wrapper.
5. Normalize user config in `vllm_omni/diffusion/data.py` or model config conversion logic without mutating input mappings.
6. Update loader or model-config routing for the correct scope.
7. Thread `quant_config` through every relevant diffusion linear layer or scoped component.
8. Add config, loader, and smoke tests, then update docs and examples.

For `nvfp4`, future ModelOpt formats, or other methods: if the generic method is not already present in upstream `vllm`, do not implement it first as a diffusion-only stack.

## Common Failures

| Symptom | Likely Cause | Fix |
|--------|--------------|-----|
| `Unknown quantization method` | method is not in the unified factory path | add the correct override or upstream registration |
| config behaves strangely | input mapping was mutated or precedence is unclear | copy the mapping and define conflict behavior |
| only some layers quantize | `quant_config` not threaded through all linear layers | audit every transformer linear constructor |
| FP8 or Int8 quality collapses | sensitive layers should stay BF16 | start with `img_mlp` or the model-specific sensitive layer guidance |
| GGUF adapter mismatch | model is unsupported or mapping is missing | add a model-specific adapter |
| GGUF shape mismatch | remap or qkv or ffn split logic is wrong | fix mapping per architecture and re-test with a fixed seed |
| pre-quantized omni checkpoint affects wrong components | quantization scope is not constrained correctly | verify component routing and config normalization |
| quantized path is slower than BF16 | dtype mismatch, kernel behavior, or compile issue | verify dtype, test smaller sizes, compare one-step runs, try eager |

## Verification

- Record the exact date context in notes and docs
- Confirm whether the mode is `fp8`, `int8`, `gguf`, or a new method
- Use a fixed seed and identical prompt, image size, and inference steps
- Compare against a BF16 baseline for both quality and speed
- For GGUF, verify architecture-specific mapping before full end-to-end runs
- For new methods, pass config and loader-path tests before claiming the model path works
- Fail clearly on unsupported models; do not leave half-working fallback behavior
