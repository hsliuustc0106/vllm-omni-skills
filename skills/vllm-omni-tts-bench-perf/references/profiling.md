# Profiling TTS Serving

Three layers, escalate from cheapest to most expensive.

## 1. Server-side: PyTorch profiler

Capture Stage 1 / Stage 2 / vocoder per-step breakdown.

```bash
VLLM_TORCH_PROFILER_DIR=/tmp/vllm_prof \
  vllm serve <model> --omni --port 8000

# in another shell, around the request you want to capture:
curl -X POST localhost:8000/start_profile
python benchmarks/tts/bench_tts.py ...
curl -X POST localhost:8000/stop_profile
```

Open the resulting trace in `chrome://tracing` or perfetto. Look for:

- Stage 1 (AR) wall time per token
- Stage 2 (code2wav) per-chunk cost
- Vocoder synchronous waits — these block streaming
- Inter-stage tensor transfer time

## 2. Client-side bench profile

`bench_tts.py --profile` collects request-side timings. Useful when server timings look fine but TTFP regresses — usually means tokenizer cost, ref-audio I/O, or HTTP framing.

## 3. GPU-kernel layer: nsys → NCU

When per-step time regresses but layer breakdown looks identical, drop to nsys:

```bash
nsys profile -o tts_run \
  --trace=cuda,nvtx,cudnn,cublas \
  --capture-range=cudaProfilerApi \
  python benchmarks/tts/bench_tts.py ...
```

Hot kernels (RMSNorm, attention) then go to NCU for occupancy/bandwidth roofline.

Hardware-bound vs compute-bound is GPU-class dependent — read the spec sheet first, then pick the roofline target. Bandwidth-bound classes (low FLOP/byte balance) optimise differently from compute-bound classes.

## What "regression" Usually Means

| Bench delta | Most likely cause |
|---|---|
| `audio_ttfp_ms` up, RTF unchanged | First-step regression: graph capture, Stage 1 cold |
| RTF up, `audio_ttfp_ms` unchanged | Steady-state kernel regression: Stage 2 / vocoder |
| Throughput down at `c >= 8`, latency stable | Scheduler / batching change |
| Everything up uniformly | Build or env (driver, cuda, torch); confirm before blaming the diff |
