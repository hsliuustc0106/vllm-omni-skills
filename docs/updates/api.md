# vllm-omni-api Update Log

> Last updated: 2026-03-04
> [View all skills updates](../CHANGELOG.md) | [Back to index](README.md)

---

### 2026-03-25
**[PR #2145](https://github.com/vllm-project/vllm-omni/pull/2145)** - Improve Fish Speech S2 Pro voice cloning TTFP

**Changed**:
- This PR improves Fish Speech S2 Pro voice cloning TTFP.
- Previously, the Fish Speech voice cloning path built the full clone prompt in the API server:
- - resolve `ref_audio`

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2268](https://github.com/vllm-project/vllm-omni/pull/2268)** - Fix Fish Speech S2 Pro prompt handling for truncated audio & emotion tag

**Fixed**:
- This PR fixes the Fish Speech S2 Pro issues reported in #2248 by aligning prompt construction across serving, model-side structured clone prefill, and the offline example.
- It also closes several follow-up gaps found during review:
- - structured voice clone now uses the same prompt/tag protocol as text-only serving

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2145](https://github.com/vllm-project/vllm-omni/pull/2145)** - Improve Fish Speech S2 Pro voice cloning TTFP

**Changed**:
- This PR improves Fish Speech S2 Pro voice cloning TTFP.
- Previously, the Fish Speech voice cloning path built the full clone prompt in the API server:
- - resolve `ref_audio`

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2268](https://github.com/vllm-project/vllm-omni/pull/2268)** - Fix Fish Speech S2 Pro prompt handling for truncated audio & emotion tag

**Fixed**:
- This PR fixes the Fish Speech S2 Pro issues reported in #2248 by aligning prompt construction across serving, model-side structured clone prefill, and the offline example.
- It also closes several follow-up gaps found during review:
- - structured voice clone now uses the same prompt/tag protocol as text-only serving

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-26
**[PR #1438](https://github.com/vllm-project/vllm-omni/pull/1438)** - Streaming output

**Added**:
- Simple streaming output implementation for Qwene3TTS models for the latest disaggregated inference pipeline.
- one can test it with:
- ```

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-02
**[PR #1504](https://github.com/vllm-project/vllm-omni/pull/1504)** - Speed up diffusion model startup by multi-thread weight loading

**Added**:
- The weight loading time for large diffusion model are large, ~3min for QwenImage, ~5min for Wan2.2-I2V 14B. This PR reduce weight loading time by loading safetensors shards in parallel with a thread pool instead of sequentially.
- Helpful in:
- - Reduce wait time for CI or benchmarking board

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-26
**[PR #1509](https://github.com/vllm-project/vllm-omni/pull/1509)** - remove unused logger in omni_diffusion (#531)

**Changed**:
- Resolve #531 (the first item, which is the only item that still applies in the current codebase)
- As is explained in the comment of 531 (https://github.com/vllm-project/vllm-omni/issues/531#issuecomment-3964798019), other items are no longer applicable or have already been fixed in today's codebase
- - Test that the same amount of logging output is produced (i.e., expect the correct logging level and format have been already handled elsewhere)

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-26
**[PR #1522](https://github.com/vllm-project/vllm-omni/pull/1522)** - Use uds for zmq address if not set --stage-id

**Added**:
- Quik fix test failure:
- https://buildkite.com/vllm/vllm-omni/builds/3417/steps/waterfall?sid=019c99b1-9a45-48c5-9bfe-1776c5704c1c&tab=output
- Because ports are pre-allocated whose number are equal to stage number to used by zmq communication between api server and  engines. So there is a chance that they allocate same port for different stage, and port conflict happens then.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-28
**[PR #1554](https://github.com/vllm-project/vllm-omni/pull/1554)** - fix(qwen3-tts): fix Base ICL voice clone producing corrupted audio

**Fixed**:
- - Fix Base task ICL (in-context learning) voice clone mode producing mostly-silent/corrupted audio output
- - Root cause: `_estimate_prompt_len` did not pass `estimate_ref_code_len` callback, so prompt length estimation always fell back to 2048, causing a mismatch with model-side embeddings
- - Load codec frame rate from speech tokenizer config at init, and provide a callback that estimates `ref_code_len = ceil(audio_duration * codec_frame_rate)` from the resolved waveform

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-28
**[PR #1562](https://github.com/vllm-project/vllm-omni/pull/1562)** - Fix unexpected crash when init OmniDiffusion

**Fixed**:
- When init class of OmniDiffusion, it may cause unexpected crash since var "pipeline_class" may not be initialied.
- Fix unexpected crash when init OmniDiffusion.
- python examples/offline_inference/bagel/end2end.py --model /data/BAGEL-7B-MoT --modality text2img --prompts 'A cute cat'

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-02
**[PR #1566](https://github.com/vllm-project/vllm-omni/pull/1566)** - Import InputPreprocessor into Renderer

**Fixed**:
- Because https://github.com/vllm-project/vllm/pull/34510 this issue Move InputPreprocessor, so we need to fix.
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-03
**[PR #1609](https://github.com/vllm-project/vllm-omni/pull/1609)** - Fix filepath resolution for model with subdir and GLM-Image generation

**Fixed**:
- Resolves #1608
- This PR fixed the file path resolution in stage util for models which have `model_subdir` or `tokenizer_subdir`, and so that enabled GLM-Image generation with model ID.
- Offline generation of GLM-Image

**Updated in skill**:
- ✅ (auto-marked)

---


## 2026-03 - Week 1

---

*Maintained by vllm-omni-skills auto-update system*
*Archived every 4 weeks (aligned with vllm-omni release cycle)*
