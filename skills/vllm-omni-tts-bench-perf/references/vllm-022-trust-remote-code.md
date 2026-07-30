# `trust_remote_code` Under vllm 0.22+

`get_tokenizer` in vllm 0.22+ calls `cached_resolve_tokenizer_args`, which fails on TTS models distributed with custom code unless `trust_remote_code` is set on the **client** as well as the server.

## Symptom

```
ValueError: Tokenizer class XXX does not exist or is not currently imported.
```

…when running `bench_tts.py` against a vllm 0.22+ server, even though the server started fine.

## Why The Obvious Fixes Do Not Work

`bench_tts.py`'s positional `extra` uses `argparse.REMAINDER`. Two patterns that look right both fail:

| Attempt | Outcome |
|---|---|
| `bench_tts.py … --trust-remote-code` (trailing) | argparse rejects the unknown flag before REMAINDER captures it. |
| `bench_tts.py … -- --trust-remote-code` (separator) | REMAINDER captures `['--', '--trust-remote-code']`; the literal `--` is forwarded to `vllm bench serve`, which rejects the bare separator. |

## Workarounds

**Option A — drive the underlying CLI directly** (recommended for one-off bench runs):

```bash
vllm bench serve --omni \
  --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --backend openai-audio-speech \
  --endpoint /v1/audio/speech \
  --trust-remote-code \
  --max-concurrency 1 --num-prompts 20 \
  --dataset-name seed-tts --dataset-path linyueqian/seed-tts-eval-subset
```

You lose `model_configs.yaml` task-extra-body convenience, so reproduce the per-task `--extra-body` JSON from that file manually.

**Option B — patch `bench_tts.py`** to strip the leading `--` separator (one-line change in `benchmarks/tts/bench_tts.py`'s `main`, near the `extra_cli_args=args.extra or []` line):

```python
extra = args.extra or []
if extra and extra[0] == "--":
    extra = extra[1:]
# then pass extra= instead of args.extra
```

Once that lands, `bench_tts.py … -- --trust-remote-code` works as expected. Worth a small upstream PR.

## Why Two Flags

The server-side `--trust-remote-code` resolves the model class. The client-side one resolves the **tokenizer** class, which the bench harness loads independently to drive the request loop.
