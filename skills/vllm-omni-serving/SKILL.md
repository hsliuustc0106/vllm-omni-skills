---
name: vllm-omni-serving
description: Launch and configure vLLM-Omni API servers for production model serving. Use when starting a model server, configuring stage pipelines, setting up GPU memory, enabling optimizations, or deploying models behind a load balancer.
---

# vLLM-Omni Model Serving

## Overview

vLLM-Omni serves models via an OpenAI-compatible HTTP server. It supports autoregressive models (text, omni), diffusion models (image, video), and TTS models (audio) through a unified `vllm serve` command with the `--omni` flag.

## Quick Start

```bash
vllm serve <model-name> --omni --port 8091
```

**Examples by modality:**

```bash
# Image generation
vllm serve Tongyi-MAI/Z-Image-Turbo --omni --port 8091

# Omni-modality (text + image + audio)
vllm serve Qwen/Qwen2.5-Omni-7B --omni --port 8091

# TTS
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --omni --port 8091

# Video generation
vllm serve Wan-AI/Wan2.2-T2V-A14B-Diffusers --omni --port 8091
```

## Server Configuration

### Key CLI Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--omni` | Enable omni-modality pipeline (required) | `--omni` |
| `--port` | HTTP port | `--port 8091` |
| `--host` | Bind address | `--host 0.0.0.0` |
| `--gpu-memory-utilization` | Fraction of GPU memory to use | `--gpu-memory-utilization 0.85` |
| `--tensor-parallel-size` | Number of GPUs for tensor parallelism | `--tensor-parallel-size 2` |
| `--pipeline-parallel-size` | Pipeline parallelism stages | `--pipeline-parallel-size 2` |
| `--max-model-len` | Maximum sequence length | `--max-model-len 4096` |
| `--dtype` | Model dtype | `--dtype float16` |

### Stage Configuration

vLLM-Omni uses stage configs to define multi-stage pipelines. Each model has default stage configs, but you can customize them:

```bash
vllm serve Qwen/Qwen2.5-Omni-7B --omni \
  --stage-configs-path ./my-stage-config.yaml
```

Stage config structure:

```yaml
stages:
  - name: "encoder"
    stage_type: "ar"
    stage_args:
      runtime:
        max_batch_size: 4
  - name: "diffusion"
    stage_type: "diffusion"
    stage_args:
      runtime:
        max_batch_size: 1
```

The `max_batch_size` for diffusion stages defaults to 1. Increase it only for models that support batched diffusion.

### GPU Memory Configuration

Calculate memory needs based on model size and desired throughput:

```bash
# Conservative (80% GPU memory)
vllm serve <model> --omni --gpu-memory-utilization 0.8

# Aggressive (95% for maximum throughput)
vllm serve <model> --omni --gpu-memory-utilization 0.95
```

## Multi-GPU Serving

### Tensor Parallelism

Split model across multiple GPUs:

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni \
  --tensor-parallel-size 4 --port 8091
```

### Pipeline Parallelism

For very large models:

```bash
vllm serve <model> --omni \
  --tensor-parallel-size 2 \
  --pipeline-parallel-size 2
```

## Production Deployment Checklist

- [ ] Set `--host 0.0.0.0` for external access
- [ ] Configure `--gpu-memory-utilization` based on model size
- [ ] Set appropriate `--max-model-len`
- [ ] Enable `--disable-log-requests` for reduced I/O overhead
- [ ] Place behind a reverse proxy (nginx/caddy) for TLS
- [ ] Configure health check endpoint at `/health`
- [ ] Set up log rotation for server logs
- [ ] Monitor GPU utilization with `nvidia-smi dmon`

## Running Multiple Models

Run separate server instances on different ports:

```bash
# Terminal 1: Image generation
vllm serve Tongyi-MAI/Z-Image-Turbo --omni --port 8091

# Terminal 2: Text/Omni
vllm serve Qwen/Qwen2.5-Omni-7B --omni --port 8092
```

Use a reverse proxy to route by path or model name.

## Troubleshooting

**Server fails to start**: Check GPU memory availability with `nvidia-smi`. Reduce `--gpu-memory-utilization` or choose a smaller model.

**Slow first request**: Model weights are loaded lazily. The first request triggers full model initialization. Subsequent requests are fast.

**Connection refused**: Verify `--host` and `--port` settings. Default host is `127.0.0.1` (localhost only).

**`--dtype` ignored with default stage configs**: When using default stage configs (no `--stage-configs-path`), the `--dtype` arg was silently dropped from diffusion stage engine args. Fixed in #2530 — dtype now correctly propagates from CLI.

**`--stage-init-timeout` not respected**: User-configured stage init timeout was being overridden. Default is now 300s (server-side). Pass `--stage-init-timeout <seconds>` to customize. Fixed in #2519.

**OOM errors produce no response**: Diffusion pipeline OOM and execution errors now return structured HTTP error responses (e.g., 507) with `request_id`, `stage_id`, and `error_type` fields instead of hanging. Uses `OmniRequestError` dataclass for end-to-end propagation. Fixed in #2638.

## References

- For model-specific configurations, see [references/model-configs.md](references/model-configs.md)
- For scaling and load balancing, see [references/scaling-guide.md](references/scaling-guide.md)
