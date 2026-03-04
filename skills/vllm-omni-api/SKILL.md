---
name: vllm-omni-api
description: Integrate with vLLM-Omni using the OpenAI-compatible API for text, image, video, and audio generation. Use when building client applications, calling vllm-omni endpoints, sending requests to the API server, or integrating vllm-omni into an application.
---

# vLLM-Omni API Integration

## Overview

vLLM-Omni exposes OpenAI-compatible REST endpoints for all modalities. Existing OpenAI client libraries work with minimal changes. The server supports chat completions, image generation, image editing, and speech synthesis.

## Starting the Server

```bash
vllm serve <model-name> --omni --port 8091
```

## Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/chat/completions` | POST | Chat-based generation (text, image, audio) |
| `/v1/images/generations` | POST | Direct image generation |
| `/v1/audio/speech` | POST | Text-to-speech |
| `/health` | GET | Server health check |
| `/v1/models` | GET | List loaded models |

## Chat Completions (Universal)

The chat completions endpoint handles all modalities through the message format:

### Python (openai SDK)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8091/v1", api_key="unused")

response = client.chat.completions.create(
    model="Tongyi-MAI/Z-Image-Turbo",
    messages=[{"role": "user", "content": "a sunset over mountains"}],
    extra_body={
        "height": 1024,
        "width": 1024,
        "num_inference_steps": 50,
        "guidance_scale": 4.0,
        "seed": 42,
    },
)

image_b64 = response.choices[0].message.content[0].image_url.url
```

### curl

```bash
curl -s http://localhost:8091/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "a sunset over mountains"}],
    "extra_body": {
      "height": 1024,
      "width": 1024,
      "num_inference_steps": 50,
      "guidance_scale": 4.0,
      "seed": 42
    }
  }' | jq -r '.choices[0].message.content[0].image_url.url' \
     | cut -d',' -f2 | base64 -d > sunset.png
```

## Image Generation Endpoint

```bash
curl -s http://localhost:8091/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a cup of coffee on a table",
    "size": "1024x1024",
    "n": 1
  }' | jq '.data[0].url'
```

## Streaming Responses

For models supporting streaming (text/audio outputs):

```python
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B",
    messages=[{"role": "user", "content": "Tell me about AI"}],
    stream=True,
)
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Multi-modal Input

Send images/audio as input to omni-modality models:

```python
import base64

with open("photo.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Omni-7B",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": "Describe this image"},
        ],
    }],
)
```

## Error Handling

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad request | Check request body format |
| 404 | Model not found | Verify model name and server config |
| 413 | Input too large | Reduce input size or increase limits |
| 500 | Server error | Check server logs |
| 503 | Server overloaded | Retry with backoff |

## Health Check

```python
import requests

resp = requests.get("http://localhost:8091/health")
assert resp.status_code == 200
```

## References

- For full endpoint specifications and parameters, see [references/endpoints.md](references/endpoints.md)


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation](https://github.com/vllm-project/vllm-omni/pull/1609)

### Changes
- Bug fix: [Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Import InputPreprocessor into Renderer](https://github.com/vllm-project/vllm-omni/pull/1566)

### Changes
- Bug fix: [Bugfix] Import InputPreprocessor into Renderer

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Fix unexpected crash when init OmniDiffusion](https://github.com/vllm-project/vllm-omni/pull/1562)

### Changes
- Bug fix: [BugFix] Fix unexpected crash when init OmniDiffusion

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [fix(qwen3-tts): fix Base ICL voice clone producing corrupted audio](https://github.com/vllm-project/vllm-omni/pull/1554)

### Changes
- Bug fix: fix(qwen3-tts): fix Base ICL voice clone producing corrupted audio

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Use uds for zmq address if not set --stage-id](https://github.com/vllm-project/vllm-omni/pull/1522)

### Changes
- New feature: [Bugfix] Use uds for zmq address if not set --stage-id

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Chore] remove unused logger in omni_diffusion (#531)](https://github.com/vllm-project/vllm-omni/pull/1509)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Feature][Wan2.2] Speed up diffusion model startup by multi-thread weight loading](https://github.com/vllm-project/vllm-omni/pull/1504)

### Changes
- New feature: [Feature][Wan2.2] Speed up diffusion model startup by multi-thread weight loading

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Qwen3TTS][Feat] Streaming output](https://github.com/vllm-project/vllm-omni/pull/1438)

### Changes
- New feature: [Qwen3TTS][Feat] Streaming output

*Updated: 2026-03-04*
