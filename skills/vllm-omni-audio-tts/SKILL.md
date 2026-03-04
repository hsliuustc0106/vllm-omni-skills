---
name: vllm-omni-audio-tts
description: Generate audio and speech with vLLM-Omni using Qwen3-TTS, MiMo-Audio, and Stable-Audio models. Use when synthesizing speech from text, generating audio effects or music, configuring TTS parameters, cloning voices, or working with text-to-speech models.
---

# vLLM-Omni Audio & TTS

## Overview

vLLM-Omni supports text-to-speech (TTS), text-to-audio (sound effects, music), and audio understanding through multiple model families. TTS models use autoregressive architectures while audio generation uses diffusion.

## Supported Audio Models

| Model | HF ID | Type | Min VRAM |
|-------|-------|------|----------|
| Qwen3-TTS CustomVoice | `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | TTS + voice cloning | 8 GB |
| Qwen3-TTS VoiceDesign | `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` | TTS + voice design | 8 GB |
| Qwen3-TTS Base | `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | Basic TTS | 4 GB |
| MiMo-Audio-7B | `XiaomiMiMo/MiMo-Audio-7B-Instruct` | Audio understanding + TTS | 24 GB |
| Stable-Audio-Open | `stabilityai/stable-audio-open-1.0` | Text-to-audio (music/effects) | 8 GB |

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

## Voice Cloning (Qwen3-TTS CustomVoice)

Clone a voice from a reference audio sample:

```python
omni = Omni(model="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
outputs = omni.generate(
    prompt="This is a test of voice cloning with vLLM-Omni.",
    audio_references=["reference_voice.wav"],
)
outputs[0].request_output[0].audio.save("cloned_speech.wav")
```

## Voice Design (Qwen3-TTS VoiceDesign)

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

## TTS Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `voice` | Voice ID or reference audio path | Model default |
| `speed` | Speech rate multiplier | 1.0 |
| `response_format` | Output format (wav, mp3, opus) | wav |

## Streaming Audio

For real-time TTS streaming:

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    messages=[{"role": "user", "content": "A long paragraph of text to stream..."}],
    stream=True,
)
```

## Troubleshooting

**Audio quality issues**: Use higher sample rate models (12Hz variants). Ensure reference audio for voice cloning is clean (no background noise).

**Slow generation**: TTS models are autoregressive -- generation time scales with output duration. For long texts, consider splitting into segments.

## References

- For Qwen3-TTS details and voice options, see [references/qwen-tts.md](references/qwen-tts.md)
- For MiMo-Audio capabilities, see [references/mimo-audio.md](references/mimo-audio.md)


## Recent Updates (Auto-generated)

**Source**: [[bugfix] Fix unexpected argument 'is_finished' in function llm2code2wav_async_chunk of mimo-audio](https://github.com/vllm-project/vllm-omni/pull/1570)

### Changes
- Bug fix: [bugfix] Fix unexpected argument 'is_finished' in function llm2code2wav_async_chunk of mimo-audio

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[NPU][Bugfix] Align GPU side and recover qwen3-tts](https://github.com/vllm-project/vllm-omni/pull/1564)

### Changes
- Bug fix: [NPU][Bugfix] Align GPU side and recover qwen3-tts

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Fix][Chore] Qwen3-TTS Modeling Minor Code Sanity Improvements](https://github.com/vllm-project/vllm-omni/pull/1482)

### Changes
- Bug fix: [Fix][Chore] Qwen3-TTS Modeling Minor Code Sanity Improvements

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Fix case-sensitive task_type matching in Qwen3TTSModelForGeneration](https://github.com/vllm-project/vllm-omni/pull/1455)

### Changes
- Bug fix: [Bugfix] Fix case-sensitive task_type matching in Qwen3TTSModelForGeneration

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Qwen3TTS][Feat] Streaming output](https://github.com/vllm-project/vllm-omni/pull/1438)

### Changes
- New feature: [Qwen3TTS][Feat] Streaming output

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Debug] Multi-Request for Qwen 3 Omni use_audio_in_video](https://github.com/vllm-project/vllm-omni/pull/1433)


*Updated: 2026-03-04*
