# Qwen3-TTS Models

## Architecture

Qwen3-TTS is a text-to-speech system built on the Qwen3 language model architecture. It generates speech tokens autoregressively, which are then decoded into audio waveforms. The 12Hz variant generates audio tokens at 12 tokens per second.

## Model Variants

### Qwen3-TTS-12Hz-1.7B-CustomVoice

- **HF ID**: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`
- **Parameters**: 1.7B
- **Min VRAM**: 8 GB
- **Key feature**: Voice cloning from reference audio

Provide a 5-30 second audio sample to clone a voice:
```python
omni = Omni(model="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
outputs = omni.generate(
    prompt="Text to speak in the cloned voice.",
    audio_references=["speaker_sample.wav"],
)
```

Best practices for reference audio:
- 10-20 seconds of clear speech
- Minimal background noise
- Consistent speaker (single voice)
- WAV format, 16kHz or higher sample rate

### Qwen3-TTS-12Hz-1.7B-VoiceDesign

- **HF ID**: `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`
- **Parameters**: 1.7B
- **Min VRAM**: 8 GB
- **Key feature**: Design voices from text descriptions

Describe the voice you want:
```python
omni = Omni(model="Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign")
outputs = omni.generate(
    prompt="Welcome to our service!",
    voice_description="An energetic young male voice with American accent",
)
```

### Qwen3-TTS-12Hz-0.6B-Base

- **HF ID**: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`
- **Parameters**: 0.6B
- **Min VRAM**: 4 GB
- **Key feature**: Lightweight base model for basic TTS

## Serving Configuration

```bash
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --omni --port 8091
```

The server exposes both `/v1/audio/speech` and `/v1/chat/completions` endpoints for TTS.

## Output Formats

| Format | Extension | Quality | Size |
|--------|-----------|---------|------|
| WAV | .wav | Lossless | Large |
| MP3 | .mp3 | Good | Small |
| Opus | .opus | Good | Smallest |
