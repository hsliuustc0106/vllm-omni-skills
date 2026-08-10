# TeaCache Configuration

## How It Works

TeaCache (Temporal-Adaptive Cache) identifies redundant computations in the diffusion denoising process. During iterative denoising, many intermediate states are similar between adjacent steps. TeaCache detects these similarities and reuses cached computations instead of recomputing.

## Mechanism

1. At each denoising step, compute a lightweight similarity score against the previous cached state
2. If the score exceeds the threshold, reuse the cached output (skip the full transformer forward pass)
3. Otherwise, compute normally and update the cache

This achieves 1.5-2.0x speedup with minimal quality degradation.

## Configuration

```bash
vllm serve <model> --omni \
  --enable-teacache \
  --teacache-threshold <value>
```

## Threshold Tuning

| Threshold | Cache Hit Rate | Speedup | Quality |
|-----------|---------------|---------|---------|
| 0.01 | ~70% | ~2.0x | Slight degradation |
| 0.05 | ~50% | ~1.7x | Minimal degradation |
| 0.10 | ~35% | ~1.5x | Near-lossless |
| 0.20 | ~20% | ~1.3x | Lossless |

**Recommendation**: Start with 0.10 and adjust based on quality evaluation.

## Supported Models

TeaCache works with all DiT-based models in vLLM-Omni:
- FLUX family
- Stable Diffusion 3
- Wan2.2 (T2V, I2V, TI2V)
- Qwen-Image (DiT stage)
- GLM-Image
- Z-Image
- HunyuanImage3.0
- OmniGen2
- MiniMax H3 (FL2VA partition only — Ref2VA rejects TeaCache with ValueError)

### Model-Specific Defaults

When `--teacache-threshold` is not set, the threshold defers to per-model defaults: 0.17 for MiniMax H3, 0.20 fallback for others (#5840). Config files store polynomial coefficients per transformer type for automatic tuning.

### MiniMax H3

TeaCache for MiniMax H3 works only on the FL2VA (frame-to-video) partition. In combined FL2VA+Ref2VA serving, FL2VA requests use TeaCache while Ref2VA requests run uncached. The extractor (`extract_minimax_h3_context`) mirrors the packed multimodal forward path: `_embed` → `blocks` loop (with `video_token_layout` forwarded) → `final_layer` postprocessing with row selection and update masks. Registered under transformer class `MiniMaxH3DiTModel`. TeaCache and Cache-DiT are mutually exclusive on MiniMax H3.

## Combining with Other Optimizations

TeaCache can be combined with:
- Tensor parallelism (recommended)
- CPU offloading (compatible)
- Quantization (compatible)
- Sequence parallelism (compatible)

Test combinations incrementally to isolate quality/speed trade-offs.
