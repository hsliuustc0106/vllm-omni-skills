# Wan2.2 Video Models

## Architecture

Wan2.2 models use a diffusion transformer architecture for video generation. The models operate in latent space, generating sequences of latent frames that are decoded into video.

## Model Variants

### Wan2.2-T2V-A14B (Text-to-Video)

- **HF ID**: `Wan-AI/Wan2.2-T2V-A14B-Diffusers`
- **Parameters**: 14B (active parameters vary by MoE routing)
- **Min VRAM**: 48 GB
- **Recommended**: tensor_parallel_size >= 2

```bash
vllm serve Wan-AI/Wan2.2-T2V-A14B-Diffusers --omni \
  --tensor-parallel-size 2 --port 8091
```

### Wan2.2-TI2V-5B (Text+Image-to-Video)

- **HF ID**: `Wan-AI/Wan2.2-TI2V-5B-Diffusers`
- **Parameters**: 5B
- **Min VRAM**: 24 GB

Takes both a text prompt and a reference image to generate video that starts from or is guided by the image.

```bash
vllm serve Wan-AI/Wan2.2-TI2V-5B-Diffusers --omni --port 8091
```

### Wan2.2-I2V-A14B (Image-to-Video)

- **HF ID**: `Wan-AI/Wan2.2-I2V-A14B-Diffusers`
- **Parameters**: 14B
- **Min VRAM**: 48 GB

Animates a static image into a video clip.

```bash
vllm serve Wan-AI/Wan2.2-I2V-A14B-Diffusers --omni \
  --tensor-parallel-size 2 --port 8091
```

## Stage Configuration

Default stage configs work well for most use cases. For custom settings:

```yaml
stages:
  - name: "video_diffusion"
    stage_type: "diffusion"
    stage_args:
      runtime:
        max_batch_size: 1
```

Video models generally do not benefit from batching due to high memory requirements per sample.

## Prompt Engineering

Effective video prompts describe:
1. The subject and action
2. The camera movement (optional)
3. The mood or style

Examples:
- "A cat jumping from a table, slow motion, cinematic lighting"
- "Aerial drone shot of a winding river through a forest, golden hour"
- "Close-up of rain drops falling on a window, bokeh background"
- "Time-lapse of clouds moving over a mountain range"

## Performance Optimization

- Enable TeaCache for 1.5-2x speedup
- Use sequence parallelism for faster denoising
- CPU offloading helps fit 14B models on smaller GPUs
