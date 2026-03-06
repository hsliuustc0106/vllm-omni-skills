# Qwen3-TTS Models

## Architecture

Qwen3-TTS is a two-stage TTS pipeline built on the Qwen3 language model:

- **Stage 0 (Code Predictor)**: Autoregressive Qwen3-based model that converts text tokens into discrete RVQ codec codes. Uses vLLM's native `Qwen3DecoderLayer` with fused `QKVParallelLinear` and PagedAttention.
- **Stage 1 (Code2Wav)**: Wraps the HF SpeechTokenizer to decode codec codes into audio waveform.

The 12Hz variants generate audio tokens at 12 tokens per second.

## Model Variants

### 1.7B Models

#### Qwen3-TTS-12Hz-1.7B-CustomVoice

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

#### Qwen3-TTS-12Hz-1.7B-VoiceDesign

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

#### Qwen3-TTS-12Hz-1.7B-Base

- **HF ID**: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`
- **Parameters**: 1.7B
- **Min VRAM**: 8 GB
- **Key feature**: Base TTS without voice cloning or design

### 0.6B Models

#### Qwen3-TTS-12Hz-0.6B-CustomVoice

- **HF ID**: `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`
- **Parameters**: 0.6B
- **Min VRAM**: 4 GB
- **Key feature**: Lightweight voice cloning

#### Qwen3-TTS-12Hz-0.6B-Base

- **HF ID**: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`
- **Parameters**: 0.6B
- **Min VRAM**: 4 GB
- **Key feature**: Lightweight base TTS

## Serving Configuration

```bash
# Async chunk streaming (default, lower TTFP)
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
  --omni --port 8091 \
  --stage-configs-path vllm_omni/model_executor/stage_configs/qwen3_tts.yaml

# Batch mode (higher throughput, no streaming)
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
  --omni --port 8091 \
  --stage-configs-path vllm_omni/model_executor/stage_configs/qwen3_tts_batch.yaml
```

The server exposes both `/v1/audio/speech` and `/v1/chat/completions` endpoints for TTS.

## Output Formats

| Format | Extension | Quality | Size |
|--------|-----------|---------|------|
| WAV | .wav | Lossless | Large |
| MP3 | .mp3 | Good | Small |
| Opus | .opus | Good | Smallest |
