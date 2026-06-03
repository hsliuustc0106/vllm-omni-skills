---
name: vllm-omni-tts-bench-acc
description: Benchmark TTS accuracy and audio quality in vLLM-Omni, covering intelligibility (WER/CER via Whisper), speaker similarity (WavLM/ECAPA-TDNN), naturalness (UTMOS), and codec reconstruction fidelity. Use when validating a TTS port produces audio matching a reference implementation, regression-checking after refactors that touch codec/vocoder paths, comparing model variants, or wiring an accuracy gate into CI.
---

# vLLM-Omni TTS Accuracy Benchmark

## Overview

Performance benchmarks tell you the server is fast. Accuracy benchmarks tell you the audio is correct. A regression in `bench-perf` is loud; a regression in `bench-acc` is silent until users hear it. Run accuracy benchmarks any time you touch Stage 1 sampling, code2wav, or the vocoder path.

Four axes, four metrics:

| Axis | Metric | Tool |
|---|---|---|
| Intelligibility | WER / CER | Whisper (large-v3 default) |
| Speaker fidelity | Cosine similarity in speaker-embedding space | WavLM-base / ECAPA-TDNN |
| Naturalness | UTMOS (predicted MOS) | UTMOSv2 |
| Codec / vocoder | PESQ, STOI, vs. reference decode | pesq, pystoi |

## Dataset

Standard reference: `linyueqian/seed-tts-eval-subset` on HuggingFace.

- `prompt-wavs/` — **reference audio for voice cloning** (used as input)
- `wavs/` — ground-truth audio for the prompt text (used as the speaker-similarity reference)

These are different directories. The voice-clone task points at `prompt-wavs/`; the speaker-similarity reference reads from `wavs/`. Mixing them up makes SIM look artificially high.

Locales: `en` and `zh` cover the standard CI cells. Multi-locale models should add the locale-specific cell.

## Workflow

### 1. Generate audio for the eval set

```bash
vllm serve <model> --omni --port 8000

python benchmarks/tts/bench_tts.py \
  --model <model> \
  --task voice_clone \
  --dataset-name seed-tts \
  --dataset-path linyueqian/seed-tts-eval-subset \
  --locale en \
  --concurrency 1 \
  --num-prompts <full-eval-size> \
  --save-audio-dir results/<run-name>/audio
```

Use `--concurrency 1` for accuracy runs — batching can introduce sampling variance that obscures real quality deltas.

### 2. Run the four metric scripts

See [references/asr-wer.md](references/asr-wer.md), [references/speaker-sim.md](references/speaker-sim.md), [references/utmos.md](references/utmos.md), [references/codec-fidelity.md](references/codec-fidelity.md) for the exact commands. The short form:

```bash
python -m scripts.score_wer       --audio results/<run>/audio --refs <eval-jsonl>  # WER/CER
python -m scripts.score_sim       --audio results/<run>/audio --refs <wavs-dir>    # speaker SIM
python -m scripts.score_utmos     --audio results/<run>/audio                       # UTMOS
python -m scripts.score_codec_pq  --audio results/<run>/audio --refs <wavs-dir>     # PESQ/STOI
```

### 3. Compare against a reference run

Two reference patterns:

**Reference implementation parity:** generate the same eval with the upstream HF/reference code, then diff metrics. New ports must land within a small delta on each axis (typical thresholds: WER ≤ +0.5pp, SIM ≤ −0.01, UTMOS ≤ −0.05).

**Cross-build regression:** generate on `main` and on the PR branch, compare. Use the same Whisper checkpoint, the same speaker model, and the same UTMOS folds — otherwise the deltas are not comparable.

### 4. CI gate (optional)

Accuracy runs are slower than perf runs and dataset-bound. Most teams gate them on a nightly job, not per-PR. When wiring up:

- Pin Whisper model id and revision
- Pin UTMOS model and revision (UTMOSv2 has 5 folds — pre-fetch all)
- Pin dataset revision
- Quote a baseline + tolerance per metric, not a single number

## Reading the Numbers

| Pattern | Likely cause |
|---|---|
| WER up, SIM up, UTMOS down | Vocoder regressed (cleaner sampling, worse audio quality) |
| WER stable, SIM down sharply | Stage 1 / token sampling temperature changed |
| WER up, UTMOS stable | Stage 1 → text grounding broke (wrong codes, intelligible voice) |
| All four down uniformly | Wrong reference dir (`wavs/` vs `prompt-wavs/`), or wrong locale |
| UTMOS down only on Chinese | Whisper-small ASR mistranscribed Chinese — bump to large-v3, add `language="zh"` and `initial_prompt` |

## Common Mistakes

| Mistake | Cost | Fix |
|---|---|---|
| Use `prompt-wavs/` as SIM reference | SIM looks ~0.99 always | Use `wavs/` |
| Concurrency > 1 on accuracy runs | Sampling jitter | `--concurrency 1` |
| Default Whisper-small on Chinese | False WER regressions | Use large-v3 + language + initial_prompt |
| UTMOS folds re-downloaded each run | Slow, flaky on poor links | Pre-fetch all 5 folds, mount the cache |
| Re-rolling the eval set per run | Numbers non-comparable | Pin dataset revision + seed |

## References

- [asr-wer.md](references/asr-wer.md) — Whisper WER/CER pipeline, language-specific handling
- [speaker-sim.md](references/speaker-sim.md) — speaker similarity scoring, model choice
- [utmos.md](references/utmos.md) — UTMOSv2 setup, fold pre-fetching, CPU vs GPU
- [codec-fidelity.md](references/codec-fidelity.md) — PESQ/STOI for vocoder/codec regressions
