# Changelog

All notable changes to vllm-omni-skills will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

**Archive Cycle**: Archived every 4 weeks (aligned with vllm-omni release cycle)

---

## [Unreleased] - 2026-03-04 ~ 2026-04-01

### Added
- [quantization] support sp for hunyuan ([#2163](https://github.com/vllm-project/vllm-omni/pull/2163))
- [quantization] support quantization for Flux Kontext ([#2184](https://github.com/vllm-project/vllm-omni/pull/2184))
- [quantization] support sp for hunyuan ([#2163](https://github.com/vllm-project/vllm-omni/pull/2163))
- [quantization] support quantization for Flux Kontext ([#2184](https://github.com/vllm-project/vllm-omni/pull/2184))
- [api] Streaming output ([#1438](https://github.com/vllm-project/vllm-omni/pull/1438))
- [cicd] Streaming output ([#1438](https://github.com/vllm-project/vllm-omni/pull/1438))
- [api] Speed up diffusion model startup by multi-thread weight loading ([#1504](https://github.com/vllm-project/vllm-omni/pull/1504))
- [cicd] Speed up diffusion model startup by multi-thread weight loading ([#1504](https://github.com/vllm-project/vllm-omni/pull/1504))
- [perf] Speed up diffusion model startup by multi-thread weight loading ([#1504](https://github.com/vllm-project/vllm-omni/pull/1504))
- [image-gen] HunyuanImage3 image editing support ([#1644](https://github.com/vllm-project/vllm-omni/pull/1644))
  - Conditional image preprocessing pipeline
  - VAE + ViT joint preprocessing
  - IPC serialization fix for numpy scalars
- [video-gen] Wan2.2 multi-thread weight loading ([#1504](https://github.com/vllm-project/vllm-omni/pull/1504))
- [audio-tts] Qwen3TTS streaming output capability ([#1438](https://github.com/vllm-project/vllm-omni/pull/1438))

### Changed
- [api] Improved IPC serialization for numpy scalars ([#1644](https://github.com/vllm-project/vllm-omni/pull/1644))

### Fixed
- [cicd] Fix examples tests error ([#2138](https://github.com/vllm-project/vllm-omni/pull/2138))
- [cicd] Fix keyError: num_processed_tokens_delta ([#2213](https://github.com/vllm-project/vllm-omni/pull/2213))
- [cicd] Fix examples tests error ([#2138](https://github.com/vllm-project/vllm-omni/pull/2138))
- [cicd] Fix keyError: num_processed_tokens_delta ([#2213](https://github.com/vllm-project/vllm-omni/pull/2213))
- [quantization] fix offline text_to_image error from #1009 ([#1515](https://github.com/vllm-project/vllm-omni/pull/1515))
- [api] Fix unexpected crash when init OmniDiffusion ([#1562](https://github.com/vllm-project/vllm-omni/pull/1562))
- [quantization] Fix unexpected crash when init OmniDiffusion ([#1562](https://github.com/vllm-project/vllm-omni/pull/1562))
- [quantization] Fix load_weights error when loading HunyuanImage3.0 ([#1598](https://github.com/vllm-project/vllm-omni/pull/1598))
- [image-gen] Fix filepath resolution for GLM-Image ([#1609](https://github.com/vllm-project/vllm-omni/pull/1609))
- [image-gen] Fix load_weights error for HunyuanImage3.0 ([#1598](https://github.com/vllm-project/vllm-omni/pull/1598))
- [audio-tts] Fix Qwen3-TTS code predictor crash ([#1619](https://github.com/vllm-project/vllm-omni/pull/1619))

---

## [2026-02] - 2026-02-01 ~ 2026-03-01

### Added
- 15 new model supports across image/video/audio generation
- 8 performance optimizations

### Fixed
- 23 bug fixes across all skills

[View detailed updates](updates/)

---

## Version Notes

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Fixed**: Bug fixes
- **Performance**: Performance optimizations
- **Documentation**: Documentation updates

---

## View by Skill

- [Image Generation](updates/image-gen.md)
- [Video Generation](updates/video-gen.md)
- [Audio & TTS](updates/audio-tts.md)
- [API](updates/api.md)
- [Quantization](updates/quantization.md)
- [Performance](updates/performance.md)
- [Distributed](updates/distributed.md)
- [CI/CD](updates/cicd.md)

---

*Last updated: 2026-03-04*
*Next archive: 2026-04-01 (vllm-omni release)*
