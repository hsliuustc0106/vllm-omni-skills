# Qwen-Image Family

## Architecture

Qwen-Image models use a multi-stage pipeline: an autoregressive (AR) language model generates latent tokens, which are then decoded by a diffusion transformer (DiT) into images. This AR+DiT architecture enables instruction-following image generation.

## Models

### Qwen-Image

- **HF ID**: `Qwen/Qwen-Image`
- **Min VRAM**: 24 GB
- **Capabilities**: Text-to-image with instruction following

```bash
vllm serve Qwen/Qwen-Image --omni --port 8091
```

### Qwen-Image-2512

- **HF ID**: `Qwen/Qwen-Image-2512`
- **Min VRAM**: 24 GB
- **Capabilities**: Text-to-image at up to 2512x2512 resolution

### Qwen-Image-Layered

- **HF ID**: `Qwen/Qwen-Image-Layered`
- **Min VRAM**: 24 GB
- **Capabilities**: Generate images with separate layers (foreground/background)

## Stage Configuration

Qwen-Image uses multi-stage execution. The default stage config handles the AR and DiT stages automatically. For custom batch sizes:

```yaml
stages:
  - name: "ar_stage"
    stage_type: "ar"
    stage_args:
      runtime:
        max_batch_size: 4
  - name: "dit_stage"
    stage_type: "diffusion"
    stage_args:
      runtime:
        max_batch_size: 1
```

## Prompt Best Practices

Qwen-Image responds well to natural language instructions:

```
"Generate a professional headshot photo of a woman with short brown hair"
"Create an oil painting of a medieval castle at sunset"
"Design a minimalist logo for a coffee shop called 'Bean There'"
```
