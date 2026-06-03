# ASR-Based Intelligibility (WER / CER)

## Approach

1. Run an ASR model on synthesized audio.
2. Compute WER / CER against the prompt text.
3. Lower is better. The ASR model is your "ear".

## Default Model

`openai/whisper-large-v3`. Smaller models bias the numbers:

- `whisper-small` mistranscribes Chinese without language hints, producing **false** WER regressions
- `whisper-base` is unreliable below 16 kHz output

## Pipeline Sketch

```python
import whisper, jiwer, soundfile as sf

asr = whisper.load_model("large-v3")

def transcribe(path: str, lang: str | None = None, initial_prompt: str | None = None) -> str:
    return asr.transcribe(
        path,
        language=lang,             # "zh", "en", "ja", ...
        initial_prompt=initial_prompt,
        condition_on_previous_text=False,
        temperature=0.0,
    )["text"]

wer = jiwer.wer(reference_texts, [transcribe(p) for p in synth_paths])
cer = jiwer.cer(reference_texts, [transcribe(p) for p in synth_paths])
```

## Language-Specific Handling

| Language | Required hint | Notes |
|---|---|---|
| `en` | none | default settings work |
| `zh` | `language="zh"`, `initial_prompt="以下是普通话内容。"` | without these, Chinese audio is often transcribed as pinyin or English |
| `ja` | `language="ja"`, `initial_prompt="以下は日本語です。"` | same kanji confusion problem |

When a regression is locale-specific, suspect the ASR setup before suspecting the TTS model.

## Text Normalization

`jiwer.Compose([RemovePunctuation(), ToLowerCase(), Strip(), ReduceToListOfListOfWords()])` for English. For CJK, character-level CER without normalization is more meaningful than WER.

## Reference Run

Always quote the ASR model version alongside the WER number:

```
voice_clone / seed-tts-en / Whisper-large-v3-20231106:
  WER = 4.1%  (baseline 4.3%, Δ = −0.2pp)
```

Same ASR, same dataset, same locale — otherwise the numbers do not compare.
