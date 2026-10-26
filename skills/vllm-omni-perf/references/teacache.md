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
- Ming-Image (Design, Design-Layer)

## Ming-Image (Design / Design-Layer)

Ming-Image step caching is opt-in (disabled by default). Ming-Image uses zero negative conditioning (empty `negative_prompt`); height/width must be divisible by 16. Configure via `--cache-backend` + `--cache-config`:

```bash
# Design — TeaCache (default rel_l1_thresh 0.3)
vllm serve inclusionAI/Ming-Image-0.1-Design --omni \
  --cache-backend tea_cache --cache-config '{"rel_l1_thresh":0.3}'

# Design — Cache-DiT (residual_diff_threshold 0.16)
vllm serve inclusionAI/Ming-Image-0.1-Design --omni \
  --cache-backend cache_dit --cache-config '{"residual_diff_threshold":0.16}'
```

Design-Layer uses TeaCache threshold 0.13 and Cache-DiT 0.16. Measured E2E latency reduction vs no-cache (2×H100, 1024×1024, 12 steps): Design TeaCache 6.8%, Design Cache-DiT 23.5%, Design-Layer TeaCache 18.7%, Design-Layer Cache-DiT 23.3%.

## Combining with Other Optimizations

TeaCache can be combined with:
- Tensor parallelism (recommended)
- CPU offloading (compatible)
- Quantization (compatible)
- Sequence parallelism (compatible)

Test combinations incrementally to isolate quality/speed trade-offs.
