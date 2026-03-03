# API Endpoint Reference

## POST /v1/chat/completions

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | No | Model name (uses server default if omitted) |
| `messages` | array | Yes | Array of message objects |
| `stream` | boolean | No | Enable streaming (default: false) |
| `temperature` | float | No | Sampling temperature |
| `max_tokens` | int | No | Maximum tokens to generate |
| `extra_body` | object | No | Model-specific parameters |

### extra_body Parameters (Diffusion Models)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `height` | int | Model default | Output image height in pixels |
| `width` | int | Model default | Output image width in pixels |
| `num_inference_steps` | int | Model default | Number of diffusion steps |
| `guidance_scale` | float | Model default | Classifier-free guidance scale |
| `seed` | int | Random | Random seed for reproducibility |
| `negative_prompt` | string | None | Negative prompt for guided generation |

### extra_body Parameters (TTS Models)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `voice` | string | Model default | Voice identifier or reference audio |
| `speed` | float | 1.0 | Speech speed multiplier |
| `response_format` | string | "wav" | Audio format (wav, mp3, opus) |

### Message Object

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | "system", "user", or "assistant" |
| `content` | string or array | Text string or array of content parts |

### Content Part Types

| Type | Fields | Purpose |
|------|--------|---------|
| `text` | `text` | Text input |
| `image_url` | `image_url.url` | Image input (URL or base64 data URI) |
| `audio_url` | `audio_url.url` | Audio input (URL or base64 data URI) |
| `video_url` | `video_url.url` | Video input (URL or base64 data URI) |

## POST /v1/images/generations

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | Text description of desired image |
| `n` | int | No | Number of images (default: 1) |
| `size` | string | No | Image size "WxH" (e.g., "1024x1024") |
| `response_format` | string | No | "url" or "b64_json" |

## POST /v1/audio/speech

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | TTS model name |
| `input` | string | Yes | Text to synthesize |
| `voice` | string | No | Voice preset or reference |
| `speed` | float | No | Speed multiplier |
| `response_format` | string | No | Audio format |

## GET /v1/models

Returns list of currently loaded models.

### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "Tongyi-MAI/Z-Image-Turbo",
      "object": "model",
      "owned_by": "vllm"
    }
  ]
}
```

## GET /health

Returns 200 if server is ready. Use for load balancer health checks and readiness probes.
