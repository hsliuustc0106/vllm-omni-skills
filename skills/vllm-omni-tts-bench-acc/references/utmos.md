# UTMOS — Predicted MOS

UTMOSv2 predicts a Mean Opinion Score for naturalness without human raters. Treat it as a **trend signal**, not an absolute number.

## Install

```bash
pip install git+https://github.com/sarulab-speech/UTMOSv2.git
```

The PyPI `SpeechMOS` package ships a different (older) checkpoint; numbers do not match the literature.

## Pipeline

`utmosv2.create_model(pretrained=True)` returns the 5-fold ensemble already; you do not loop folds yourself. `model.predict(input_path=...)` returns a plain float.

```python
import utmosv2

model = utmosv2.create_model(pretrained=True)

def utmos(path: str) -> float:
    return model.predict(input_path=path)
```

The first call to `create_model(pretrained=True)` downloads the bundled checkpoint and caches it under the package's default cache dir. On a fresh box, deferring to the first scoring call makes that call ~30 s; pre-warm by calling `create_model` at script start.

## Reading Scores

- Real human MOS ranges roughly 3.5–4.5
- UTMOS predictions sit in a similar band but are not directly comparable to human MOS
- Reportable threshold: changes of ≥0.05 between two runs of the same eval set, same checkpoints

## When UTMOS Disagrees With Your Ears

UTMOS is biased toward common training distributions. It will under-rate:

- Strong accents, dialectal speech
- Singing or expressive ranges
- Sub-16 kHz audio (always resample to 16 kHz mono before scoring)

If your model targets one of these, supplement UTMOS with a small human-rating round.
