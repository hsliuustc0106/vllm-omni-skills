# CosyVoice3

## Architecture

CosyVoice3 is a two-stage TTS system from FunAudioLLM:

- **Stage 0 (Talker)**: Autoregressive model that converts text prompts into speech tokens.
- **Stage 1 (Code2Wav)**: Conditional flow matching (CFM) decoder that transforms speech tokens into acoustic features, followed by a HiFiGAN vocoder for waveform synthesis.

Unlike Qwen3-TTS, CosyVoice3 does not yet support async_chunk streaming - Stage 0 completes fully before Stage 1 begins.

## Model

- **HF ID**: `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`
- **Parameters**: 0.5B
- **Min VRAM**: 4 GB

## Setup

The HF checkpoint requires a `config.json` with `model_type: "cosyvoice3"` for vLLM-Omni to detect the model. If the checkpoint doesn't already include one:

```json
{
    "model_type": "cosyvoice3",
    "architectures": ["CosyVoice3Model"]
}
```

Also requires mel filter assets from Whisper:
```bash
mkdir -p vllm_omni/model_executor/models/cosyvoice3/assets
curl -L https://raw.githubusercontent.com/openai/whisper/main/whisper/assets/mel_filters.npz \
  -o vllm_omni/model_executor/models/cosyvoice3/assets/mel_filters.npz
```

## Serving

```bash
vllm serve FunAudioLLM/Fun-CosyVoice3-0.5B-2512 \
  --omni --port 8091 \
  --stage-configs-path vllm_omni/model_executor/stage_configs/cosyvoice3.yaml
```

## Offline Inference

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(
    model="pretrained_models/Fun-CosyVoice3-0.5B",
    stage_configs_path="vllm_omni/model_executor/stage_configs/cosyvoice3.yaml",
    trust_remote_code=True,
    tokenizer="<model_path>/CosyVoice-BlankEN",
)
outputs = omni.generate("Hello, this is a test of CosyVoice.")
```

See `examples/offline_inference/cosyvoice3/` for the full example script.
