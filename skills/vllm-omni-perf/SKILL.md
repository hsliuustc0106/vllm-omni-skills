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

**Source**: [[BugFix][Qwen3TTS] CodePredictor CudaGraph Pool](https://github.com/vllm-project/vllm-omni/pull/2059)

### Changes
- Bug fix: [BugFix][Qwen3TTS] CodePredictor CudaGraph Pool

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[bugfix] /chat/completion doesn't read extra_body for diffusion model](https://github.com/vllm-project/vllm-omni/pull/2042)

### Changes
- Bug fix: [bugfix] /chat/completion doesn't read extra_body for diffusion model

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Test] Implement mock HTTP request handling in benchmark CLI tests](https://github.com/vllm-project/vllm-omni/pull/2014)


*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Fixbug][Perf] Qwen3-omni: code predictor with re-prefill + SDPA and eliminate decode hot-path CPU round-trips](https://github.com/vllm-project/vllm-omni/pull/2012)

### Changes
- Bug fix: [Fixbug][Perf] Qwen3-omni: code predictor with re-prefill + SDPA and eliminate decode hot-path CPU round-trips

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Perf] [Qwen3-TTS] Keep audio_codes and last_talker_hidden on GPU to eliminate per-step sync stalls](https://github.com/vllm-project/vllm-omni/pull/1985)

### Changes
- Performance improvement: [Perf] [Qwen3-TTS] Keep audio_codes and last_talker_hidden on GPU to eliminate per-step sync stalls

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix config misalignment between offline and online diffusion inference (Wan2.2, Qwen-Image series)](https://github.com/vllm-project/vllm-omni/pull/1979)

### Changes
- Bug fix: [Bugfix] Fix config misalignment between offline and online diffusion inference (Wan2.2, Qwen-Image series)

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Test] L4 complete diffusion feature test for Bagel models](https://github.com/vllm-project/vllm-omni/pull/1938)

### Changes
- New feature: [Test] L4 complete diffusion feature test for Bagel models

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [Fix OmniGen2 transformer config loading for HF models](https://github.com/vllm-project/vllm-omni/pull/1934)

### Changes
- Bug fix: Fix OmniGen2 transformer config loading for HF models

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Bug][Qwen3TTS][Streaming] remove dynamic initial chunk and only compute on initial request](https://github.com/vllm-project/vllm-omni/pull/1930)


*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] fix helios video generate use cpu device](https://github.com/vllm-project/vllm-omni/pull/1915)

### Changes
- Bug fix: [Bugfix] fix helios video generate use cpu device

*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Optim][Qwen3TTS][CodePredictor] support torch.compile with reduce-overhead and dynamic False](https://github.com/vllm-project/vllm-omni/pull/1913)


*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Entrypoint][Refactor] vLLM-Omni Entrypoint Refactoring](https://github.com/vllm-project/vllm-omni/pull/1908)


*Updated: 2026-03-22*


## Recent Updates (Auto-generated)

**Source**: [[Feature]: Remove some useless `hf_overrides` in yaml](https://github.com/vllm-project/vllm-omni/pull/1898)

### Changes
- New feature: [Feature]: Remove some useless `hf_overrides` in yaml

*Updated: 2026-03-22*
