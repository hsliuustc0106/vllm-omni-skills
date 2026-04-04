# vllm-omni-api Update Log

> Last updated: 2026-03-04
> [View all skills updates](../CHANGELOG.md) | [Back to index](README.md)

---

### 2026-03-29
**[PR #2297](https://github.com/vllm-project/vllm-omni/pull/2297)** - fix: handle Qwen-Image-Layered layered RGBA output for jpeg edits

**Fixed**:
- Root cause:
- /v1/images/edits already accepts output_format=jpeg, but the response encoding path did not normalize layered model outputs before saving. Qwen-Image-Layered produces layer images in RGBA, and Pillow cannot save RGBA directly as JPEG, so requests with output_format=jpeg failed with OSError: cannot write mode RGBA as JPEG, which surfaced as HTTP 500.
- Resolution:

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-30
**[PR #2298](https://github.com/vllm-project/vllm-omni/pull/2298)** - fix: return 400 for unsupported multi-image edits such as Qwen-Image-Layered

**Fixed**:
- **Root cause**
- `/v1/images/edits` accepted multiple input images without checking whether the current diffusion model actually supports multi-image inputs. For `Qwen-Image-Layered`, the pipeline only supports a single input image, so the request failed later inside the diffusion stage and was wrapped as `Diffusion generation failed`, which surfaced as an HTTP 500 instead of a client-side 400.
- **Fix**

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-30
**[PR #2329](https://github.com/vllm-project/vllm-omni/pull/2329)** - fix: handle Qwen-Image-Layered layered RGBA output for jpeg …

**Fixed**:
- …edits (#2297)
- (cherry picked from commit ecfee25c3b6f7ac799f78889af93245ed48e73e7)
- ---

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-30
**[PR #2334](https://github.com/vllm-project/vllm-omni/pull/2334)** - fix: validate layered image layers range

**Fixed**:
- Root cause:
- The `layers` parameter for Qwen-Image-Layered was not validated consistently at the API boundary. `/v1/images/edits` only rejected values `< 1`, while other invalid values such as `2` or `11` could still pass through. In addition, the diffusion chat path accepted `extra_body.layers` without any range check, and the JSON image request model did not enforce the backend-supported range either. As a result, out-of-range values could reach the layered pipeline, where extreme inputs could trigger excessive allocation and lead to OOM.
- Solution:

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-31
**[PR #2349](https://github.com/vllm-project/vllm-omni/pull/2349)** - fix: validate layered image layers range (#2334)

**Fixed**:
- (cherry picked from commit 1ca942999ab929af306297d8853d317b9c975896)
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-31
**[PR #2352](https://github.com/vllm-project/vllm-omni/pull/2352)** - fix: return 400 for unsupported multi-image edits such as Qw…

**Fixed**:
- …en-Image-Layered (#2298)
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-04-01
**[PR #2398](https://github.com/vllm-project/vllm-omni/pull/2398)** - Bagel KV-ready early forwarding and time step consistency for /v1/chat/completions

**Changed**:
- The /v1/chat/completions endpoint for disaggregated pipeline image generation only forwarded height and width from the request's extra_body to the diffusion stage sampling params, but ignored num_inference_steps. This caused the DiT stage to always fall back to the hardcoded default of 50 timesteps regardless of the client-specified value.
- In the disaggregated pipeline, the orchestrator previously waited for AR Stage-0 to fully finish decoding (up to max_tokens tokens) before forwarding the request to the DiT stage. However, the DiT stage only needs the prefill KV cache for conditioning and does not depend on decode outputs. This change makes the AR scheduler emit a kv_ready signal as soon as KV cache extraction completes, and the orchestrator immediately forwards the request to the DiT stage upon receiving this signal, eliminating the unnecessary wait for AR decode to finish. For Bagel with max_tokens=2048, this reduces disaggregated t2i end-to-end latency from ~22s to ~19.7s (matching single-stage baseline) and disaggregated i2i from ~35.8s to ~27.3s at 50 timesteps.
- ```bash

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-04-04
**[PR #2431](https://github.com/vllm-project/vllm-omni/pull/2431)** - Add online serving support, fix stage config, and add CI tests

**Added**:
- CosyVoice3 online serving via `/v1/audio/speech` was broken due to generic stage names colliding with other models and missing model type registration. This PR fixes the serving path end-to-end and adds CI coverage.
- - **Stage name collision**: Namespace `talker`/`code2wav` → `cosyvoice3_talker`/`cosyvoice3_code2wav` to avoid conflicts with other models
- - **cuDNN crash**: Set `enforce_eager=true` for code2wav stage — Conv1d in HiFiGAN has dynamic shapes incompatible with CUDA graphs

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-04-03
**[PR #2463](https://github.com/vllm-project/vllm-omni/pull/2463)** - Add two-stage TTS serving support

**Added**:
- - Add support for [k2-fsa/OmniVoice](https://huggingface.co/k2-fsa/OmniVoice), a zero-shot multilingual TTS model (600+ languages) using Qwen3-0.6B with iterative masked unmasking
- - Two-stage pipeline following CosyVoice3 pattern: Generator (32-step iterative unmasking → 8-codebook tokens) + Decoder (HiggsAudioV2 RVQ + DAC → 24kHz waveform)
- - Decoder verified bit-exact against reference HiggsAudioV2 implementation

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-04-04
**[PR #2475](https://github.com/vllm-project/vllm-omni/pull/2475)** - Rebase to vllm v0.19.0

**Changed**:
- This PR aims to rebase the vllm version that this repo relies on to v0.19.0
- Testing on release pipeline
- https://buildkite.com/vllm/vllm-omni-rebase/builds/713/steps/canvas

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
