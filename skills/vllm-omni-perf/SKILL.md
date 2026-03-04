---
name: vllm-omni-perf
description: Optimize vLLM-Omni performance through benchmarking, TeaCache, Cache-DiT, quantization, CPU offloading, and parallelism tuning. Use when improving inference speed, reducing latency, lowering memory usage, running benchmarks, or enabling diffusion acceleration.
---

# vLLM-Omni Performance Tuning

## Overview

vLLM-Omni provides multiple optimization levers for both autoregressive and diffusion pipelines. Key techniques include KV cache optimization (inherited from vLLM), TeaCache/Cache-DiT for diffusion acceleration, quantization, CPU offloading, and parallelism configuration.

## Optimization Quick Reference

| Technique | Applies To | Speedup | Quality Impact |
|-----------|-----------|---------|----------------|
| TeaCache | Diffusion models | 1.5-2.0x | Minimal |
| Cache-DiT | Diffusion models | 1.3-1.8x | Minimal |
| Quantization | All models | 1.2-1.5x | Slight |
| Tensor Parallelism | All models | Near-linear | None |
| Sequence Parallelism | DiT models | Near-linear | None |
| CPU Offloading | All models | Enables larger models | Adds latency |
| GPU Memory Tuning | All models | More throughput | None |

## TeaCache (Diffusion Acceleration)

TeaCache provides adaptive caching for diffusion transformer denoising steps, skipping redundant computations:

```bash
vllm serve <model> --omni \
  --enable-teacache \
  --teacache-threshold 0.1
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--enable-teacache` | Enable TeaCache | Disabled |
| `--teacache-threshold` | Cache hit threshold (lower = more caching) | Model-specific |

Recommended thresholds by model:
- Image models: 0.05-0.15
- Video models: 0.08-0.20

## Cache-DiT

Alternative diffusion acceleration backend:

```bash
vllm serve <model> --omni --enable-cache-dit
```

Can be combined with TeaCache, but test independently first to measure impact.

## Quantization

For full quantization guidance (method selection, AWQ/GPTQ workflows, FP8 KV cache, quality verification), see the dedicated **[vllm-omni-quantization](../vllm-omni-quantization/SKILL.md)** skill.

## CPU Offloading

Offload model layers to CPU RAM to fit larger models:

### Model-Level Offloading

```bash
vllm serve <model> --omni --cpu-offload-gb 10
```

Offloads approximately 10 GB of model weights to CPU. Adds latency for offloaded layers.

### Layer-Wise Offloading

For diffusion models, layer-wise offloading moves individual transformer layers to CPU between forward passes:

```bash
vllm serve <model> --omni --enable-layerwise-cpu-offload
```

## GPU Memory Configuration

Maximize throughput by tuning GPU memory allocation:

```bash
# Default: 90% of GPU memory
vllm serve <model> --omni --gpu-memory-utilization 0.9

# Conservative: 80% (leaves room for other processes)
vllm serve <model> --omni --gpu-memory-utilization 0.8

# Aggressive: 95%
vllm serve <model> --omni --gpu-memory-utilization 0.95
```

## Benchmarking

### Quick Benchmark

```bash
python -m vllm_omni.benchmarks.benchmark_serving \
  --model Tongyi-MAI/Z-Image-Turbo \
  --num-prompts 100 \
  --port 8091
```

### Measuring Latency

Time a single request:

```bash
time curl -s http://localhost:8091/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "a red circle"}],
    "extra_body": {"height": 512, "width": 512, "num_inference_steps": 20}
  }' > /dev/null
```

### Monitoring During Benchmark

```bash
# GPU utilization
watch -n 1 nvidia-smi

# Server metrics
curl http://localhost:8091/metrics
```

## Optimization Workflow

1. **Baseline**: Run benchmark with default settings
2. **Memory**: Tune `--gpu-memory-utilization` to maximize without OOM
3. **Parallelism**: Add tensor parallelism if multi-GPU available
4. **Caching**: Enable TeaCache or Cache-DiT for diffusion models
5. **Quantization**: Apply if memory-constrained
6. **Offloading**: Use CPU offloading as last resort for large models
7. **Re-benchmark**: Compare against baseline

## Troubleshooting

**No speedup with TeaCache**: Threshold may be too conservative. Lower it gradually (e.g., 0.05) and check quality.

**OOM after optimization**: Quantization reduces memory. Combine with lower `gpu-memory-utilization`.

**Latency regression with TP**: For small models, the communication overhead of tensor parallelism may exceed the compute savings. Use TP only for models that saturate a single GPU.

## References

- For TeaCache configuration details, see [references/teacache.md](references/teacache.md)
- For quantization methods and compatibility, see [references/quantization.md](references/quantization.md)


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix Qwen3-TTS code predictor crash due to missing vLLM config context](https://github.com/vllm-project/vllm-omni/pull/1619)

### Changes
- Bug fix: [Bugfix] Fix Qwen3-TTS code predictor crash due to missing vLLM config context

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation](https://github.com/vllm-project/vllm-omni/pull/1609)

### Changes
- Bug fix: [Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix load_weights error when loading HunyuanImage3.0](https://github.com/vllm-project/vllm-omni/pull/1598)

### Changes
- Bug fix: [BugFix] Fix load_weights error when loading HunyuanImage3.0

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix]: fix a lot of bug](https://github.com/vllm-project/vllm-omni/pull/1565)

### Changes
- Bug fix: [BugFix]: fix a lot of bug

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix unexpected crash when init OmniDiffusion](https://github.com/vllm-project/vllm-omni/pull/1562)

### Changes
- Bug fix: [BugFix] Fix unexpected crash when init OmniDiffusion

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [Fix no embed text spk tokens](https://github.com/vllm-project/vllm-omni/pull/1540)

### Changes
- Bug fix: Fix no embed text spk tokens

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Debug] Enable curl retry aligned with openai](https://github.com/vllm-project/vllm-omni/pull/1539)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix transformers 5.x compat issues in online TTS serving](https://github.com/vllm-project/vllm-omni/pull/1536)

### Changes
- Bug fix: [Bugfix] Fix transformers 5.x compat issues in online TTS serving

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [Revert gpu_1 job to use regular image](https://github.com/vllm-project/vllm-omni/pull/1521)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [Use pull through cache image for H100 pool](https://github.com/vllm-project/vllm-omni/pull/1518)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] fix offline text_to_image error from #1009](https://github.com/vllm-project/vllm-omni/pull/1515)

### Changes
- Bug fix: [Bugfix] fix offline text_to_image error from #1009

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Doc] Update installation instructions for vllm 0.16.0](https://github.com/vllm-project/vllm-omni/pull/1505)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Feature][Wan2.2] Speed up diffusion model startup by multi-thread weight loading](https://github.com/vllm-project/vllm-omni/pull/1504)

### Changes
- New feature: [Feature][Wan2.2] Speed up diffusion model startup by multi-thread weight loading

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] process request.num_cached_tokens if it equals to the initial value ](https://github.com/vllm-project/vllm-omni/pull/1468)

### Changes
- Bug fix: [BugFix] process request.num_cached_tokens if it equals to the initial value 

*Updated: 2026-03-04*
