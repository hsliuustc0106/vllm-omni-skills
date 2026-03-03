# vllm-omni-skills

A collection of AI assistant skills for [vLLM-Omni](https://github.com/vllm-project/vllm-omni) -- a framework for efficient omni-modality model inference supporting text, image, video, and audio.

## Skills Index

| Skill | Description |
|-------|-------------|
| [vllm-omni-setup](skills/vllm-omni-setup/) | Installation, environment configuration, GPU/driver prerequisites |
| [vllm-omni-api](skills/vllm-omni-api/) | OpenAI-compatible API client integration |
| [vllm-omni-serving](skills/vllm-omni-serving/) | Launching API servers, model configuration, scaling |
| [vllm-omni-hardware](skills/vllm-omni-hardware/) | Hardware backends (CUDA, ROCm, NPU, XPU) |
| [vllm-omni-image-gen](skills/vllm-omni-image-gen/) | Image generation and editing (FLUX, SD3, Qwen-Image, BAGEL, etc.) |
| [vllm-omni-video-gen](skills/vllm-omni-video-gen/) | Video generation (Wan2.2 T2V/I2V/TI2V) |
| [vllm-omni-audio-tts](skills/vllm-omni-audio-tts/) | Audio generation and TTS (Qwen3-TTS, MiMo-Audio, Stable-Audio) |
| [vllm-omni-multimodal](skills/vllm-omni-multimodal/) | End-to-end omni-modality models (Qwen-Omni) |
| [vllm-omni-distributed](skills/vllm-omni-distributed/) | Distributed inference, disaggregation, Ray |
| [vllm-omni-perf](skills/vllm-omni-perf/) | Performance tuning, benchmarking, TeaCache, quantization |
| [vllm-omni-contrib](skills/vllm-omni-contrib/) | Contributing new models and development workflow |
| [vllm-omni-cicd](skills/vllm-omni-cicd/) | CI/CD pipelines for model deployments |

## Installation

### For Cursor IDE

Copy the `skills/` directory into your project:

```bash
cp -r skills/ /path/to/your-project/.cursor/skills/
```

Or symlink for shared use:

```bash
ln -s /path/to/vllm-omni-skills/skills/ ~/.cursor/skills/vllm-omni/
```

### For Claude / Codex

Copy skills into your Codex skills directory:

```bash
cp -r skills/* ~/.codex/skills/
```

## Usage

Once installed, skills activate automatically based on context. For example:

- Ask "How do I install vllm-omni?" and the **setup** skill activates
- Ask "Generate an image of a sunset" and the **image-gen** skill activates
- Ask "Set up distributed inference across 4 GPUs" and the **distributed** skill activates

Each skill provides step-by-step workflows, code examples, and references to detailed documentation.

## Validation

Run the validation script to check all skills for structural correctness:

```bash
python scripts/validate_all.py
```

Validate a single skill:

```bash
python scripts/validate_all.py skills/vllm-omni-setup/
```

## Project Structure

```
vllm-omni-skills/
├── README.md
├── LICENSE
├── docs/
│   ├── PRD.md              # Product requirements
│   ├── ARCHITECTURE.md     # Architecture design
│   └── TEST_DESIGN.md      # Test design
├── scripts/
│   └── validate_all.py     # Skill validation tool
└── skills/
    └── vllm-omni-*/        # 12 skill directories
        ├── SKILL.md         # Main skill instructions
        ├── references/      # Detailed reference docs
        └── scripts/         # Utility scripts (some skills)
```

## Compatible With

- vLLM-Omni v0.16.0
- vLLM v0.16.0
- Python 3.12

## License

Apache License 2.0
