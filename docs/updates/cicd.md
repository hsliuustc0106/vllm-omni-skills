# vllm-omni-cicd 更新日志

> 最后更新: 2026-03-04
> [查看所有skills更新](../CHANGELOG.md) | [返回索引](README.md)

---

### 2026-02-26
**[PR #1435](https://github.com/vllm-project/vllm-omni/pull/1435)** - ComfyUI test, more screenshot, and code cleaning

**Changed**:
- <!-- markdownlint-disable -->
- The commits in this PR do the following:
- - Add integration test for the ComfyUI plugin. It runs the online serving in a subprocess with mocked AsyncOmni to skip actual generation. The purpose is to guard any changes to the API layer and ensures that API editors also remember to update API calls in the ComfyUI plugin.

**Updated in skill**:
- ✅ (自动标记)

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


### 2026-02-26
**[PR #1448](https://github.com/vllm-project/vllm-omni/pull/1448)** - Race condition in MultiprocExecutor when concurent access to Scheduler

**Fixed**:
- <!-- markdownlint-disable -->
- This PR fix the race condition bug in `MultiprocExecutor` when both `collective_rpc` and `add_req` access into `Scheduler`.
- The test can expose the error and code fix is given in the PR

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-26
**[PR #1449](https://github.com/vllm-project/vllm-omni/pull/1449)** - Reduce Perf test case and fix modify stage config

**Fixed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- Recover H100 test cases and fix full test

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-27
**[PR #1488](https://github.com/vllm-project/vllm-omni/pull/1488)** - enable cpu_offloading flag for non_cuda

**Changed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- Current cpu_offloading is only open to CUDA. However, CPU offloading is also very useful feature due to memory capacity issue such as intel arc B60.

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-26
**[PR #1492](https://github.com/vllm-project/vllm-omni/pull/1492)** - Enable layerwise offload on all hardware

**Changed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- This PR replace `torch.cuda.` by `current_omni_platform.`, so that other platforms also can use layerwise offload feature.

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


### 2026-02-28
**[PR #1534](https://github.com/vllm-project/vllm-omni/pull/1534)** - Merge vllm pull 35368

**Changed**:
- Cherrypick the changes in vllm PR https://github.com/vllm-project/vllm/pull/35368 from @linyueqian .
- It helps #1367 #1519 and also may helps #1496 and #1447.
- Tested with:

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-28
**[PR #1543](https://github.com/vllm-project/vllm-omni/pull/1543)** - Modify some CI test cases to run on L4 environment to reduce H100 resource usage.

**Changed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- Modify some CI test cases to run on L4 environment to reduce H100 resource usage.

**Updated in skill**:
- ✅ (自动标记)

---


## 2026-03 - Week 1

---

*本文件由 vllm-omni-skills auto-update 系统自动维护*
*每4周归档一次（对应vllm-omni的release周期）*
