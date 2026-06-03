# UTMOS — Predicted MOS

UTMOSv2 predicts a Mean Opinion Score for naturalness without human raters. Treat it as a **trend signal**, not an absolute number.

## Install

```bash
pip install git+https://github.com/sarulab-speech/UTMOSv2.git
```

The PyPI `SpeechMOS` package ships a different (older) checkpoint; numbers do not match the literature.

## Folds

UTMOSv2 uses a 5-fold ensemble. Pre-fetch all folds once:

```bash
python -c "
from utmosv2 import UTMOSv2
for fold in range(5):
    UTMOSv2(fold=fold)
"
```

Each fold is ~50 MB. On a fresh box, deferring the download to the first run makes the first run 5–10× slower and brittle to mirror flakes.

## Pipeline Sketch

```python
import torch
from utmosv2 import UTMOSv2

device = "cuda" if torch.cuda.is_available() else "cpu"
models = [UTMOSv2(fold=i).to(device).eval() for i in range(5)]

@torch.inference_mode()
def utmos(path: str) -> float:
    scores = [m.predict(path).item() for m in models]
    return sum(scores) / len(scores)
```

CPU is fine; UTMOS is small. Use GPU only if you are batching tens of thousands of files.

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
