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
| `response_format` | string | No | Audio format (wav, mp3, opus) |
| `stream_format` | string | No | `"audio"` for raw PCM byte streaming, `"sse"` for OpenAI `speech.audio.*` SSE events. Omit for non-streaming. |
| `stream` | bool | No | Legacy switch; equivalent to `stream_format="audio"`. |

### SSE Streaming (`stream_format="sse"`)

Set `stream_format="sse"` (omit `stream`) to receive OpenAI-compatible SSE events:

- `speech.audio.delta` — base64-encoded audio chunk
- `speech.audio.done` — terminal event with `usage` object
- `speech.audio.error` — emitted on generation failure instead of `speech.audio.done`

Requires `response_format="pcm"` or `"wav"`. Speed adjustment is not supported when streaming.

### WebSocket Streaming (`/v1/audio/speech/stream`)

Send text incrementally; audio is generated once when `input.done` is received:

| Message | Direction | Description |
|---------|-----------|-------------|
| `{"type": "session.config", ...}` | Client→Server | Configure voice, format |
| `{"type": "input.text", "text": "..."}` | Client→Server | Append text chunk |
| `{"type": "input.done"}` | Client→Server | Signal end of input; triggers generation |
| `{"type": "audio.start", ...}` | Server→Client | Audio generation starting |
| Binary frame(s) | Server→Client | PCM audio chunks |
| `{"type": "audio.done", ...}` | Server→Client | Audio complete |
| `{"type": "session.done", "total_sentences": N}` | Server→Client | Session complete |

All text is buffered and synthesized as a single request (no sentence-splitting). `total_sentences` is 1 (or 0 for empty input).

### POST /v1/audio/speech/batch

Generates multiple speech items in one request. Each successful item includes a `usage` object:

```json
{
  "index": 0,
  "status": "success",
  "audio_data": "<base64>",
  "media_type": "audio/wav",
  "usage": {
    "input_tokens": 119,
    "output_tokens": 77,
    "total_tokens": 196,
    "input_token_details": {"text_tokens": 18, "audio_tokens": 101}
  }
}
```

- `input_tokens` = `text_tokens` + `audio_tokens` (reference-audio frames; zero for non-ICL tasks)
- `output_tokens` = generated codec tokens

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
