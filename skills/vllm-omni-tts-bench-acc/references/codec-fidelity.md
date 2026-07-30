# Codec / Vocoder Fidelity

When a refactor touches the codec decoder or the vocoder, you want metrics that compare audio waveform to a reference waveform, independent of what model produced the codes.

## Two Cheap Checks

### PESQ (Perceptual Evaluation of Speech Quality)

```python
from pesq import pesq
import soundfile as sf

ref,  sr_r = sf.read(ref_path,   dtype="float32")  # pesq needs float32 or int16
synth, sr_s = sf.read(synth_path, dtype="float32")
assert sr_r == sr_s == 16000  # PESQ is 8k or 16k
score = pesq(16000, ref, synth, "wb")  # wideband
```

Range: −0.5 to 4.5, higher is better. Good resynthesis: ≥3.5.

### STOI (Short-Time Objective Intelligibility)

```python
from pystoi import stoi
score = stoi(ref, synth, fs_sig=16000, extended=False)
```

Range: 0 to 1, higher is better.

## When to Run These

PESQ/STOI need **aligned reference and synth waveforms**. They are most useful for:

- **Codec parity check:** encode reference audio → decode through the codec path → compare to original
- **Vocoder regression:** identical Stage-1 output, two vocoder builds, diff PESQ/STOI
- **End-to-end** when the synthesized audio matches reference content (read-aloud setups)

They are **not** useful when the TTS model is free to produce arbitrarily different prosody — there the waveform never aligns and PESQ/STOI collapse.

## Aligning Before Scoring

Use DTW or trim silence before scoring when prosody differs slightly. `librosa.effects.trim` plus a 100 ms zero-pad is usually enough for short clips.

```python
import librosa
ref_t,   _ = librosa.effects.trim(ref,   top_db=30)
synth_t, _ = librosa.effects.trim(synth, top_db=30)
n = min(len(ref_t), len(synth_t))
ref_t, synth_t = ref_t[:n], synth_t[:n]
```

## Decision Table

| Change you made | Metric to trust |
|---|---|
| Refactored Stage 1 (AR sampling) | WER, SIM, UTMOS — **not** PESQ/STOI |
| Refactored code2wav / vocoder | PESQ, STOI, UTMOS |
| Refactored streaming/chunking | Listen + perf bench; metrics are insensitive |
| Quantized weights | All four, in that order |
