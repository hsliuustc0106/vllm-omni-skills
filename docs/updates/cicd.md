# vllm-omni-cicd Update Log

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


### 2026-04-04
**[PR #2301](https://github.com/vllm-project/vllm-omni/pull/2301)** - : Magihuman support

**Changed**:
- Support [daVinci-MagiHuman](https://huggingface.co/princepride/daVinci-MagiHuman)
- ```
- """End-to-end test for MagiHuman pipeline via vLLM-Omni.

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


### 2026-04-01
**[PR #2337](https://github.com/vllm-project/vllm-omni/pull/2337)** - Add MUSA platform support for Moore Threads GPUs

**Added**:
- Add support for Moore Threads (MUSA) GPUs and expand the vllm-omni ecosystem.
- * Run [Qwen/Qwen2.5-Omni-3B](https://huggingface.co/Qwen/Qwen2.5-Omni-3B)
- * Run [Qwen/Qwen2.5-Omni-7B)](https://huggingface.co/Qwen/Qwen2.5-Omni-7B)

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
**[PR #2350](https://github.com/vllm-project/vllm-omni/pull/2350)** - fix test: use minimum supported layered output count

**Fixed**:
- fix CI
- ```
- __________________________________________________ test_layered_output_image_count[layers_guard_001_layers2] ___________________________________________________

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-31
**[PR #2351](https://github.com/vllm-project/vllm-omni/pull/2351)** - Fix 4 broken Qwen3-TTS async chunk unit tests

**Fixed**:
- - Fix 4 test failures in `test_qwen3_tts_async_chunk.py` that were introduced by source changes in PRs #1930, #1852, and #2104 without corresponding test updates
- - `test_flush_on_finish`: `finished` is now a plain `bool`, not a tensor; removed `.item()` call
- - `test_ic_load_change_mid_request`: IC is cached per request since #1930; updated expected emission frames

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


### 2026-03-31
**[PR #2354](https://github.com/vllm-project/vllm-omni/pull/2354)** - Update Whisper model loading to support multi-GPU configurations and optimize CUDA memory management

**Fixed**:
- fix timeout error in nightly CI, update Whisper model loading to support multi-GPU configurations and optimize CUDA memory management
- https://buildkite.com/vllm/vllm-omni/builds/5507/steps/canvas
- ---

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-04-01
**[PR #2378](https://github.com/vllm-project/vllm-omni/pull/2378)** - qwen3_tts chunk boundary handling logic in initial chunk (IC)

**Fixed**:
- Fix the initial chunk (IC) coverage logic in `qwen3_tts.py` to align with the correct behavior already implemented in `fish_speech.py`.
- Currently, `qwen3_tts.py` uses `<` and `chunk_size - 1` which constrains IC coverage to **strictly less than** `chunk_size`, while `fish_speech.py` uses `<=` and no `-1`, allowing IC to cover **up to** `chunk_size`. This mismatch causes `qwen3_tts.py` to miss the last IC chunk (e.g. `cs=25, ic=5`: IC emits at 5, 10, 15, 20 then jumps to normal phase emitting 21–45, skipping a 1–25 emit).
- **Proposed fix (only two lines changed):**

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


### 2026-04-01
**[PR #2401](https://github.com/vllm-project/vllm-omni/pull/2401)** - Tune GPU resources for test

**Changed**:
- There are test groups that does not require multi-gpu agent instance.
- mimo test uses custom ci configuration which only uses 1 GPU
- `str(Path(__file__).parent.parent / "stage_configs" / "mimo_audio_ci.yaml"),`

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
**[PR #2446](https://github.com/vllm-project/vllm-omni/pull/2446)** - Fix structured voice clone prefill conditioning

**Fixed**:
- This patch fixes the Fish Speech S2 Pro voice clone regression reported in #2394.
- The root cause was that the structured voice clone prefill path only rebuilt the prompt from semantic token IDs, but did not add the full DAC codebook embeddings back onto the reference-audio span. Decode-time `talker_mtp()` still used full codebook conditioning, so prefill and decode saw different conditioning signals and the cloned voice drifted or collapsed.
- This patch:

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-04-02
**[PR #2454](https://github.com/vllm-project/vllm-omni/pull/2454)** - Skip tests/e2e/online_serving/test_zimage_expansion.py due to issue #2435

**Changed**:
- Skip tests/e2e/online_serving/test_zimage_expansion.py due to issue #2435
- ---
- <details>

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
**[PR #1435](https://github.com/vllm-project/vllm-omni/pull/1435)** - ComfyUI test, more screenshot, and code cleaning

**Changed**:
- The commits in this PR do the following:
- - Add integration test for the ComfyUI plugin. It runs the online serving in a subprocess with mocked AsyncOmni to skip actual generation. The purpose is to guard any changes to the API layer and ensures that API editors also remember to update API calls in the ComfyUI plugin.
- - Code cleaning as per #1113 comments after it is merged

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


### 2026-02-26
**[PR #1448](https://github.com/vllm-project/vllm-omni/pull/1448)** - Race condition in MultiprocExecutor when concurent access to Scheduler

**Fixed**:
- This PR fix the race condition bug in `MultiprocExecutor` when both `collective_rpc` and `add_req` access into `Scheduler`.
- The test can expose the error and code fix is given in the PR
- This is bug description provide in test file

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-26
**[PR #1449](https://github.com/vllm-project/vllm-omni/pull/1449)** - Reduce Perf test case and fix modify stage config

**Fixed**:
- Recover H100 test cases and fix full test
- run in ci
- ---

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-27
**[PR #1488](https://github.com/vllm-project/vllm-omni/pull/1488)** - enable cpu_offloading flag for non_cuda

**Changed**:
- Current cpu_offloading is only open to CUDA. However, CPU offloading is also very useful feature due to memory capacity issue such as intel arc B60.
- This PR aims to provide a new way to decide if certain device should provide cpu-offloading capability or not.
- Verified on XPU

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-26
**[PR #1492](https://github.com/vllm-project/vllm-omni/pull/1492)** - Enable layerwise offload on all hardware

**Changed**:
- This PR replace `torch.cuda.` by `current_omni_platform.`, so that other platforms also can use layerwise offload feature.
- ```
- vllm serve Qwen/Qwen-Image --omni --enable-layerwise-offload

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


### 2026-02-28
**[PR #1534](https://github.com/vllm-project/vllm-omni/pull/1534)** - Merge vllm pull 35368

**Changed**:
- Cherrypick the changes in vllm PR https://github.com/vllm-project/vllm/pull/35368 from @linyueqian .
- It helps #1367 #1519 and also may helps #1496 and #1447.
- Tested with:

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-28
**[PR #1543](https://github.com/vllm-project/vllm-omni/pull/1543)** - Modify some CI test cases to run on L4 environment to reduce H100 resource usage.

**Changed**:
- Modify some CI test cases to run on L4 environment to reduce H100 resource usage.
- 1. test benchmark testcase and abort testcase
- ` /workspace/.venv/bin/python -m pytest -sv tests/benchmarks/test_serve_cli.py tests/engine/test_async_omni_engine_abort.py --html=report.html --self-contained-html`

**Updated in skill**:
- ✅ (auto-marked)

---


## 2026-03 - Week 1

---

*Maintained by vllm-omni-skills auto-update system*
*Archived every 4 weeks (aligned with vllm-omni release cycle)*
