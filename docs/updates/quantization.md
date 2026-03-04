# vllm-omni-quantization 更新日志

> 最后更新: 2026-03-04
> [查看所有skills更新](../CHANGELOG.md) | [返回索引](README.md)

---

### 2026-02-27
**[PR #1505](https://github.com/vllm-project/vllm-omni/pull/1505)** - Update installation instructions for vllm 0.16.0

**Changed**:
- As the vllm v0.16.0 is officially released, we do not need to use the prerelease to install.
- Tested on a new Dockerfile:
- ```Dockerfile

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-02-26
**[PR #1515](https://github.com/vllm-project/vllm-omni/pull/1515)** - fix offline text_to_image error from #1009

**Fixed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- fix #1512

**Updated in skill**:
- ✅ (自动标记)

---


### 2026-03-03
**[PR #1539](https://github.com/vllm-project/vllm-omni/pull/1539)** - Enable curl retry aligned with openai

**Changed**:
- Add HTTP retry logic (max 3 attempts, 3s delay) to run_curl_multimodal_generation.sh for both Qwen2.5-Omni and Qwen3-Omni, fixing intermittent test failures caused by server-side TimeoutError when fetching remote media URLs.
- ```text
- tests/examples/online_serving/test_qwen2_5_omni.py::test_send_multimodal_request_003[omni_server0]

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
**[PR #1598](https://github.com/vllm-project/vllm-omni/pull/1598)** - Fix load_weights error when loading HunyuanImage3.0

**Fixed**:
- Move some submodule load weights code of HunyuanImage3Pipeline to AutoWeightsLoader:load_weights, fix weights not initialized error.
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.

**Updated in skill**:
- ✅ (自动标记)

---


## 2026-03 - Week 1

---

*本文件由 vllm-omni-skills auto-update 系统自动维护*
*每4周归档一次（对应vllm-omni的release周期）*
