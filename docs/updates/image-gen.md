# vllm-omni-image-gen 更新日志

> 最后更新: 2026-03-04
> [查看所有skills更新](../CHANGELOG.md) | [返回索引](README.md)

---

## 2026-03 - Week 1

### 2026-03-04
**[PR #1644](https://github.com/vllm-project/vllm-omni/pull/1644)** - Add edit preprocessor for HunyuanImage3

**Added**:
- ✨ HunyuanImage3 image editing support
- Conditional image preprocessing pipeline (VAE + ViT)
- IPC serialization fix for numpy scalars

**Updated in skill**:
- ✅ Supported Models 表格已更新
- ✅ Quick Start 已添加 image editing 示例
- ✅ Troubleshooting 已添加注意事项

---

### 2026-03-03
**[PR #1609](https://github.com/vllm-project/vllm-omni/pull/1609)** - Fix filepath resolution for model with subdir and GLM-Image generation

**Fixed**:
- Filepath resolution for models with subdirectories
- GLM-Image generation stability

---

### 2026-03-02
**[PR #1598](https://github.com/vllm-project/vllm-omni/pull/1598)** - Fix load_weights error when loading HunyuanImage3.0

**Fixed**:
- Weight loading error for HunyuanImage3.0
- Model initialization reliability

**Updated in skill**:
- ✅ Troubleshooting 章节已更新

---

## 归档

- [2026-02 归档](archive/2026-02.md)
- [2026-01 归档](archive/2026-01.md)

---

*本文件由 vllm-omni-skills auto-update 系统自动维护*
*每4周归档一次（对应vllm-omni的release周期）*
