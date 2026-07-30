# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **skills collection** for vLLM-Omni (https://github.com/vllm-project/vllm-omni) -- a framework for omni-modality model inference supporting text, image, video, and audio. Skills are structured prompts that help AI assistants guide developers through vLLM-Omni workflows.

## Key Commands

```bash
# Validate all skills for structural correctness
python scripts/validate_all.py

# Validate a single skill
python scripts/validate_all.py skills/vllm-omni-setup/
```

## Skill Architecture

Each skill follows a three-layer structure:

1. **SKILL.md** (always loaded) -- YAML frontmatter (`name`, `description`) + concise workflow (max 300 lines)
2. **references/** (loaded on demand) -- Detailed guides, model-specific docs
3. **scripts/** (executed, not loaded) -- Python/shell utilities

### SKILL.md Template

```markdown
---
name: skill-name
description: What this skill does. Use when [trigger scenarios].
---

# Skill Title

## Overview
Brief context (2-3 sentences).

## Workflow
Step-by-step instructions.

## References
- For [topic], see [file.md](references/file.md)
```

## Naming Conventions

- Skill directories: `vllm-omni-<topic>` (lowercase, hyphens)
- Reference files: `<topic>.md` (lowercase, hyphens)
- Scripts: `<verb>_<noun>.py` or `<verb>_<noun>.sh` (snake_case)

## Skill Inventory (17 skills)

| Skill | Scope |
|-------|-------|
| `vllm-omni-setup` | Installation, environment config |
| `vllm-omni-api` | OpenAI-compatible API integration |
| `vllm-omni-serving` | API servers, model config, scaling |
| `vllm-omni-hardware` | CUDA, ROCm, NPU, XPU backends |
| `vllm-omni-image-gen` | FLUX, SD3, Qwen-Image, BAGEL |
| `vllm-omni-video-gen` | Wan2.2 T2V/I2V/TI2V |
| `vllm-omni-audio-tts` | Qwen3-TTS, MiMo-Audio |
| `vllm-omni-multimodal` | Qwen-Omni end-to-end |
| `vllm-omni-distributed` | Distributed inference, Ray |
| `vllm-omni-perf` | Performance tuning, TeaCache |
| `vllm-omni-quantization` | AWQ, GPTQ, FP8 quantization |
| `vllm-omni-contrib` | Contributing new models |
| `vllm-omni-cicd` | CI/CD pipelines |
| `vllm-omni-review` | PR review guidelines |
| `vllm-omni-recipe` | vLLM recipes documentation |
| `vllm-omni-tts-integration` | TTS integration patterns |
| `vllm-omni-nightly-local` | **H200** (SSH=in container) or **H800** (Slurm+docker); **`source /rebase/.venv/bin/activate`**; `nightly_jobs`; HTML via vllm-omni-test-report (nightly) |

## Validation Rules

The `validate_all.py` script enforces:

- SKILL.md must exist with valid YAML frontmatter
- Frontmatter must have `name` and `description` fields
- `name` must match directory name (lowercase, alphanumeric + hyphens)
- Description must include WHEN context (trigger scenarios)
- Body must be under 300 lines
- All markdown links to local files must resolve
- Reference files not linked from SKILL.md are flagged as orphaned
- Python/shell scripts must be syntactically valid

## Safe Change Rules

These files have cascade effects - modify with care:

| File | Impact |
|------|--------|
| `scripts/validate_all.py` | Affects validation of all skills |
| `CLAUDE.md` | Changes AI behavior for all skill work |
| `.github/PULL_REQUEST_TEMPLATE.md` | Affects all PR workflows |

When modifying these files, re-validate all skills and test with an actual agent.

## Do NOT Use

- **Do NOT** add new skills without corresponding `vllm-omni-` prefix
- **Do NOT** hardcode version numbers in skill content (use `$VLLM_VERSION` variables)
- **Do NOT** create circular references between skills
- **Do NOT** exceed 300 lines in any SKILL.md body

## Version Variables

Skills reference these shell variables for version-dependent commands:

```bash
export VLLM_VERSION="0.16.0"
export VLLM_OMNI_VERSION="v0.16.0"
export PYTHON_VERSION="3.12"
```

## PR Workflow

1. Use the PR template in `.github/PULL_REQUEST_TEMPLATE.md`
2. Run `python scripts/validate_all.py` before committing
3. Test skill with actual agent + LLM if modifying workflow content
4. Update `docs/CHANGELOG.md` for significant changes

### Definition of Done

A skill change is complete when:
- [ ] `python scripts/validate_all.py` passes
- [ ] SKILL.md under 300 lines
- [ ] All markdown links resolve
- [ ] Description includes "Use when" trigger context
