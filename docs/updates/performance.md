# vllm-omni-perf 更新日志

> 最后更新: 2026-03-04
> [查看所有skills更新](../CHANGELOG.md) | [返回索引](README.md)

---

### 2026-02-26
**[PR #1468](https://github.com/vllm-project/vllm-omni/pull/1468)** - process request.num_cached_tokens if it equals to the initial value

**Fixed**:
- <!-- markdownlint-disable -->
- PLEASE FILL IN THE PR DESCRIPTION HERE ENSURING ALL CHECKLIST ITEMS (AT THE BOTTOM) HAVE BEEN CONSIDERED.
- <img width="908" height="214" alt="image" src="https://github.com/user-attachments/assets/c9cd8596-1fe9-405e-bfce-7f1e1b319e93" />

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
**[PR #1518](https://github.com/vllm-project/vllm-omni/pull/1518)** - Use pull through cache image for H100 pool

**Changed**:
- so they don't run into rate limit

**Updated in skill**:
- ✅ (自动标记)

---


## 2026-03 - Week 1

---

*本文件由 vllm-omni-skills auto-update 系统自动维护*
*每4周归档一次（对应vllm-omni的release周期）*
