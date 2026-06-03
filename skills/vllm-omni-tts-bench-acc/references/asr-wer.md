# ASR-Based Intelligibility (WER / CER)

## Approach

1. Run an ASR model on synthesized audio.
2. Compute WER / CER against the target text.
3. Lower is better. The ASR model is your "ear".

## Backend Choice by Locale (Match vllm-omni CI)

vllm-omni's `vllm_omni/benchmarks/data_modules/seed_tts_eval.py` uses different backends per locale, and your numbers must match that pairing to be comparable to CI:

| Locale | ASR | Notes |
|---|---|---|
| `en` | `openai/whisper-large-v3` via `transformers` (16 kHz mono) | `temperature=0.0`, `condition_on_previous_text=False` |
| `zh` | `paraformer-zh` via `funasr`, hypothesis normalised with `zhconv` to zh-cn | Whisper on Chinese disagrees with CI WER by several points — do not substitute |

Install: `pip install 'vllm-omni[seed-tts-eval]'` brings both backends and `zhconv`.

## Pipeline — English

```python
import jiwer, whisper

asr = whisper.load_model("large-v3")

def transcribe_en(path: str) -> str:
    return asr.transcribe(
        path,
        language="en",
        condition_on_previous_text=False,
        temperature=0.0,
    )["text"]

wer = jiwer.wer(reference_texts, [transcribe_en(p) for p in synth_paths])
cer = jiwer.cer(reference_texts, [transcribe_en(p) for p in synth_paths])
```

## Pipeline — Chinese

```python
import jiwer, zhconv
from funasr import AutoModel

asr = AutoModel(model="paraformer-zh")

def transcribe_zh(path: str) -> str:
    res  = asr.generate(input=path, batch_size_s=300)
    text = res[0]["text"]
    return zhconv.convert(text, "zh-cn")

# Character-level CER is the standard for Chinese
cer = jiwer.cer(reference_texts, [transcribe_zh(p) for p in synth_paths])
```

When a regression is locale-specific, suspect the ASR backend before suspecting the TTS model.

## Text Normalization

`jiwer.Compose([RemovePunctuation(), ToLowerCase(), Strip(), ReduceToListOfListOfWords()])` for English. For CJK, character-level CER without normalization is more meaningful than WER.

## Reference Run

Always quote the ASR model version alongside the WER number:

```
voice_clone / seed-tts-en / Whisper-large-v3-20231106:
  WER = 4.1%  (baseline 4.3%, Δ = −0.2pp)
```

Same ASR, same dataset, same locale — otherwise the numbers do not compare.
