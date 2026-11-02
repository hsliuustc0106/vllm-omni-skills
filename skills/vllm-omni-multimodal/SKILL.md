---
name: vllm-omni-multimodal
description: "Transcribe speech, generate images from prompts, analyze video content, and convert between modalities using multimodal omni-modality models like Qwen2.5-Omni and Qwen3-Omni. Use when working with multimodal models for speech recognition, image generation, video understanding, voice synthesis, or any task combining text, image, audio, and video inputs and outputs simultaneously."
---

# vLLM-Omni Multimodal (Omni-Modality Models)

## Overview

Omni-modality models accept multiple input types (text, image, audio, video) and produce multiple output types (text, audio) in a single model. vLLM-Omni currently supports the Qwen-Omni family for this capability.

## Supported Omni Models

| Model | HF ID | Inputs | Outputs | Min VRAM |
|-------|-------|--------|---------|----------|
| Qwen2.5-Omni-7B | `Qwen/Qwen2.5-Omni-7B` | Text, image, audio, video | Text, audio | 24 GB |
| Qwen2.5-Omni-3B | `Qwen/Qwen2.5-Omni-3B` | Text, image, audio, video | Text, audio | 12 GB |
| Qwen3-Omni-30B-A3B | `Qwen/Qwen3-Omni-30B-A3B-Instruct` | Text, image, audio, video | Text, audio | 48 GB |

## Quick Start

### Offline: Text Conversation

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Qwen/Qwen2.5-Omni-7B")
outputs = omni.generate("What is the capital of France?")
print(outputs[0].request_output[0].text)
```

### Online: Start Server

```bash
vllm serve Qwen/Qwen2.5-Omni-7B --omni --port 8091
```

## Input Validation Workflow

Validate media inputs before sending to avoid OOM errors and processing failures:

```python
import os
import base64
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8091/v1", api_key="unused")

MAX_IMAGE_MB = 20
MAX_AUDIO_MB = 50
MAX_VIDEO_MB = 100
SUPPORTED_IMAGE = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_AUDIO = {".wav", ".mp3", ".flac"}
SUPPORTED_VIDEO = {".mp4", ".webm"}

def validate_and_encode(path: str, max_mb: float, supported_exts: set) -> str:
    ext = os.path.splitext(path)[1].lower()
    assert ext in supported_exts, f"Unsupported format: {ext}"
    size_mb = os.path.getsize(path) / (1024 * 1024)
    assert size_mb <= max_mb, f"File too large: {size_mb:.1f}MB > {max_mb}MB"
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
```

## Multi-Modal Input Patterns

### Image Understanding

```python
img_b64 = validate_and_encode("photo.jpg", MAX_IMAGE_MB, SUPPORTED_IMAGE)
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": "What do you see in this image?"},
        ],
    }],
)
print(response.choices[0].message.content)
```

### Audio Understanding (Speech-to-Text)

```python
audio_b64 = validate_and_encode("recording.wav", MAX_AUDIO_MB, SUPPORTED_AUDIO)
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B",
    messages=[{
        "role": "user",
        "content": [
            {"type": "audio_url", "audio_url": {"url": f"data:audio/wav;base64,{audio_b64}"}},
            {"type": "text", "text": "Transcribe this audio."},
        ],
    }],
)
```

### Video Understanding

```python
video_b64 = validate_and_encode("clip.mp4", MAX_VIDEO_MB, SUPPORTED_VIDEO)
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B",
    messages=[{
        "role": "user",
        "content": [
            {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{video_b64}"}},
            {"type": "text", "text": "Describe what happens in this video."},
        ],
    }],
)
```

### Combined Inputs

```python
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "audio_url", "audio_url": {"url": f"data:audio/wav;base64,{audio_b64}"}},
            {"type": "text", "text": "Does the audio describe what's in the image?"},
        ],
    }],
)
```

## Audio Output (Voice Synthesis)

```python
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B",
    messages=[{"role": "user", "content": "Say hello in English and Chinese."}],
    extra_body={"output_modalities": ["text", "audio"]},
)
```

## Multi-Turn Conversations

```python
messages = [
    {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
        {"type": "text", "text": "What's in this image?"},
    ]},
]
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B", messages=messages
)
messages.append({"role": "assistant", "content": response.choices[0].message.content})
messages.append({"role": "user", "content": "What colors are dominant?"})
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B", messages=messages
)
```

## Qwen3-Omni (MoE)

Qwen3-Omni uses a Mixture-of-Experts architecture (30B total, 3B active). Requires multi-GPU:

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni \
  --tensor-parallel-size 2 --port 8091
```

Qwen3-Omni is compatible with the v2 model runner (vllm 0.19). Uses native `launch_core_engines` instead of custom spawning. `add_streaming_update` API removed; audio output tensors are explicitly converted to float. CUDAGraph supports tuple-returning thinker model. Fixed in #2522.

The Qwen3-Omni thinker supports an opt-in `hf_numerics` mode that makes RMSNorm, residual/deepstack adds, rotary embedding, and MoE routing bitwise-match the `transformers` implementation so an HF trainer can recompute rollout log-probs exactly for on-policy RL. Enable with `engine_extras.additional_config.hf_numerics: true` on stage 0, combined with `VLLM_BATCH_INVARIANT=1`, `tensor_parallel_size: 1`, no expert parallelism, and `moe_backend: triton` (set `--moe-backend triton` when `auto` would pick FlashInfer); only the default rope type and unquantized MoE decoder layers are supported. Keep it off for serving — the replaced ops are unfused eager PyTorch.

`cudagraph_mm_encoder: true` now also captures the thinker's audio encoder (image path unchanged; video stays eager), replaying clips of 13–104 tokens (up to ~8 s) from CUDA graphs. Audio graphs are CUDA-only and stay eager with model runner v2, `mm_encoder_tp_mode: data`, or when no listed budget reaches 13 tokens; disable just audio with `additional_config.audio_encoder_cudagraph: false`. Audio budgets round down to whole 13-token chunks and cap at 104 tokens; larger budgets inflate the audio graph pool (~88 MiB → ~270 MiB at 208/256 tokens), deducted from the thinker KV cache.

## Troubleshooting

**Slow with video input**: Video processing requires extracting and encoding frames. Shorter clips process faster.

**Audio output garbled**: Ensure the client correctly handles the audio response format (base64 encoded WAV).

**Out of memory with multi-modal input**: Large images/videos consume significant memory. Use the validation workflow above to check file sizes before sending.

**Qwen3-Omni performance**: The multi-stage pipeline optimizes CPU hidden-state copying — only copies to CPU when downstream stages need payloads. Text-only inference (without `--omni`) is supported for benchmarking via `use_omni: false`. Fixed in #3203.

## References

- For Qwen-Omni architecture and advanced config, see [references/qwen-omni.md](references/qwen-omni.md)
