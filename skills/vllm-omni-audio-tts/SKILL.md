---
name: vllm-omni-audio-tts
description: Generate audio and speech with vLLM-Omni using Qwen3-TTS, Fish Speech S2 Pro, CosyVoice3, MiMo-Audio, and Stable-Audio models. Use when synthesizing speech from text, generating audio effects or music, configuring TTS parameters, cloning voices, adding new TTS models, or working with text-to-speech models.
---

# vLLM-Omni Audio & TTS

## Overview

vLLM-Omni supports text-to-speech (TTS), text-to-audio (sound effects, music), and audio understanding through multiple model families. TTS models use a two-stage autoregressive pipeline (Code Predictor + Code2Wav decoder), while audio generation uses diffusion.

## Supported Audio Models

| Model | HF ID | Type | Min VRAM |
|-------|-------|------|----------|
| Qwen3-TTS 1.7B CustomVoice | `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | TTS + voice cloning | 8 GB |
| Qwen3-TTS 1.7B VoiceDesign | `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` | TTS + voice design | 8 GB |
| Qwen3-TTS 1.7B Base | `Qwen/Qwen3-TTS-12Hz-1.7B-Base` | Basic TTS | 8 GB |
| Qwen3-TTS 0.6B CustomVoice | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | TTS + voice cloning | 4 GB |
| Qwen3-TTS 0.6B Base | `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | Basic TTS | 4 GB |
| Fish Speech S2 Pro | `fishaudio/s2-pro` | TTS + voice cloning (dual-AR + DAC) | 16 GB |
| CosyVoice3 0.5B | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` | TTS (AR + flow matching) | 4 GB |
| MiMo-Audio-7B | `XiaomiMiMo/MiMo-Audio-7B-Instruct` | Audio understanding + TTS | 24 GB |
| MiMo-V2.5-ASR | `XiaomiMiMo/MiMo-V2.5-ASR` | ASR (speech-to-text) | 24 GB |
| OmniVoice | `nvidia/OmniVoice` | TTS + voice cloning (HiggsAudioV2) | 8 GB |
| VoxCPM2 | `openbmb/VoxCPM2` | TTS (native AR, 30+ languages) | 8 GB |
| Stable-Audio-Open | `stabilityai/stable-audio-open-1.0` | Text-to-audio (music/effects) | 8 GB |

OmniVoice supports voice cloning via `ref_audio` + `ref_text` (requires transformers>=5.3). OmniVoice/Higgs Audio v3 ships two deploy profiles: `higgs_multimodal_qwen3.yaml` (high-throughput default) and `higgs_multimodal_qwen3_low_latency.yaml` (CUDA-graph accelerated for concurrency 1-4). Use `--deploy-config` to select. VoxCPM2 is a 2B tokenizer-free native AR TTS model producing 48kHz audio in 30+ languages (requires `pip install voxcpm`).

## Model Architectures

Both Qwen3-TTS and CosyVoice3 use a two-stage autoregressive pipeline. See the reference docs for architecture details, key files, and model variants:

- [Qwen3-TTS architecture and variants](references/qwen-tts.md)
- [Fish Speech S2 Pro architecture and setup](references/fish-speech.md)
- [CosyVoice3 architecture and setup](references/cosyvoice3.md)

## Quick Start: Text-to-Speech

### Offline

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
outputs = omni.generate("Hello, welcome to vLLM-Omni!")
audio = outputs[0].request_output[0].audio
audio.save("greeting.wav")
```

### Online API

```bash
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --omni --port 8091

curl -s http://localhost:8091/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "input": "Hello, welcome to vLLM-Omni!",
    "voice": "default"
  }' --output greeting.wav
```

## Voice Cloning (CustomVoice variants)

Clone a voice from a reference audio sample:

```python
omni = Omni(model="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
outputs = omni.generate(
    prompt="This is a test of voice cloning with vLLM-Omni.",
    audio_references=["reference_voice.wav"],
)
outputs[0].request_output[0].audio.save("cloned_speech.wav")
```

