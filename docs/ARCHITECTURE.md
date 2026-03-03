# vllm-omni-skills: Architecture Design

## Repository Layout

```
vllm-omni-skills/
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── TEST_DESIGN.md
├── scripts/
│   └── validate_all.py
└── skills/
    ├── vllm-omni-setup/
    │   ├── SKILL.md
    │   └── references/
    │       └── gpu-compatibility.md
    ├── vllm-omni-serving/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── model-configs.md
    │   │   └── scaling-guide.md
    │   └── scripts/
    │       └── health_check.py
    ├── vllm-omni-image-gen/
    │   ├── SKILL.md
    │   └── references/
    │       ├── flux-models.md
    │       ├── qwen-image.md
    │       └── image-edit.md
    ├── vllm-omni-video-gen/
    │   ├── SKILL.md
    │   └── references/
    │       └── wan-models.md
    ├── vllm-omni-audio-tts/
    │   ├── SKILL.md
    │   └── references/
    │       ├── qwen-tts.md
    │       └── mimo-audio.md
    ├── vllm-omni-multimodal/
    │   ├── SKILL.md
    │   └── references/
    │       └── qwen-omni.md
    ├── vllm-omni-api/
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── endpoints.md
    │   └── scripts/
    │       └── test_api.py
    ├── vllm-omni-distributed/
    │   ├── SKILL.md
    │   └── references/
    │       ├── disaggregation.md
    │       └── ray-execution.md
    ├── vllm-omni-perf/
    │   ├── SKILL.md
    │   ├── references/
    │   │   ├── teacache.md
    │   │   └── quantization.md
    │   └── scripts/
    │       └── run_benchmark.sh
    ├── vllm-omni-contrib/
    │   ├── SKILL.md
    │   └── references/
    │       └── model-integration.md
    ├── vllm-omni-hardware/
    │   ├── SKILL.md
    │   └── references/
    │       ├── cuda.md
    │       ├── rocm.md
    │       ├── npu.md
    │       └── xpu.md
    └── vllm-omni-cicd/
        ├── SKILL.md
        ├── references/
        │   └── pipeline-templates.md
        └── scripts/
            └── validate_deployment.sh
```

## Skill Design Pattern

Every skill follows the same three-layer structure:

### Layer 1: SKILL.md (always loaded on trigger)

- YAML frontmatter with `name` and `description`
- Concise workflow instructions (under 500 lines)
- References to deeper documentation via relative links

### Layer 2: references/ (loaded on demand)

- Model-specific guides, API docs, hardware details
- Keeps SKILL.md lean; agent reads only what is needed
- One level deep from SKILL.md (no nested references)

### Layer 3: scripts/ (executed, not loaded into context)

- Deterministic utility scripts for validation, health checks, benchmarking
- Python or shell scripts that produce structured output
- Saves tokens and ensures consistency

## SKILL.md Template

```markdown
---
name: skill-name
description: What this skill does. Use when [trigger scenarios].
---

# Skill Title

## Overview
Brief context (2-3 sentences).

## Prerequisites
What must be in place before using this skill.

## Workflow
Step-by-step instructions.

## Common Patterns
Frequently used configurations or code snippets.

## Troubleshooting
Common issues and resolutions.

## References
- For [topic], see [file.md](references/file.md)
```

## Dependency Graph

Skills are organized in tiers based on dependencies:

```
Tier 1 (Foundation)     Tier 2 (Core)        Tier 3 (Modality)     Tier 4+
─────────────────       ──────────────       ──────────────────     ────────
vllm-omni-setup    ──>  vllm-omni-serving    vllm-omni-image-gen   vllm-omni-distributed
vllm-omni-api      ──>  vllm-omni-hardware   vllm-omni-video-gen   vllm-omni-perf
                                              vllm-omni-audio-tts   vllm-omni-contrib
                                              vllm-omni-multimodal  vllm-omni-cicd
```

Tier 1 skills have no dependencies. Higher tiers may reference lower-tier skills but remain self-contained -- a developer can use any skill independently.

## Naming Conventions

- Skill directories: `vllm-omni-<topic>` (lowercase, hyphens)
- Reference files: `<topic>.md` (lowercase, hyphens)
- Scripts: `<verb>_<noun>.py` or `<verb>_<noun>.sh` (snake_case)
