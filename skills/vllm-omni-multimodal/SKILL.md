---
name: vllm-omni-multimodal
description: Use end-to-end omni-modality models like Qwen2.5-Omni and Qwen3-Omni for combined text, image, audio, and video understanding and generation. Use when working with omni-modality models that handle multiple input and output types simultaneously.
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

## Multi-Modal Input Patterns

### Image Understanding

```python
import base64
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8091/v1", api_key="unused")

with open("photo.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

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

### Audio Understanding

```python
with open("recording.wav", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode()

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
with open("clip.mp4", "rb") as f:
    video_b64 = base64.b64encode(f.read()).decode()

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

Send multiple modalities in a single request:

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

## Audio Output

Omni models can generate audio responses alongside text:

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

## Troubleshooting

**Slow with video input**: Video processing requires extracting and encoding frames. Shorter clips process faster.

**Audio output garbled**: Ensure the client correctly handles the audio response format (base64 encoded WAV).

**Out of memory with multi-modal input**: Large images/videos consume significant memory. Resize inputs before sending.

## References

- For Qwen-Omni architecture and advanced config, see [references/qwen-omni.md](references/qwen-omni.md)