## Voice Design (VoiceDesign variant)

Design a voice by describing its characteristics:

```python
omni = Omni(model="Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign")
outputs = omni.generate(
    prompt="Welcome to our product launch event!",
    voice_description="A warm, professional female voice with a calm tone",
)
outputs[0].request_output[0].audio.save("designed_voice.wav")
```

## Text-to-Audio (Music & Effects)

Generate music or sound effects with Stable-Audio-Open:

```bash
vllm serve stabilityai/stable-audio-open-1.0 --omni --port 8091
```

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8091/v1", api_key="unused")

response = client.chat.completions.create(
    model="stabilityai/stable-audio-open-1.0",
    messages=[{"role": "user", "content": "Relaxing piano music with rain sounds"}],
)
```

## Audio Understanding (MiMo-Audio)

MiMo-Audio can both understand audio input and generate speech:

```python
omni = Omni(model="XiaomiMiMo/MiMo-Audio-7B-Instruct")

# Transcribe/understand audio
outputs = omni.generate(
    prompt="What is being said in this audio?",
    audio_inputs=["recording.wav"],
)
print(outputs[0].request_output[0].text)
```

## Stage Configuration (Qwen3-TTS)

`async_scheduling` is **enabled by default** for Qwen3-TTS models, improving first-packet latency and throughput.

Default stage config uses async_chunk streaming (`qwen3_tts.yaml`). Key knobs:

| Config | Description | Default |
|--------|-------------|---------|
| `async_chunk` | Enable inter-stage streaming | `true` |
| `runtime.max_batch_size` | Max requests batched per stage | `1` |
| `enforce_eager` | Disable CUDA Graph (Stage 0: false, Stage 1: true) | varies |
| `codec_chunk_frames` | AR frames per async chunk (inter-stage streaming only) | `25` |
| `codec_left_context_frames` | Sliding context window for smooth boundaries | `25` |
| `initial_codec_chunk_frames` | Frames for first emitted codec chunk only (lowers TTFA) | `0` |
| `decode_chunk_frames` | Code2Wav internal decode chunk size (independent of codec streaming) | `300` |
| `decode_left_context_frames` | Code2Wav internal left context for decode | `25` |

Connector streaming chunking (`codec_chunk_frames` / `codec_left_context_frames`) is **decoupled** from Code2Wav internal decode chunking (`decode_chunk_frames` / `decode_left_context_frames`). The connector controls inter-stage streaming windows only, while Code2Wav keeps its own independent decode parameters. Use `initial_codec_chunk_frames` to emit a small first chunk for low TTFA, then subsequent chunks return to the normal `codec_chunk_frames` window.

The uniproc Code2Wav stage default `max_num_seqs` is now `10` (was `1`). Avoid reducing below 10 for latency-sensitive deployments.

CUDA Graph warmup for Qwen3-TTS now accounts for custom `decode_chunk_frames` / `decode_left_context_frames` overrides.

For batch mode (no streaming), use `qwen3_tts_batch.yaml`.

Fish Speech uses `fish_speech_s2_pro.yaml` with similar knobs. Its DAC codec outputs at 44.1 kHz (vs Qwen3-TTS's 24 kHz).

MOSS-TTS codec decoder supports CUDA Graph acceleration when `enforce_eager: false` in the stage config. Capture sizes are configured via `decode_cudagraph_capture_sizes` in the connector's `extra` config (default: `[4, 8, 16, 25, 32, 50, 64, 100, 128, 200, 256]`). Inputs are bucket-matched to the smallest pre-captured size, replaying the graph with right zero-padding.

Note: CosyVoice3 does not support async_chunk streaming yet - use `cosyvoice3.yaml` (batch mode only).

CosyVoice3 supports optional TensorRT acceleration (`COSYVOICE3_TRT=1`, default on) for the campplus speaker embedding and flow-decoder estimator engines. Requires TensorRT >= 10. Disable with `COSYVOICE3_TRT=0` if TensorRT is unavailable. When enabled, TTFP improves significantly (e.g., ~2800ms → ~200ms at concurrency=1 on H100).

## Qwen3-TTS `non_streaming_mode`

The `non_streaming_mode` parameter (bool | null) overrides the model's streaming-mode prompt construction for Qwen3-TTS. It does NOT affect HTTP/WebSocket response streaming or async-chunk pipelining.

- **`null` (default)**: VoiceDesign defaults to `true`; Base and CustomVoice use model defaults.
- **`true`**: Force non-streaming prompt construction for any task type (useful for Base models where streaming-mode prompts may degrade quality).
- **`false`**: Force streaming-mode prompt construction.

Accepted by `/v1/audio/speech`, `/v1/audio/speech/batch`, and WebSocket session config. Example:

```bash
curl -s http://localhost:8091/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    "input": "Hello world",
    "non_streaming_mode": true
  }' --output speech.wav
