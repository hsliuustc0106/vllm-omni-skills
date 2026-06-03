# Speaker Similarity (SIM)

## Approach

Embed reference audio and synthesized audio in a speaker-embedding space, then take cosine similarity.

Two conventions exist in the literature:

- **SIM-o** (output vs prompt): the same speaker prompt that was fed in is used as the reference. This is what vllm-omni's built-in `seed_tts_eval.py` reports, and what Seed-TTS-eval uses. The reference path is `<locale>/prompt-wavs/<utt_id>.wav` (== `seed_tts_ref_wav_path` in the dataset record).
- **SIM-r** (output vs ground truth): a separately recorded ground-truth take of the same target text is the reference.

For parity with vllm-omni CI, use SIM-o. For absolute quality claims in a paper, SIM-r is more meaningful.

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
from transformers import AutoFeatureExtractor, AutoModelForAudioXVector

device = "cuda" if torch.cuda.is_available() else "cpu"
fe   = AutoFeatureExtractor.from_pretrained("microsoft/wavlm-base-plus-sv")
emb  = AutoModelForAudioXVector.from_pretrained("microsoft/wavlm-base-plus-sv").to(device).eval()

@torch.inference_mode()
def embed(path: str) -> torch.Tensor:
    wav, sr = torchaudio.load(path)
    if wav.shape[0] > 1:                          # stereo -> mono
        wav = wav.mean(dim=0, keepdim=True)
    if sr != 16000:
        wav = torchaudio.functional.resample(wav, sr, 16000)
    inputs = fe(wav.squeeze(0).numpy(), sampling_rate=16000, return_tensors="pt").to(device)
    return emb(**inputs).embeddings.squeeze(0)

# For SIM-o (vllm-omni CI parity): ref = the prompt wav (seed_tts_ref_wav_path,
# typically <locale>/prompt-wavs/<utt_id>.wav)
# For SIM-r: ref = a separately curated ground-truth recording for this utt_id
cos = torch.nn.functional.cosine_similarity(embed(synth), embed(ref), dim=0).item()
```

`AutoModelForAudioXVector` resolves to `WavLMForXVector` for the `-sv` checkpoint and is what exposes `.embeddings`. `AutoModel` returns the base `WavLMModel` (only `last_hidden_state`), and `AutoModelForAudioClassification` returns logits, not X-vector embeddings.

## Reference Picking — Two Conventions

SIM-o and SIM-r answer different questions:

- SIM-o (output vs prompt) — does the synthesised voice sound like the speaker we prompted with? This is what vllm-omni's `seed_tts_eval.py:647-655` computes against `seed_tts_ref_wav_path` (== the `prompt-wavs/` clip).
- SIM-r (output vs ground truth) — does the synthesised audio match a separately recorded take of the target sentence? Stronger as an absolute quality claim, but requires a curated reference set.

Use SIM-o for CI parity. Document SIM-r runs as such when you use them.

## Typical Numbers

- Strong cloning models on in-distribution data: SIM ≈ 0.78–0.88
- Cross-lingual or zero-shot: SIM drops 0.05–0.15
- A 0.02 absolute drop is a real regression worth investigating

## Channel and SR Mismatches

Always resample both sides to **16 kHz mono** before embedding. Bass-heavy 48 kHz vs 16 kHz comparisons can shift cosine by ≥0.03 for no good reason.
