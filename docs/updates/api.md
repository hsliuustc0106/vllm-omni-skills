# vllm-omni-api 更新日志

> 最后更新: 2026-03-04

---

### 2026-02-26
**[PR #1438](https://github.com/vllm-project/vllm-omni/pull/1438)** - Streaming output

**Added**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- Simple streaming output implementation for Qwene3TTS models for the latest disaggregated inference pipeline.

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-03-02
**[PR #1504](https://github.com/vllm-project/vllm-omni/pull/1504)** - Speed up diffusion model startup by multi-thread weight loading

**Added**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- The weight loading time for large diffusion model are large, ~3min for QwenImage, ~5min for Wan2.2-I2V 14B. This PR reduce weight loading time by loading safetensors shards in parallel with a thread pool instead of sequentially.

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-26
**[PR #1509](https://github.com/vllm-project/vllm-omni/pull/1509)** - remove unused logger in omni_diffusion (#531)

**Changed**:
- <!-- markdownlint-disable -->
- Resolve #531 (the first item, which is the only item that still applies in the current codebase)
- As is explained in the comment of 531 (https://github.com/vllm-project/vllm-omni/issues/531#issuecomment-3964798019), other items are no longer applicable or have already been fixed in today's codebase

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-26
**[PR #1522](https://github.com/vllm-project/vllm-omni/pull/1522)** - Use uds for zmq address if not set --stage-id

**Added**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- Quick fix test failure:

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-28
**[PR #1554](https://github.com/vllm-project/vllm-omni/pull/1554)** - fix(qwen3-tts): fix Base ICL voice clone producing corrupted audio

**Fixed**:
- - Fix Base task ICL (in-context learning) voice clone mode producing mostly-silent/corrupted audio output
- - Root cause: `_estimate_prompt_len` did not pass `estimate_ref_code_len` callback, so prompt length estimation always fell back to 2048, causing a mismatch with model-side embeddings
- - Load codec frame rate from speech tokenizer config at init, and provide a callback that estimates `ref_code_len = ceil(audio_duration * codec_frame_rate)` from the resolved waveform

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-28
**[PR #1562](https://github.com/vllm-project/vllm-omni/pull/1562)** - Fix unexpected crash when init OmniDiffusion

**Fixed**:
- When init class of OmniDiffusion, it may cause unexpected crash since var "pipeline_class" may not be initialied.
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-03-02
**[PR #1566](https://github.com/vllm-project/vllm-omni/pull/1566)** - Import InputPreprocessor into Renderer

**Fixed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- Because https://github.com/vllm-project/vllm/pull/34510 this issue Move InputPreprocessor, so we need to fix.

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-03-03
**[PR #1609](https://github.com/vllm-project/vllm-omni/pull/1609)** - Fix filepath resolution for model with subdir and GLM-Image generation

**Fixed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- Resolves #1608

**Updated in skill**:
- ✅ (自动标记)

---


## 2026-03 - Week 1

### 2026-03-04
**[PR #1644](https://github.com/vllm-project/vllm-omni/pull/1644)** - IPC serialization fix

**Changed**:
- Improved IPC serialization for numpy scalars
- Prevents multi-process communication failures

---

*本文件由 vllm-omni-skills auto-update 系统自动维护*
