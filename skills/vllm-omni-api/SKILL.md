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

**Source**: [Revert "[Profile] Adding metrics for Diffusion/DiT Single diffusion Pipeline (#668)"](https://github.com/vllm-project/vllm-omni/pull/1724)

### Changes
- New feature: Revert "[Profile] Adding metrics for Diffusion/DiT Single diffusion Pipeline (#668)"

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[Feature]:  Add vae-patch-parallel CLI argument in online serving](https://github.com/vllm-project/vllm-omni/pull/1716)

### Changes
- New feature: [Feature]:  Add vae-patch-parallel CLI argument in online serving

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[BugFix] Return proper HTTP status for ErrorResponse in create_speech](https://github.com/vllm-project/vllm-omni/pull/1687)

### Changes
- Bug fix: [BugFix] Return proper HTTP status for ErrorResponse in create_speech

### New Features
- `/v1/audio/speech`

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Add TTS request validation to prevent engine crashes](https://github.com/vllm-project/vllm-omni/pull/1641)

### Changes
- New feature: [Bugfix] Add TTS request validation to prevent engine crashes

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation](https://github.com/vllm-project/vllm-omni/pull/1609)

### Changes
- Bug fix: [Bugfix] Fix filepath resolution for model with subdir and GLM-Image generation

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[Feat][Qwen3TTS] reduce TTFA with flexible initial phase](https://github.com/vllm-project/vllm-omni/pull/1583)

### Changes
- New feature: [Feat][Qwen3TTS] reduce TTFA with flexible initial phase

*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[1/N][Refactor] Clean up dead code in output processor](https://github.com/vllm-project/vllm-omni/pull/1579)


*Updated: 2026-03-08*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Import InputPreprocessor into Renderer](https://github.com/vllm-project/vllm-omni/pull/1566)

### Changes
- Bug fix: [Bugfix] Import InputPreprocessor into Renderer

*Updated: 2026-03-08*
