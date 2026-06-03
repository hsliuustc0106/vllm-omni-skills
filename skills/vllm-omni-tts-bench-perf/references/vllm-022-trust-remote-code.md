# `trust_remote_code` Under vllm 0.22+

`get_tokenizer` in vllm 0.22+ calls `cached_resolve_tokenizer_args`, which fails on TTS models distributed with custom code unless `trust_remote_code` is set on the **client** as well as the server.

## Symptom

```
ValueError: Tokenizer class XXX does not exist or is not currently imported.
```

…when running `bench_tts.py` against a vllm 0.22+ server, even though the server started fine.

## Fix

`bench_tts.py` forwards anything after `--` to the underlying client. Pass `--trust-remote-code` there:

```bash
python benchmarks/tts/bench_tts.py \
  --model Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
  --task voice_clone \
  --dataset-name seed-tts \
  --concurrency 1 4 \
  -- --trust-remote-code
```

## Why Two Flags

The server-side `--trust-remote-code` resolves the model class. The client-side one resolves the **tokenizer** class, which the bench harness loads independently to drive the request loop.
