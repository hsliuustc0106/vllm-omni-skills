# vLLM-Omni Skills 更新日志索引

## 快速导航

### 按Skill查看
- [Image Generation](image-gen.md) - 图像生成模型更新
- [Video Generation](video-gen.md) - 视频生成模型更新
- [Audio & TTS](audio-tts.md) - 音频和语音合成更新
- [API](api.md) - API端点和接口更新
- [Quantization](quantization.md) - 量化方法更新
- [Performance](performance.md) - 性能优化更新
- [Distributed](distributed.md) - 分布式推理更新
- [CI/CD](cicd.md) - CI/CD流程更新

### 按时间查看
- [2026-03 (Week 1)](./#2026-03) - 最新更新
- [2026-02](archive/2026-02.md) - 归档
- [2026-01](archive/2026-01.md) - 归档

---

## 最近更新 (最近7天)

### 2026-03-04
- **[image-gen]** HunyuanImage3 image editing support ([#1644](https://github.com/vllm-project/vllm-omni/pull/1644))

### 2026-03-03
- **[image-gen]** Fix filepath resolution for GLM-Image ([#1609](https://github.com/vllm-project/vllm-omni/pull/1609))

### 2026-03-02
- **[image-gen]** Fix load_weights error for HunyuanImage3.0 ([#1598](https://github.com/vllm-project/vllm-omni/pull/1598))
- **[video-gen]** Speed up diffusion model startup by multi-thread weight loading ([#1504](https://github.com/vllm-project/vllm-omni/pull/1504))
- **[audio-tts]** Qwen3TTS streaming output ([#1438](https://github.com/vllm-project/vllm-omni/pull/1438))

---

## 更新统计

| Skill | 本周更新 | 本月更新 | 总计 |
|-------|---------|---------|------|
| image-gen | 3 | 3 | 3 |
| api | 2 | 2 | 2 |
| audio-tts | 2 | 2 | 2 |
| video-gen | 1 | 1 | 1 |
| quantization | 1 | 1 | 1 |
| performance | 5 | 5 | 5 |

---

## 归档策略

**每4周归档一次**（对应vllm-omni的release周期）

- 当前周期: 2026-03-04 ~ 2026-04-01
- 下次归档: 2026-04-01

---

## 如何使用

### 查看特定skill的更新
```bash
# 查看图像生成相关的所有更新
cat docs/updates/image-gen.md

# 查看最近更新
head -50 docs/updates/api.md
```

### 查看整体变化
```bash
# 查看集中changelog
cat docs/CHANGELOG.md
```

---

*由 vllm-omni-skills auto-update 系统自动维护*
*归档周期: 4周 (与vllm-omni release对齐)*
