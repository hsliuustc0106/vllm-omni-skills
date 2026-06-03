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

Standard reference: `linyueqian/seed-tts-eval-subset` on HuggingFace, the same subset CI uses in `tests/dfx/perf/tests/test_tts.json`.

- `<locale>/prompt-wavs/` — speaker prompts for voice cloning (used as **both** request input and the vllm-omni-internal SIM reference)
- `<locale>/meta.lst` — utterance metadata (utt_id, prompt text, target text)

vllm-omni's built-in eval (`vllm_omni/benchmarks/data_modules/seed_tts_eval.py`) scores SIM against the **prompt wav** (output-vs-prompt, SIM-o). If you instead want SIM-r (output-vs-ground-truth) you need a separately curated reference set; this skill documents the parity path.

Locales: `en` and `zh`. ZH and EN use different ASR backends — see below.

## Workflow

### 1. Run the eval through vllm-omni's built-in `--wer-eval`

The fastest correct path is `bench_tts.py --wer-eval`, which runs the bench, drops audio under `--output-dir`, and scores WER / SIM / UTMOS in the same process using the same Whisper / Paraformer / WavLM the CI uses.

```bash
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-Base --omni --port 8000

python benchmarks/tts/bench_tts.py \
  --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --task voice_clone \
  --dataset-path linyueqian/seed-tts-eval-subset \
  --locale en \
  --concurrency 1 \
  --num-prompts <full-eval-size> \
  --wer-eval \
  --output-dir results/<run-name>
```

Use `--concurrency 1` for accuracy runs — batching introduces sampling variance that obscures real quality deltas.

### 2. Read the per-utterance metrics

The output directory holds one JSON per cell with `seed_tts_wer_eval_items` (per-utt) plus aggregate WER / CER / SIM. UTMOS scoring is opt-in inside that JSON path and is wired in `seed_tts_eval.py`.

### 3. Compare against a reference run

Two reference patterns:

**Reference implementation parity:** generate the same eval with the upstream HF/reference code, then diff metrics. New ports must land within a small delta on each axis (typical thresholds: WER ≤ +0.5pp, SIM ≤ −0.01, UTMOS ≤ −0.05).

**Cross-build regression:** generate on `main` and on the PR branch, compare. Use the same ASR model, the same speaker model, and the same UTMOS revision — otherwise the deltas are not comparable.

### 4. CI gate (optional)

Accuracy runs are slower than perf runs and dataset-bound. Most teams gate them on a nightly job, not per-PR. When wiring up:

- Pin ASR model id and revision (Whisper-large-v3 for EN, Paraformer-zh for ZH — see [asr-wer.md](references/asr-wer.md))
- Pin UTMOSv2 revision
- Pin dataset revision
- Quote a baseline + tolerance per metric, not a single number

## Reading the Numbers

| Pattern | Likely cause |
|---|---|
| WER up, SIM up, UTMOS down | Vocoder regressed (cleaner sampling, worse audio quality) |
| WER stable, SIM down sharply | Stage 1 / token sampling temperature changed |
| WER up, UTMOS stable | Stage 1 → text grounding broke (wrong codes, intelligible voice) |
| All four off uniformly | Wrong locale, or wrong ASR backend for the locale |
| WER on Chinese looks pathological | Wrong ASR — vllm-omni's parity is Paraformer-zh, not Whisper. See [asr-wer.md](references/asr-wer.md) |

## Common Mistakes

| Mistake | Cost | Fix |
|---|---|---|
| Use Whisper for Chinese parity | Disagrees with vllm-omni CI WER | Use Paraformer-zh via funasr |
| Hand-roll SIM with `wavs/` as the reference | Numbers do not match CI | vllm-omni's SIM-o uses `prompt-wavs/`; use that for parity, or label your run as SIM-r explicitly |
| Concurrency > 1 on accuracy runs | Sampling jitter | `--concurrency 1` |
| Re-rolling the eval set per run | Numbers non-comparable | Pin dataset revision + seed |

## References

- [asr-wer.md](references/asr-wer.md) — Whisper WER/CER pipeline, language-specific handling
- [speaker-sim.md](references/speaker-sim.md) — speaker similarity scoring, model choice
- [utmos.md](references/utmos.md) — UTMOSv2 setup, fold pre-fetching, CPU vs GPU
- [codec-fidelity.md](references/codec-fidelity.md) — PESQ/STOI for vocoder/codec regressions
