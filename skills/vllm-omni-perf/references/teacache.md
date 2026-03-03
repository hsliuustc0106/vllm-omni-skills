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

## Combining with Other Optimizations

TeaCache can be combined with:
- Tensor parallelism (recommended)
- CPU offloading (compatible)
- Quantization (compatible)
- Sequence parallelism (compatible)

Test combinations incrementally to isolate quality/speed trade-offs.
