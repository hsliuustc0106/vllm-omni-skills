---
name: vllm-omni-image-gen
description: Generate and edit images with vLLM-Omni using models like FLUX, Stable Diffusion 3, Qwen-Image, GLM-Image, BAGEL, and Z-Image. Use when generating images from text, editing images, configuring diffusion parameters, or working with image generation models.
---

# vLLM-Omni Image Generation

## Overview

vLLM-Omni supports text-to-image generation and image editing through diffusion transformer (DiT) models and multi-stage AR+DiT pipelines. Supported model families include FLUX, Stable Diffusion 3, Qwen-Image, GLM-Image, BAGEL, Z-Image, OmniGen2, and more.

## Supported Image Models

| Model | HF ID | Type | Min VRAM |
|-------|-------|------|----------|
| Z-Image-Turbo | `Tongyi-MAI/Z-Image-Turbo` | Text-to-image | 8 GB |
| Qwen-Image | `Qwen/Qwen-Image` | Text-to-image (AR+DiT) | 24 GB |
| Qwen-Image-Edit | `Qwen/Qwen-Image-Edit` | Image editing | 24 GB |
| GLM-Image | `zai-org/GLM-Image` | Text-to-image | 24 GB |
| BAGEL-7B-MoT | `ByteDance-Seed/BAGEL-7B-MoT` | Text-to-image + understanding | 24 GB |
| FLUX.1-dev | `black-forest-labs/FLUX.1-dev` | Text-to-image | 40 GB |
| FLUX.2-klein | `black-forest-labs/FLUX.2-klein-4B` | Text-to-image | 16 GB |
| SD 3.5 Medium | `stabilityai/stable-diffusion-3.5-medium` | Text-to-image | 12 GB |
| OmniGen2 | `OmniGen2/OmniGen2` | Text-to-image | 24 GB |
| HunyuanImage3.0 | `tencent/HunyuanImage-3.0` | Text-to-image | 40 GB |

## Quick Start: Offline Generation

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Tongyi-MAI/Z-Image-Turbo")
outputs = omni.generate("a cup of coffee on a table")
outputs[0].request_output[0].images[0].save("coffee.png")
```

## Quick Start: Online API

```bash
# Start server
vllm serve Tongyi-MAI/Z-Image-Turbo --omni --port 8091

# Generate via API
curl -s http://localhost:8091/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "a sunset over mountains"}],
    "extra_body": {
      "height": 1024, "width": 1024,
      "num_inference_steps": 50,
      "guidance_scale": 4.0,
      "seed": 42
    }
  }' | jq -r '.choices[0].message.content[0].image_url.url' \
     | cut -d',' -f2 | base64 -d > sunset.png
```

## Diffusion Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `height` | Output height in pixels | 512-2048 |
| `width` | Output width in pixels | 512-2048 |
| `num_inference_steps` | Denoising steps (more = higher quality, slower) | 20-100 |
| `guidance_scale` | CFG scale (higher = more prompt adherence) | 1.0-15.0 |
| `seed` | Random seed for reproducibility | Any integer |
| `negative_prompt` | What to avoid in the image | Text string |

## Image Editing

For models that support image editing (Qwen-Image-Edit, LongCat-Image-Edit):

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Qwen/Qwen-Image-Edit")
outputs = omni.generate(
    prompt="Change the sky to sunset colors",
    images=["input.jpg"],
)
outputs[0].request_output[0].images[0].save("edited.png")
```

## Batch Generation

```python
omni = Omni(model="Tongyi-MAI/Z-Image-Turbo")
prompts = [
    "a red car on a highway",
    "a blue ocean with waves",
    "a green forest in autumn",
]
outputs = omni.generate(prompts)
for i, out in enumerate(outputs):
    out.request_output[0].images[0].save(f"image_{i}.png")
```

Note: diffusion pipeline `max_batch_size` defaults to 1. Input lists are processed sequentially unless you modify stage configs to increase batch size.

## Choosing a Model

- **Fast prototyping**: Z-Image-Turbo (small, fast)
- **High quality**: FLUX.1-dev or HunyuanImage3.0
- **Low VRAM**: SD 3.5 Medium or FLUX.2-klein-4B
- **Image editing**: Qwen-Image-Edit
- **Understanding + generation**: BAGEL-7B-MoT

## Troubleshooting

**Black or blank images**: Increase `num_inference_steps`. Some models need 50+ steps for good results.

**Out of memory**: Reduce resolution, or use CPU offloading:
```bash
vllm serve <model> --omni --cpu-offload-gb 10
```

**Slow generation**: Enable TeaCache for 1.5-2x speedup (see vllm-omni-perf skill).

## References

- For FLUX model details, see [references/flux-models.md](references/flux-models.md)
- For Qwen-Image family, see [references/qwen-image.md](references/qwen-image.md)
- For image editing workflows, see [references/image-edit.md](references/image-edit.md)


## Recent Updates (Auto-generated)

**Source**: [[FP8 Quantization] Add FP8 quantization support for Flux transformer](https://github.com/vllm-project/vllm-omni/pull/1640)

### Changes
- New feature: [FP8 Quantization] Add FP8 quantization support for Flux transformer

### New Features
- text-to-image
- Text-to-Image
- Flux

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation](https://github.com/vllm-project/vllm-omni/pull/1609)

### Changes
- Bug fix: [Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation

### New Features
- GLM-Image
- GLM-Image
- GLM-Image
- GLM-Image
- GLM-Image
- GLM-Image
- GLM-Image
- GLM-Image

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix load_weights error when loading HunyuanImage3.0](https://github.com/vllm-project/vllm-omni/pull/1598)

### Changes
- Bug fix: [BugFix] Fix load_weights error when loading HunyuanImage3.0

### New Features
- HunyuanImage3
- HunyuanImage3Pipeline
- HunyuanImage3
- HunyuanImage-3
- HunyuanImage-3
- HunyuanImage-3
- HunyuanImage3Pipeline
- HunyuanImage3Pipeline
- HunyuanImage3Pipeline
- HunyuanImage3Pipeline
- HunyuanImage3Pipeline
- HunyuanImage3Pipeline
- HunyuanImage3Pipeline
- HunyuanImage3Pipeline
- HunyuanImage-3

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[NPU] [Features] [Bugfix] Support mindiesd adaln](https://github.com/vllm-project/vllm-omni/pull/1537)

### Changes
- New feature: [NPU] [Features] [Bugfix] Support mindiesd adaln

### New Features
- mindiesd
- mindiesd
- Qwen-Image-Edit-2509
- mindiesd
- mindiesd
- mindiesd
- mindiesd

*Updated: 2026-03-08*
