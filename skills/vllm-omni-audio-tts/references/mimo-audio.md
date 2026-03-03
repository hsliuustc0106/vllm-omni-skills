# MiMo-Audio

## Overview

MiMo-Audio-7B-Instruct by Xiaomi is a multimodal audio model that supports both audio understanding (speech recognition, audio classification) and audio generation (text-to-speech).

## Model Details

- **HF ID**: `XiaomiMiMo/MiMo-Audio-7B-Instruct`
- **Parameters**: 7B
- **Min VRAM**: 24 GB
- **Capabilities**: Audio understanding, text-to-speech, audio question answering

## Usage

### Audio Understanding

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="XiaomiMiMo/MiMo-Audio-7B-Instruct")

outputs = omni.generate(
    prompt="Transcribe this audio recording.",
    audio_inputs=["meeting_recording.wav"],
)
print(outputs[0].request_output[0].text)
```

### Audio Question Answering

```python
outputs = omni.generate(
    prompt="How many speakers are in this audio? What language are they speaking?",
    audio_inputs=["conversation.wav"],
)
print(outputs[0].request_output[0].text)
```

### Text-to-Speech

```python
outputs = omni.generate("Please read this aloud: Welcome to MiMo Audio.")
outputs[0].request_output[0].audio.save("mimo_speech.wav")
```

## Serving

```bash
vllm serve XiaomiMiMo/MiMo-Audio-7B-Instruct --omni --port 8091
```

## Comparison with Qwen3-TTS

| Feature | MiMo-Audio-7B | Qwen3-TTS |
|---------|--------------|-----------|
| TTS | Yes | Yes |
| Voice cloning | No | Yes (CustomVoice) |
| Audio understanding | Yes | No |
| Min VRAM | 24 GB | 4-8 GB |
| Parameters | 7B | 0.6-1.7B |

Use MiMo-Audio when you need bidirectional audio capabilities (understanding + generation). Use Qwen3-TTS for dedicated, lightweight TTS with voice customization.
