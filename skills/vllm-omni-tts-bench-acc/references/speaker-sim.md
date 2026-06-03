# Speaker Similarity (SIM)

## Approach

Embed reference audio and synthesized audio in a speaker-embedding space, then take cosine similarity. For voice cloning, the synthesized clip should land close to the **ground-truth** clip (`wavs/`), not to the **prompt** clip (`prompt-wavs/`).

## Model Choices

| Model | Strengths | Notes |
|---|---|---|
| `microsoft/wavlm-base-plus-sv` | Robust, widely used in TTS papers | Default for parity studies |
| ECAPA-TDNN (SpeechBrain) | Strong on cross-lingual | Heavier dependency |
| Resemblyzer | Light, fast | Quality lower than WavLM/ECAPA |

Pick one and pin its revision. Comparing numbers across models is meaningless.

## Pipeline Sketch

```python
import torch, torchaudio
from transformers import AutoFeatureExtractor, AutoModel

device = "cuda" if torch.cuda.is_available() else "cpu"
fe   = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
emb  = AutoModel.from_pretrained("microsoft/wavlm-base-plus-sv").to(device).eval()

@torch.inference_mode()
def embed(path: str) -> torch.Tensor:
    wav, sr = torchaudio.load(path)
    if sr != 16000:
        wav = torchaudio.functional.resample(wav, sr, 16000)
    inputs = fe(wav.squeeze(0).numpy(), sampling_rate=16000, return_tensors="pt").to(device)
    return emb(**inputs).embeddings.squeeze(0)

cos = torch.nn.functional.cosine_similarity(embed(synth), embed(ref_wavs_dir), dim=0).item()
```

## Reference Picking — Gotcha

For voice cloning the **reference for SIM** is the ground-truth recording (`wavs/<utt_id>.wav`), not the prompt audio (`prompt-wavs/<utt_id>.wav`). The prompt is the input; the ground truth is the target.

Using the prompt as both input and reference will give SIM ≈ 0.99 across the board and mask real regressions.

## Typical Numbers

- Strong cloning models on in-distribution data: SIM ≈ 0.78–0.88
- Cross-lingual or zero-shot: SIM drops 0.05–0.15
- A 0.02 absolute drop is a real regression worth investigating

## Channel and SR Mismatches

Always resample both sides to **16 kHz mono** before embedding. Bass-heavy 48 kHz vs 16 kHz comparisons can shift cosine by ≥0.03 for no good reason.
