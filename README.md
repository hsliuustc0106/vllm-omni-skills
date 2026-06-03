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
| [vllm-omni-tts-integration](skills/vllm-omni-tts-integration/) | Adding new TTS models and production speech-serving integrations |
| [vllm-omni-tts-bench-perf](skills/vllm-omni-tts-bench-perf/) | TTS serving perf benchmarks (RTF, TTFA/TTFP, throughput, concurrency sweeps, CI baselines) |
| [vllm-omni-tts-bench-acc](skills/vllm-omni-tts-bench-acc/) | TTS accuracy benchmarks (WER/CER, speaker SIM, UTMOS, codec/vocoder fidelity) |
| [vllm-omni-multimodal](skills/vllm-omni-multimodal/) | End-to-end omni-modality models (Qwen-Omni) |
| [vllm-omni-distributed](skills/vllm-omni-distributed/) | Distributed inference, disaggregation, Ray |
| [vllm-omni-perf](skills/vllm-omni-perf/) | Performance tuning, benchmarking, TeaCache, CPU offloading |
| [vllm-omni-quantization](skills/vllm-omni-quantization/) | Quantization (AWQ, GPTQ, FP8), memory reduction, quality verification |
| [vllm-omni-contrib](skills/vllm-omni-contrib/) | Contributing new models and development workflow |
| [vllm-omni-cicd](skills/vllm-omni-cicd/) | CI/CD pipelines for model deployments |
| [vllm-omni-review](skills/vllm-omni-review/) | PR review guidelines, checklists, and common pitfalls |
| [vllm-omni-release-note-writer](skills/vllm-omni-release-note-writer/) | Release note drafting guidance based on historical vLLM-Omni releases |
| [vllm-omni-recipe](skills/vllm-omni-recipe/) | Creating deployment guides for vLLM recipes repository |

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

### For Claude Code

Add this repository as a plugin marketplace:

```bash
/plugin marketplace add hsliuustc0106/vllm-omni-skills
```

Install a specific skill plugin, for example the review skill:

```bash
/plugin install vllm-omni-review@vllm-omni-skills
```

Claude Code's install command uses `plugin@marketplace`; after adding this repository, the marketplace name is `vllm-omni-skills`.

### For Codex

```bash
cp -r skills/* ~/.codex/skills/
```

## Usage

Once installed, skills activate automatically based on context. For example:

- Ask "How do I install vllm-omni?" and the **setup** skill activates
- Ask "Generate an image of a sunset" and the **image-gen** skill activates
- Ask "Set up distributed inference across 4 GPUs" and the **distributed** skill activates
- Ask "Review this PR for vllm-omni" and the **review** skill activates
- Ask "Draft the vLLM-Omni v0.19.0rc1 release notes" and the **release-note-writer** skill activates

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
├── .claude-plugin/
│   └── marketplace.json   # Claude Code marketplace manifest
├── docs/
│   ├── PRD.md              # Product requirements
│   ├── ARCHITECTURE.md     # Architecture design
│   └── TEST_DESIGN.md      # Test design
├── plugins/
│   └── vllm-omni-*/        # Claude Code plugin wrappers
│       ├── .claude-plugin/
│       │   └── plugin.json # Per-plugin manifest
│       └── skills/
│           └── vllm-omni-* # Symlink to canonical skill content
├── scripts/
│   └── validate_all.py     # Skill validation tool
└── skills/
    └── vllm-omni-*/        # 16 skill directories
        ├── SKILL.md         # Main skill instructions
        ├── references/      # Detailed reference docs
        └── scripts/         # Utility scripts (some skills)
```

## Version Variables

Skills use shell-style variables for version-dependent values. Set these before following any skill instructions:

```bash
export VLLM_VERSION="0.16.0"           # vLLM pip package version
export VLLM_OMNI_VERSION="v0.16.0"     # vLLM-Omni release / Docker tag
export PYTHON_VERSION="3.12"           # Python version
```

Check the [vllm-omni quickstart](https://github.com/vllm-project/vllm-omni#getting-started) for currently recommended versions.

## License

Apache License 2.0
