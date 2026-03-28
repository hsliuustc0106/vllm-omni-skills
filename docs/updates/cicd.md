# vllm-omni-cicd Update Log

> Last updated: 2026-03-04
> [View all skills updates](../CHANGELOG.md) | [Back to index](README.md)

---

### 2026-03-26
**[PR #2132](https://github.com/vllm-project/vllm-omni/pull/2132)** - L4 complete diffusion feature test for Z-Image

**Added**:
- This PR include the L4 test for Z-image.
- @fhfuih Please check whether there are other cases need to add.
- All test passed.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2137](https://github.com/vllm-project/vllm-omni/pull/2137)** - GLM-Image stage device isolation and t2i prompt preprocessing in Omni runtime

**Fixed**:
- This PR fixes two issues introduced during the entrypoints/runtime refactor for GLM-Image (AR + DiT):
- 1. **Stage device isolation bug (AR/Diffusion on wrong GPU)**
- - In async_omni_engine.py, diffusion stage initialization could leak process-level device visibility (`CUDA_VISIBLE_DEVICES`) and affect AR stage startup.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2138](https://github.com/vllm-project/vllm-omni/pull/2138)** - Fix examples tests error

**Fixed**:
- fix ci test case of tests/examples/online_serving/test_qwen3_omni.py in Omni Model Test with H100
- https://buildkite.com/vllm/vllm-omni/builds/5024/steps/canvas?sid=019d2108-dcc7-4a5d-b7f4-3ee1ddb88bde&tab=output
- for tests/examples/online_serving/test_qwen2.5_omni.py,

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-28
**[PR #2142](https://github.com/vllm-project/vllm-omni/pull/2142)** - Fix default guidance_scale from 1.0 to 4.0 and port GPU MoE ForwardContext fix from NPU

**Fixed**:
- - Fix default `guidance_scale` from 1.0 to 4.0 in `text_to_image.py`, which caused HunyuanImage3 to produce blurry, low-quality images #2127
- - Port GPU MoE ForwardContext fix from NPU (#2091) as defensive measure
- The `--guidance-scale` argument in `text_to_image.py` defaulted to **1.0**, effectively disabling classifier-free guidance. With `guidance_scale <= 1.0`, HunyuanImage3 skips the conditional/unconditional branch separation, resulting in blurry and abstract outputs. The recommended range is **4.0-5.0**.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2152](https://github.com/vllm-project/vllm-omni/pull/2152)** - Add TTS Text Preprocessing to Gradio Demo

**Added**:
- Add TTS Text Preprocessing to Gradio Demo

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2153](https://github.com/vllm-project/vllm-omni/pull/2153)** - Patch AsyncOmniEngine try_get_output hanging issues

**Changed**:
- Adds #1560 functionality post #1908 refactor. Fixes issues during init for #1346
- Added L1 test in `tests/engine/test_async_omni_engine_outputs.py`.
- Both passed.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2173](https://github.com/vllm-project/vllm-omni/pull/2173)** - remove default sampling parameters

**Fixed**:
- fix qwen2.5 CI bug
- ```
- pytest -sv ../tests/examples/online_serving/test_qwen2_5_omni.py -m "advanced_model" --run-level "advanced_model" > CI_bug.log 2>&1 &

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2174](https://github.com/vllm-project/vllm-omni/pull/2174)** - Add FLUX.2-dev online serving expansion test

**Added**:
- This PR adds L4 online serving expansion tests for FLUX.2-dev models
- test features:
- - Cache-DiT + CPU offload

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2176](https://github.com/vllm-project/vllm-omni/pull/2176)** - Resolve broken image issue when TP is enabled and no seed is provided.

**Fixed**:
- Fix issue #1713
- If no random generator or seed is provided, the latent will differ across TP ranks, causing the output image to break. To prevent this, we set a random seed (identical across all TP ranks but unique for each request) to ensure the latent remains consistent.
- A modified version of the code snippet in the issue

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2179](https://github.com/vllm-project/vllm-omni/pull/2179)** - remove benchmark/testing comparison w/ other frameworks

**Changed**:
- Signed-off-by: Huang, Zeyu <11222265+fhfuih@users.noreply.github.com>
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2191](https://github.com/vllm-project/vllm-omni/pull/2191)** - Skip test_sd3_expansion due to CI failure 5148

**Changed**:
- Skip test due to CI failure.  https://buildkite.com/vllm/vllm-omni/builds/5148/steps/canvas
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2192](https://github.com/vllm-project/vllm-omni/pull/2192)** - Revert " Add Qwen-tts test cases and unify the style of existing test cases"

**Added**:
- Reverts vllm-project/vllm-omni#1911

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2211](https://github.com/vllm-project/vllm-omni/pull/2211)** - qwen2.5-omni model cannot recognize the synthetic video

**Changed**:
- qwen2.5-omni model cannot recognize the synthetic video and audio data, need to update the test data to enable this test case
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2213](https://github.com/vllm-project/vllm-omni/pull/2213)** - Fix keyError: num_processed_tokens_delta

**Fixed**:
- Fix keyError: num_processed_tokens_delta
- pytest -sv test_qwen3_omni_expansion.py -m "advanced_model" --run-level "advanced_model"
- ```

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2217](https://github.com/vllm-project/vllm-omni/pull/2217)** - Fix dynamic function call on collective_rpc of DiffusionWorker

**Fixed**:
- This PR fix the bug on `collective_rpc` of `DiffusionWorker` where function is dynamic added on runtime through `worker_extension_cls`
- Extend the test on `tests/e2e/offline_inference/custom_pipeline/test_worker_extenstion.py`
- It should pass the test on external function call of WorkerExtension

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2219](https://github.com/vllm-project/vllm-omni/pull/2219)** - Add sd3 for test

**Added**:
- Add e2e tests for Stable Diffusion 3.5 medium model following the same pattern as Flux2 Klein tests. This PR adds test coverage for SD3.5 with commonly used acceleration features.
- Tests added:
- * cache_dit + cfg_parallel + tp (4 L4 cards)

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2230](https://github.com/vllm-project/vllm-omni/pull/2230)** - Increase diffusion initialization timeout from 600 to 700 seconds in online serving tests

**Changed**:
- Currently, there is a timeout issue when loading the Diffusion Images API LoRA E2E test case in CI.To fix it, increase diffusion initialization timeout from 600 to 700 seconds in online serving tests.
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2235](https://github.com/vllm-project/vllm-omni/pull/2235)** - fix Wan22 timeout and i2i accuracy threshold

**Fixed**:
- fix Wan22 timeout and i2i accuracy threshold
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2237](https://github.com/vllm-project/vllm-omni/pull/2237)** - fix_test_bagel_online

**Fixed**:
- Fix l3 testBagel_online.py
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2245](https://github.com/vllm-project/vllm-omni/pull/2245)** - Skip tests due to L3 CI failure

**Changed**:
- Skip CI due to L3 failure https://buildkite.com/vllm/vllm-omni/builds/5316/steps/canvas
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2263](https://github.com/vllm-project/vllm-omni/pull/2263)** - Modify conftest.py set unspecified parameters

**Fixed**:
- Modify conftest.py set unspecified parameters like num_outputs_per_prompt, width and height.
- ---
- <details>

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


### 2026-03-27
**[PR #2279](https://github.com/vllm-project/vllm-omni/pull/2279)** - Remove duplicate yaml entry

**Fixed**:
- Removes duplicate yaml entry for qwen2_5 omni XPU yaml configs introduced in #1851.
- ```
- pytest -v -s tests/e2e/offline_inference/test_qwen2_5_omni.py

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2132](https://github.com/vllm-project/vllm-omni/pull/2132)** - L4 complete diffusion feature test for Z-Image

**Added**:
- This PR include the L4 test for Z-image.
- @fhfuih Please check whether there are other cases need to add.
- All test passed.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2137](https://github.com/vllm-project/vllm-omni/pull/2137)** - GLM-Image stage device isolation and t2i prompt preprocessing in Omni runtime

**Fixed**:
- This PR fixes two issues introduced during the entrypoints/runtime refactor for GLM-Image (AR + DiT):
- 1. **Stage device isolation bug (AR/Diffusion on wrong GPU)**
- - In async_omni_engine.py, diffusion stage initialization could leak process-level device visibility (`CUDA_VISIBLE_DEVICES`) and affect AR stage startup.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2138](https://github.com/vllm-project/vllm-omni/pull/2138)** - Fix examples tests error

**Fixed**:
- fix ci test case of tests/examples/online_serving/test_qwen3_omni.py in Omni Model Test with H100
- https://buildkite.com/vllm/vllm-omni/builds/5024/steps/canvas?sid=019d2108-dcc7-4a5d-b7f4-3ee1ddb88bde&tab=output
- for tests/examples/online_serving/test_qwen2.5_omni.py,

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-28
**[PR #2142](https://github.com/vllm-project/vllm-omni/pull/2142)** - Fix default guidance_scale from 1.0 to 4.0 and port GPU MoE ForwardContext fix from NPU

**Fixed**:
- - Fix default `guidance_scale` from 1.0 to 4.0 in `text_to_image.py`, which caused HunyuanImage3 to produce blurry, low-quality images #2127
- - Port GPU MoE ForwardContext fix from NPU (#2091) as defensive measure
- The `--guidance-scale` argument in `text_to_image.py` defaulted to **1.0**, effectively disabling classifier-free guidance. With `guidance_scale <= 1.0`, HunyuanImage3 skips the conditional/unconditional branch separation, resulting in blurry and abstract outputs. The recommended range is **4.0-5.0**.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2152](https://github.com/vllm-project/vllm-omni/pull/2152)** - Add TTS Text Preprocessing to Gradio Demo

**Added**:
- Add TTS Text Preprocessing to Gradio Demo

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2153](https://github.com/vllm-project/vllm-omni/pull/2153)** - Patch AsyncOmniEngine try_get_output hanging issues

**Changed**:
- Adds #1560 functionality post #1908 refactor. Fixes issues during init for #1346
- Added L1 test in `tests/engine/test_async_omni_engine_outputs.py`.
- Both passed.

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2173](https://github.com/vllm-project/vllm-omni/pull/2173)** - remove default sampling parameters

**Fixed**:
- fix qwen2.5 CI bug
- ```
- pytest -sv ../tests/examples/online_serving/test_qwen2_5_omni.py -m "advanced_model" --run-level "advanced_model" > CI_bug.log 2>&1 &

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2174](https://github.com/vllm-project/vllm-omni/pull/2174)** - Add FLUX.2-dev online serving expansion test

**Added**:
- This PR adds L4 online serving expansion tests for FLUX.2-dev models
- test features:
- - Cache-DiT + CPU offload

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2176](https://github.com/vllm-project/vllm-omni/pull/2176)** - Resolve broken image issue when TP is enabled and no seed is provided.

**Fixed**:
- Fix issue #1713
- If no random generator or seed is provided, the latent will differ across TP ranks, causing the output image to break. To prevent this, we set a random seed (identical across all TP ranks but unique for each request) to ensure the latent remains consistent.
- A modified version of the code snippet in the issue

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2179](https://github.com/vllm-project/vllm-omni/pull/2179)** - remove benchmark/testing comparison w/ other frameworks

**Changed**:
- Signed-off-by: Huang, Zeyu <11222265+fhfuih@users.noreply.github.com>
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2191](https://github.com/vllm-project/vllm-omni/pull/2191)** - Skip test_sd3_expansion due to CI failure 5148

**Changed**:
- Skip test due to CI failure.  https://buildkite.com/vllm/vllm-omni/builds/5148/steps/canvas
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-25
**[PR #2192](https://github.com/vllm-project/vllm-omni/pull/2192)** - Revert " Add Qwen-tts test cases and unify the style of existing test cases"

**Added**:
- Reverts vllm-project/vllm-omni#1911

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2211](https://github.com/vllm-project/vllm-omni/pull/2211)** - qwen2.5-omni model cannot recognize the synthetic video

**Changed**:
- qwen2.5-omni model cannot recognize the synthetic video and audio data, need to update the test data to enable this test case
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2213](https://github.com/vllm-project/vllm-omni/pull/2213)** - Fix keyError: num_processed_tokens_delta

**Fixed**:
- Fix keyError: num_processed_tokens_delta
- pytest -sv test_qwen3_omni_expansion.py -m "advanced_model" --run-level "advanced_model"
- ```

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2217](https://github.com/vllm-project/vllm-omni/pull/2217)** - Fix dynamic function call on collective_rpc of DiffusionWorker

**Fixed**:
- This PR fix the bug on `collective_rpc` of `DiffusionWorker` where function is dynamic added on runtime through `worker_extension_cls`
- Extend the test on `tests/e2e/offline_inference/custom_pipeline/test_worker_extenstion.py`
- It should pass the test on external function call of WorkerExtension

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2219](https://github.com/vllm-project/vllm-omni/pull/2219)** - Add sd3 for test

**Added**:
- Add e2e tests for Stable Diffusion 3.5 medium model following the same pattern as Flux2 Klein tests. This PR adds test coverage for SD3.5 with commonly used acceleration features.
- Tests added:
- * cache_dit + cfg_parallel + tp (4 L4 cards)

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2230](https://github.com/vllm-project/vllm-omni/pull/2230)** - Increase diffusion initialization timeout from 600 to 700 seconds in online serving tests

**Changed**:
- Currently, there is a timeout issue when loading the Diffusion Images API LoRA E2E test case in CI.To fix it, increase diffusion initialization timeout from 600 to 700 seconds in online serving tests.
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-26
**[PR #2235](https://github.com/vllm-project/vllm-omni/pull/2235)** - fix Wan22 timeout and i2i accuracy threshold

**Fixed**:
- fix Wan22 timeout and i2i accuracy threshold
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2237](https://github.com/vllm-project/vllm-omni/pull/2237)** - fix_test_bagel_online

**Fixed**:
- Fix l3 testBagel_online.py
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2245](https://github.com/vllm-project/vllm-omni/pull/2245)** - Skip tests due to L3 CI failure

**Changed**:
- Skip CI due to L3 failure https://buildkite.com/vllm/vllm-omni/builds/5316/steps/canvas
- ---
- <details>

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-27
**[PR #2263](https://github.com/vllm-project/vllm-omni/pull/2263)** - Modify conftest.py set unspecified parameters

**Fixed**:
- Modify conftest.py set unspecified parameters like num_outputs_per_prompt, width and height.
- ---
- <details>

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


### 2026-03-27
**[PR #2279](https://github.com/vllm-project/vllm-omni/pull/2279)** - Remove duplicate yaml entry

**Fixed**:
- Removes duplicate yaml entry for qwen2_5 omni XPU yaml configs introduced in #1851.
- ```
- pytest -v -s tests/e2e/offline_inference/test_qwen2_5_omni.py

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
