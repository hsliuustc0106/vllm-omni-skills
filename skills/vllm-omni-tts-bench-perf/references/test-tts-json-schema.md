# `tests/dfx/perf/tests/test_tts.json` Schema

Each top-level entry defines a test that the perf CI runs end-to-end: start server, run client, compare against `baseline`, fail on regression.

## Shape

```json
[
  {
    "test_name": "test_qwen3_tts_base",
    "server_params": {
      "model": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
      "stage_overrides": { "1": { "devices": "1" } }
    },
    "benchmark_params": [
      { /* one cell per eval_phase */ }
    ]
  }
]
```

## `benchmark_params` Cell

| Field | Required | Notes |
|---|---|---|
| `task` | yes | `voice_clone`, `voice_design`, `tts` |
| `eval_phase` | yes | `latency`, `throughput`, `quality` |
| `dataset_name` | yes | `seed-tts` for the standard subset |
| `backend` | yes | `openai-audio-speech` for the standard `/v1/audio/speech` endpoint |
| `endpoint` | yes | typically `/v1/audio/speech` |
| `dataset_path` | yes | HF id, e.g. `linyueqian/seed-tts-eval-subset` |
| `num_prompts` | yes | parallel array, indexed with `max_concurrency` |
| `max_concurrency` | yes | parallel array, indexed with `num_prompts` |
| `seed_tts_locale` | when `dataset_name=seed-tts` | `en` or `zh` |
| `percentile-metrics` | yes | comma list, e.g. `ttft,e2el,audio_rtf,audio_ttfp,audio_duration` |
| `baseline` | yes for CI | see below |
| `enabled` | optional | set `false` to skip without deleting |

## `baseline` Block

Arrays are positional and must have the same length as `max_concurrency`.

```json
"baseline": {
  "median_audio_ttfp_ms": [1000, 3000, 14000],
  "median_audio_rtf":     [0.70, 1.15, 3.90],
  "audio_throughput":     [12,   14,   14]
}
```

| Field | Direction | Notes |
|---|---|---|
| `median_audio_ttfp_ms` | lower is better | per-cell median time to first audio packet in ms |
| `median_audio_rtf` | lower is better | per-cell median real-time factor |
| `audio_throughput` | higher is better | per-cell aggregate seconds/sec |

`--assert-baseline` on the runner fails the job when any metric crosses its threshold in the wrong direction.

## Common Phases

| `eval_phase` | Typical `max_concurrency` | What it measures |
|---|---|---|
| `latency` | `[1]` | Cold-state user-perceived latency |
| `throughput` | `[8, 16, 64]` | Saturation behaviour |
| `quality` | optional, disabled in perf CI | Set `enabled=false`; route accuracy benchmarks through the accuracy skill |

## Adding a New Cell — Checklist

1. Decide latency vs throughput; do not mix in one cell.
2. Use sequential, same-GPU runs to derive numbers ([methodology.md](methodology.md)).
3. Set `baseline` from median of repetitions 2–N, plus ~10% headroom.
4. Run `tests/dfx/perf` locally with `--assert-baseline` to confirm pass-on-current.
5. Open a PR; document the hardware class and the runs used.
