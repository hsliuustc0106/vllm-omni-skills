---
name: vllm-omni-audio-tts
description: Generate audio and speech with vLLM-Omni using Qwen3-TTS, CosyVoice3, MiMo-Audio, and Stable-Audio models. Use when synthesizing speech from text, generating audio effects or music, configuring TTS parameters, cloning voices, adding new TTS models, or working with text-to-speech models.
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
| CosyVoice3 0.5B | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` | TTS (AR + flow matching) | 4 GB |
| MiMo-Audio-7B | `XiaomiMiMo/MiMo-Audio-7B-Instruct` | Audio understanding + TTS | 24 GB |
| Stable-Audio-Open | `stabilityai/stable-audio-open-1.0` | Text-to-audio (music/effects) | 8 GB |

## Qwen3-TTS Architecture

Qwen3-TTS runs as a two-stage pipeline:

| Stage | Class | Role |
|-------|-------|------|
| 0 - Code Predictor (AR) | `Qwen3TTSTalkerForConditionalGeneration` | Text tokens -> discrete RVQ codec codes |
| 1 - Code2Wav (Decoder) | `Qwen3TTSCode2Wav` | Codec codes -> audio waveform |

Stage 0 uses vLLM's native `Qwen3DecoderLayer` with fused QKV and PagedAttention. Stage 1 wraps the HF SpeechTokenizer.

With `async_chunk: true`, Stage 0 streams codec codes to Stage 1 every 25 frames instead of waiting for completion, reducing first-packet latency.

Key files:
- `vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code_predictor_vllm.py` - AR stage
- `vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code2wav.py` - Decoder stage
- `vllm_omni/model_executor/stage_configs/qwen3_tts.yaml` - Stage config (async_chunk)
- `vllm_omni/model_executor/stage_configs/qwen3_tts_batch.yaml` - Batch mode config
- `vllm_omni/model_executor/stage_input_processors/qwen3_tts.py` - Stage transition

## CosyVoice3 Architecture

CosyVoice3 also runs as a two-stage pipeline but uses flow matching instead of a codec decoder:

| Stage | Class | Role |
|-------|-------|------|
| 0 - Talker (AR) | `CosyVoice3Model` | Text -> speech tokens |
| 1 - Code2Wav (Flow Matching + HiFiGAN) | `CosyVoice3Model` | Speech tokens -> waveform via CFM + vocoder |

CosyVoice3 does not support async_chunk - Stage 0 runs to completion before Stage 1 starts (batch mode only).

Key files:
- `vllm_omni/model_executor/models/cosyvoice3/cosyvoice3.py` - Unified model class
- `vllm_omni/model_executor/models/cosyvoice3/cosyvoice3_talker.py` - AR stage
- `vllm_omni/model_executor/models/cosyvoice3/cosyvoice3_code2wav.py` - Flow matching decoder
- `vllm_omni/model_executor/stage_configs/cosyvoice3.yaml` - Stage config
- `vllm_omni/model_executor/stage_input_processors/cosyvoice3.py` - Stage transition

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

## Stage Configuration

Default stage config uses async_chunk streaming (`qwen3_tts.yaml`). Key knobs:

| Config | Description | Default |
|--------|-------------|---------|
| `async_chunk` | Enable inter-stage streaming | `true` |
| `runtime.max_batch_size` | Max requests batched per stage | `1` |
| `enforce_eager` | Disable CUDA Graph (Stage 0: false, Stage 1: true) | varies |
| `codec_chunk_frames` | AR frames per async chunk | `25` |
| `codec_left_context_frames` | Sliding context window for smooth boundaries | `25` |

For batch mode (no streaming), use `qwen3_tts_batch.yaml`.

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

For a step-by-step guide on integrating a new TTS model into vLLM-Omni, see the [TTS model developer guide](https://github.com/vllm-project/vllm-omni/blob/main/docs/contributing/model/adding_tts_model.md).

## Troubleshooting

**Audio quality issues**: Ensure reference audio for voice cloning is clean (no background noise), 10-20 seconds, single speaker.

**Slow generation**: TTS models are autoregressive - generation time scales with output duration. Enable async_chunk for lower first-packet latency. For throughput, increase `max_batch_size`.

## References

- For Qwen3-TTS details and voice options, see [references/qwen-tts.md](references/qwen-tts.md)
- For CosyVoice3 details, see [references/cosyvoice3.md](references/cosyvoice3.md)
- For MiMo-Audio capabilities, see [references/mimo-audio.md](references/mimo-audio.md)
