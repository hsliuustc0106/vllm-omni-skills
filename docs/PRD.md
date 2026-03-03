# vllm-omni-skills: Product Requirements Document

## Problem Statement

vLLM-Omni is a complex framework supporting omni-modality model inference across text, image, video, and audio. Its surface area spans multiple model families (30+ models), multiple hardware backends (CUDA, ROCm, NPU, XPU), distributed execution patterns, and both autoregressive and diffusion architectures. Developers face significant cognitive overhead when onboarding, integrating, or operating vLLM-Omni in production.

This skills collection provides contextual, step-by-step guidance that an AI coding assistant can surface automatically based on the developer's current task -- reducing time-to-first-inference and operational errors.

## Target Users

| Persona | Description | Primary Skills |
|---------|-------------|----------------|
| ML Engineer | Deploys models for production inference | setup, serving, api, perf, hardware, cicd |
| Application Developer | Integrates vLLM-Omni into products | api, image-gen, video-gen, audio-tts, multimodal |
| Researcher | Experiments with new models and modalities | setup, multimodal, perf, distributed |
| Contributor | Adds models or features to vllm-omni | contrib, setup, hardware |

## Skill Inventory

| # | Skill Name | Scope | Priority |
|---|------------|-------|----------|
| 1 | `vllm-omni-setup` | Installation, environment config, GPU/driver prerequisites | P0 |
| 2 | `vllm-omni-api` | OpenAI-compatible API client integration | P0 |
| 3 | `vllm-omni-serving` | Launching API servers, model config, scaling | P0 |
| 4 | `vllm-omni-hardware` | Hardware plugin system (CUDA, ROCm, NPU, XPU) | P1 |
| 5 | `vllm-omni-image-gen` | Image generation/editing (FLUX, SD3, Qwen-Image, GLM-Image, BAGEL) | P1 |
| 6 | `vllm-omni-video-gen` | Video generation (Wan2.2 T2V/I2V/TI2V) | P1 |
| 7 | `vllm-omni-audio-tts` | Audio generation and TTS (Qwen3-TTS, MiMo-Audio, Stable-Audio) | P1 |
| 8 | `vllm-omni-multimodal` | End-to-end omni-modality (Qwen2.5-Omni, Qwen3-Omni) | P1 |
| 9 | `vllm-omni-distributed` | Distributed inference, disaggregation (OmniConnector) | P2 |
| 10 | `vllm-omni-perf` | Performance tuning, benchmarking, TeaCache, quantization | P2 |
| 11 | `vllm-omni-contrib` | Contributing new models, development workflow | P2 |
| 12 | `vllm-omni-cicd` | CI/CD pipelines for vllm-omni deployments | P2 |

## Success Criteria

1. Each skill is self-contained with valid YAML frontmatter (`name`, `description`)
2. Each SKILL.md body is under 500 lines
3. Each skill follows progressive disclosure: essential workflow in SKILL.md, details in references/
4. All internal file references resolve to existing files
5. Scripts are syntactically valid and executable
6. Description fields include both WHAT (capabilities) and WHEN (trigger scenarios)

## Non-Goals

- Not a replacement for the official vllm-omni documentation
- Not an exhaustive API reference -- skills provide actionable workflows
- Not model training or fine-tuning guidance (vllm-omni is inference-only)

## Dependencies

- vLLM-Omni v0.16.0 (latest stable release)
- vLLM v0.16.0 (upstream dependency)
- Python 3.12
- Supported hardware: NVIDIA GPU (CUDA), AMD GPU (ROCm), Huawei NPU, Intel XPU
