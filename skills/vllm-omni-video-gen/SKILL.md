---
name: vllm-omni-video-gen
description: Generate videos with vLLM-Omni using Wan2.2 and other video generation models. Use when generating videos from text, creating videos from images, configuring video generation parameters, or working with text-to-video or image-to-video models.
---

# vLLM-Omni Video Generation

## Overview

vLLM-Omni supports video generation through diffusion transformer models, primarily the Wan2.2 family. Three modes are supported: text-to-video (T2V), image-to-video (I2V), and text+image-to-video (TI2V).

## Supported Video Models

| Model | HF ID | Mode | Min VRAM |
|-------|-------|------|----------|
| Wan2.2-T2V-A14B | `Wan-AI/Wan2.2-T2V-A14B-Diffusers` | Text-to-video | 48 GB |
| Wan2.2-TI2V-5B | `Wan-AI/Wan2.2-TI2V-5B-Diffusers` | Text+Image-to-video | 24 GB |
| Wan2.2-I2V-A14B | `Wan-AI/Wan2.2-I2V-A14B-Diffusers` | Image-to-video | 48 GB |
| NextStep-1.1 | `stepfun-ai/NextStep-1.1` | Text-to-video | 24 GB |
| daVinci-MagiHuman | `SII-GAIR/daVinci-MagiHuman-Base-1080p` | Image-to-video + audio | 24 GB |

daVinci-MagiHuman is an image-to-video model that also generates audio (44100 Hz, 25 fps). Use `--enable-diffusion-pipeline-profiler` to get per-stage timing (`stage_durations`) and peak memory (`peak_memory_mb`) in video responses (async poll JSON or sync HTTP headers).

## Quick Start: Text-to-Video

### Offline

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Wan-AI/Wan2.2-T2V-A14B-Diffusers")
outputs = omni.generate("A dog running on a beach at sunset")
video = outputs[0].request_output[0].video
video.save("dog_beach.mp4")
```

### Online API

```bash
vllm serve Wan-AI/Wan2.2-T2V-A14B-Diffusers --omni --port 8091

curl -s http://localhost:8091/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "A dog running on a beach at sunset"}],
    "extra_body": {
      "num_inference_steps": 50,
      "guidance_scale": 5.0,
      "seed": 42
    }
  }'
```

## Image-to-Video

Animate a static image into a video:

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Wan-AI/Wan2.2-I2V-A14B-Diffusers")
outputs = omni.generate(
    prompt="The person starts walking forward",
    images=["portrait.jpg"],
)
outputs[0].request_output[0].video.save("animated.mp4")
```

## Text+Image-to-Video (TI2V)

Combine a text description and reference image:

```python
omni = Omni(model="Wan-AI/Wan2.2-TI2V-5B-Diffusers")
outputs = omni.generate(
    prompt="The city lights up at night with moving traffic",
    images=["cityscape.jpg"],
)
outputs[0].request_output[0].video.save("city_night.mp4")
```

## Video Generation Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `num_inference_steps` | Denoising steps | 30-100 |
| `guidance_scale` | CFG scale | 3.0-7.0 |
| `seed` | Random seed | Any integer |
| `num_frames` | Number of output frames | Model-dependent |
| `fps` | Frames per second | 8-24 |

## Performance Considerations

Video generation is significantly more compute-intensive than image generation:

- A single video may take 2-10 minutes on a single GPU
- Multi-GPU tensor parallelism strongly recommended for 14B models
- Multi-thread weight loading (enabled by default) significantly reduces cold-start time for Wan2.2 models
- Enable TeaCache for diffusion acceleration (see vllm-omni-perf skill)
- CPU offloading can help fit larger models:
  ```bash
  vllm serve <model> --omni --cpu-offload-gb 20
  ```

## Troubleshooting

**Generation too slow**: Use tensor parallelism or enable TeaCache/Cache-DiT acceleration.

**Out of memory**: Reduce resolution/frame count or use CPU offloading.

**Choppy output**: Increase `num_inference_steps` and `num_frames`.

## References

- For Wan2.2 model details and advanced config, see [references/wan-models.md](references/wan-models.md)