```

## Streaming Audio

For real-time TTS streaming:

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    messages=[{"role": "user", "content": "A long paragraph of text to stream..."}],
    stream=True,
)
```

## Adding a New TTS Model

For a step-by-step guide on integrating a new TTS model into vLLM-Omni, see the [TTS model developer guide](https://github.com/vllm-project/vllm-omni/blob/main/docs/contributing/model/adding_tts_model.md). Offline examples are consolidated under `examples/offline_inference/text_to_speech/<model>/end2end.py`, and online serving examples under `examples/online_serving/text_to_speech/<model>/`.

## Troubleshooting

**Audio quality issues**: Ensure reference audio for voice cloning is clean (no background noise), 10-20 seconds, single speaker.

**Qwen3-TTS code predictor crash**: Fixed in #1619. If you encounter a crash in the code predictor stage, update to the latest vllm-omni.

**Qwen3-TTS NaN on fp16-only GPUs**: The code predictor auto-upcasts to float32 for numerical stability on GPUs without bf16 support (Turing, Volta). No manual override needed. Fixed in #3253.

**Qwen3-TTS speaker_embedding dimension error**: Speaker embedding dimensions must match the model's talker hidden_size (2048 for 1.7B, 1024 for 0.6B). Mismatched dimensions return HTTP 400. Fixed in #3191.

**Qwen3-TTS load_format: dummy**: `speaker_encoder` is always constructed at init time. Voice cloning works under `load_format: dummy` without extra configuration. Fixed in #3117.

**Slow generation**: TTS models are autoregressive - generation time scales with output duration. Enable async_chunk for lower first-packet latency. For throughput, increase `max_batch_size`.

**Fish Speech voice cloning latency**: Uploaded voices via `/v1/audio/voice/upload` now auto-cache DAC-encoded reference audio. First request encodes the reference; subsequent requests reuse the cached codes for faster TTFP. Fixed in #2609.

**Event loop blocking under concurrent TTS**: Blocking tokenizer operations (`_build_voxtral_prompt`, `_build_fish_speech_prompt`) now run in a shared `ThreadPoolExecutor(max_workers=1)`. This prevents `/health` latency spikes under concurrent load. Fixed in #2511.

**Qwen3-TTS voice corruption at concurrency > 1**: Cross-request reference codec frame leakage caused audible timbre deformation in batched voice-clone requests. Fixed in #4373. Ensure per-request multimodal output payloads use batch-aligned lists (one entry per request).

## References

- For Qwen3-TTS details and voice options, see [references/qwen-tts.md](references/qwen-tts.md)
- For Fish Speech S2 Pro details, see [references/fish-speech.md](references/fish-speech.md)
- For CosyVoice3 details, see [references/cosyvoice3.md](references/cosyvoice3.md)
- For MiMo-Audio capabilities, see [references/mimo-audio.md](references/mimo-audio.md)
