# New Model Addition Review Checklist

Quick-reference checklist for PRs that add a new omni model (TTS, audio, multimodal pipeline). Use after reading the PR diff and body. Complements [diffusion-checklist.md](diffusion-checklist.md) (which covers diffusion/image/video models specifically).

---

## Quick Red Flags (scan first)

| # | Red Flag | Action |
|---|----------|--------|
| 1 | PR body lists files/architectures not present in diff | Request PR description update; flag as incomplete |
| 2 | `__all__` re-exports private `_`-prefixed functions | These shouldn't be public API |
| 3 | Same string constant defined in 3+ files | Consolidate to single source |
| 4 | "backward-compat alias" comment in brand-new code | Drop the alias |
| 5 | `del unused_param` inside function body | Remove the parameter from the signature |

---

## Dimension 1: PR Description vs Diff Integrity

The most common issue in new-model PRs is the description claiming more than the diff delivers.

- [ ] **PR body file list matches `git diff --name-only`.** Every file path mentioned in the description must appear in the diff. Common mismatches: missing model variants (e.g. 2.6 mentioned but only 4.5 present), missing stage configs, missing stage input processors.
- [ ] **Claimed architecture count matches registry entries.** If the body says "8 architectures registered," count the actual `_OMNI_MODELS` entries added in `registry.py`.
- [ ] **Stage config YAMLs reference existing files.** Any `custom_process_input_func` paths, `pipeline:` keys, and model arch strings must resolve to files/entries in the diff.
- [ ] **Example README modes match implemented code.** If the README documents 15 modes but `run_curl.sh` implements 3, flag it.

---

## Dimension 2: Dead Code Scan (model-addition specific)

### 2.1 Dead `forward()` in Stage Modules

When a model uses a custom generation path (e.g. `FlowLoss.sample()`, `CFM.sample()`), the `nn.Module.forward()` may be left over from training code.

```python
# DEAD: only self.flowloss.sample() is called, never self.flowloss(...)
class FlowLoss(nn.Module):
    def forward(self, cond, target, latent_history, mask, patch_size):
        return self.cfm(...)  # never invoked at inference
```

**Scan for:** Any `nn.Module` subclass where only a non-`forward` method is called.

### 2.2 Dead Factory / Builder Functions

```python
# DEAD: ming_tts_llm.py constructs Aggregator(...) directly
def build_ming_aggregator(cfg: MingTTSConfig) -> Aggregator:
    return Aggregator(in_channels=cfg.latent_dim, ...)
```

**Scan for:** Functions in `__all__` with zero call sites in the diff.

### 2.3 Dead Wrapper Methods

```python
# DEAD: CustomProcessMixin already registered self.preprocess
def preprocess_input(self, input_ids, input_embeds, **info_dict):
    return self.preprocess(input_ids, input_embeds, **info_dict)
```

**Scan for:** Methods whose body is a single delegation to another method with identical signature.

### 2.4 Dead Branch Guards (key never set)

```python
# DEAD: _ming_payload_stripped is never set to True anywhere in the diff
stripped = bool(info.get("_ming_payload_stripped", False))
if stripped:
    raise RuntimeError(...)  # unreachable
```

**Scan for:** Dictionary keys checked in `if` branches that are never assigned.

### 2.5 Unused Parameters

```python
def pad_prompt_waveform(waveform, *, patch_size, sample_rate, frame_hop):
    del frame_hop  # parameter accepted but immediately discarded
```

**Scan for:** `del <param_name>` at the top of a function body, or parameters never read.

---

## Dimension 3: Copy-Paste Detection

### 3.1 String Constants Defined in Multiple Files

The most frequent copy-paste issue in multi-stage pipelines: the same string key is defined independently in each stage's file instead of being imported from a shared source.

```
MING_STOP_REASON_KEY = "ming_stop_reason"
  ├── patch_emission.py (canonical)
  ├── ming_tts.py (duplicate)
  ├── ming_tts_audio_vae.py (duplicate)
  └── stage_input_processors/ming_tts.py (duplicate)
```

**Scan for:** `grep -n "^[A-Z_]+ = \"" <diff>` and check for repeated RHS string values across files.

### 3.2 Cross-Module Validation Duplication

```python
# Same geometry check in both AudioVAE.__init__ and validate_ming_tts_config()
# modeling_audio_vae.py:
if enc_kwargs["input_dim"] != hop_size: raise ValueError(...)
# validation.py:
if enc_input_dim != enc_hop_size: raise ValueError(...)
```

**Scan for:** Similar assertions with similar error messages in both a model `__init__` and a `validate_*` function.

### 3.3 Near-Identical Shape Coercion Functions

```python
# patch_emission.py
def _coerce_latent_history(value, *, device, dtype, cfg): ...
# ming_tts_audio_vae.py
def _coerce_latent_chunk(latent, *, device, dtype, latent_dim, patch_size): ...
```

Both reshape 2D→3D with dimension validation. One can call the other or they can share a helper.

---

## Dimension 4: Registry and Config Consistency

- [ ] **Pipeline registry model_type matches deploy YAML `pipeline:` key.** If a deploy YAML declares `pipeline: minicpmo_4_5`, the pipeline registry must have a `"minicpmo_4_5"` entry.
- [ ] **Every architecture in `_OMNI_MODELS` has a corresponding file.** E.g. `"MingLLMModel": ("ming_tts", "ming_tts_llm", ...)` means `ming_tts/ming_tts_llm.py` must exist and export `MingLLMModel`.
- [ ] **Deploy YAML consistency.** If 3 deploy variants exist, all 3 should either declare `pipeline:` or all should rely on auto-detection. Mixed conventions are fragile.
- [ ] **`hf_config_predicate` is correct for sibling model generations.** If an older generation (e.g. 2.6) shares `architectures=["MiniCPMO"]` with a newer one (e.g. 4.5), the predicate must reliably disambiguate them (e.g. via `version` field).

---

## Dimension 5: Import Hygiene

- [ ] **Imports used only for `__all__` re-export.** Constants imported into `config_<model>.py` solely to list in `__all__` should be noted. Prefer importing from the canonical source directly.
- [ ] **Module-level side effects.** `_install_torchaudio_soundfile_shim()` called at import time — acceptable for deployment-critical shims but should be documented.
- [ ] **No redundant `import os` (or similar) inside function bodies when already at module top.**

---

## Dimension 6: Examples and Shell Scripts

- [ ] **Shell script modes match documentation.** `run_curl.sh` / `run_server.sh` should support every mode the README documents.
- [ ] **`os.environ` access in inline Python heredocs.** Shell variables must be `export`ed before a `python <<'PY'` heredoc can read them via `os.environ`.
- [ ] **Hardcoded `/tmp/` paths use unique names** or `mktemp` to avoid concurrent-invocation collisions.
