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

OmniVoice supports voice cloning via `ref_audio` + `ref_text` (requires transformers>=5.3). VoxCPM2 is a 2B tokenizer-free native AR TTS model producing 48kHz audio in 30+ languages (requires `pip install voxcpm`).

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

### High-Concurrency Profile

For high-concurrency TTS serving (voice cloning, c=64+), use `qwen3_tts_high_concurrency.yaml`:

```bash
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --omni \
  --stage-configs-path vllm_omni/deploy/qwen3_tts_high_concurrency.yaml
```

This profile enables batched CUDA graph decoder, prefix CUDA graphs for the code predictor, bounded reference-code context, and first-chunk fast emit (`initial_codec_chunk_frames: 1`). Tuned for 2-GPU serving with Seed-TTS voice-clone workload. Median TTFP is higher than default profile; use for throughput/E2E rather than first-packet-latency optimization.

Additional high-concurrency knobs available in the deploy config:
- `decode_cudagraph_batch_sizes`: Multi-batch-size CUDA graph capture for Code2Wav
- `decode_batch_bucket_frames` / `decode_batch_max_size`: Variable-length chunk batching
- `ref_code_context_frames`: Limits reference-audio code frames per chunk for stable stage-1 shapes
- `decode_enable_tf32: true`: Opt-in TF32 for Code2Wav
- `code_predictor_prefix_graphs: true`: Prefix CUDA graph warmup for Stage0 code predictor

For batch mode (no streaming), use `qwen3_tts_batch.yaml`.

Fish Speech uses `fish_speech_s2_pro.yaml` with similar knobs. Its DAC codec outputs at 44.1 kHz (vs Qwen3-TTS's 24 kHz).

Note: CosyVoice3 does not support async_chunk streaming yet - use `cosyvoice3.yaml` (batch mode only).

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

## References

- For Qwen3-TTS details and voice options, see [references/qwen-tts.md](references/qwen-tts.md)
- For Fish Speech S2 Pro details, see [references/fish-speech.md](references/fish-speech.md)
- For CosyVoice3 details, see [references/cosyvoice3.md](references/cosyvoice3.md)
- For MiMo-Audio capabilities, see [references/mimo-audio.md](references/mimo-audio.md)
