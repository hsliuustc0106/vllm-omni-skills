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
| FLUX.2-dev | `black-forest-labs/FLUX.2-dev` | Text-to-image + cache_dit | 24 GB |
| Dreamid-Omni | `bytedance/dreamid-omni` | Text-to-image (ByteDance) | 24 GB |
| SD 3.5 Medium | `stabilityai/stable-diffusion-3.5-medium` | Text-to-image | 12 GB |
| OmniGen2 | `OmniGen2/OmniGen2` | Text-to-image | 24 GB |
| HunyuanImage3.0 | `tencent/HunyuanImage-3.0` | Text-to-image + editing | 40 GB |

Dreamid-Omni from ByteDance and FLUX.2-dev with cache_dit support are available. FLUX.2-klein supports plain string prompts (no dict wrapper needed).

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

For models that support image editing (Qwen-Image-Edit, LongCat-Image-Edit, HunyuanImage3.0):

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
- **Image editing**: Qwen-Image-Edit or HunyuanImage3.0
- **Understanding + generation**: BAGEL-7B-MoT

## Troubleshooting

**Black or blank images**: Increase `num_inference_steps`. Some models need 50+ steps for good results.

**Out of memory**: Reduce resolution, or use CPU offloading:
```bash
vllm serve <model> --omni --cpu-offload-gb 10
```

**Slow generation**: Enable TeaCache for 1.5-2x speedup (see vllm-omni-perf skill). Multi-thread weight loading (enabled by default for diffusion models) also reduces startup time significantly.

**HunyuanImage3.0 garbage output in offline inference**: Fixed in #3243. The AR stage now uses the Instruct chat template (`User:`/`Assistant:` framing) instead of the pretrain format. Trigger tags (`💭`, `<recaption>`) must go *after* `Assistant:`, not before the user prompt. Use `build_prompt_tokens()` from `vllm_omni.diffusion.models.hunyuan_image3.prompt_utils` for segment-by-segment tokenization that avoids cross-segment BPE merges. MoE routing now runs in fp32 (matching HF). VAE pixel values must stay fp32 through preprocessing — do not pre-cast to bf16.

**HunyuanImage3.0 load_weights error**: Fixed in #1598. Ensure you are using the latest vllm-omni.

**HunyuanImage3 online/offline output mismatch**: Fixed in #3500/#3516. Online multistage path now uses `build_prompt_tokens()` matching offline behavior.

**HunyuanImage3 AR sampler fails with batched requests**: Fixed in #3590. `max_num_seqs > 1` now supported for AR sampling.

**HunyuanImage3 deploy config fails at startup**: Fixed in #3537. Pipeline name changed to `hunyuan_image_3_moe`; update any custom deploy YAMLs.

**HunyuanImage3 KV reuse broken under sequence parallel**: Fixed in #3546. `ar_kv_reuse_len` is now propagated through the DiT forward pass.

**Diffusers backend crash on models without `model_index.json`**: Fixed in #3644. Non-diffusers-format models now emit a warning instead of crashing.

**GLM-Image filepath errors**: Fixed in #1609. Models with `model_subdir` or `tokenizer_subdir` now resolve paths correctly.

**BAGEL think mode for text2text/img2text**: BAGEL now supports reasoning/thinking mode for text-to-text and image-to-text modalities via `--think` flag. Injects `VLM_THINK_SYSTEM_PROMPT` to enable chain-of-thought output. Fixed in #2503.

**Qwen-Image tiny request sizes**: Small requests (below VAE alignment) are now clamped to minimum valid dimensions instead of collapsing to zero. All Qwen-Image pipeline variants use the shared `normalize_min_aligned_size()` helper. Fixed in #2637.

## References

- For FLUX model details, see [references/flux-models.md](references/flux-models.md)
- For Qwen-Image family, see [references/qwen-image.md](references/qwen-image.md)
- For image editing workflows, see [references/image-edit.md](references/image-edit.md)
