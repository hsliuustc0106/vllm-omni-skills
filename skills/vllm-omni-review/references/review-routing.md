# Review Routing

Use this file when the main review skill needs help deciding which domain skill, secondary skill, or optional specialized reviewer to involve.

## Prefix Routing

| PR Prefix | Primary Skill | Main Review Focus |
|-----------|---------------|-------------------|
| `[Image]`, `[ImageGen]` | `vllm-omni-image-gen` | Generation quality, diffusion settings, VRAM use |
| `[Video]`, `[VideoGen]` | `vllm-omni-video-gen` | Temporal consistency, throughput, frame pipeline |
| `[Audio]`, `[TTS]` | `vllm-omni-audio-tts` | Audio quality, latency, streaming behavior |
| `[Multimodal]` | `vllm-omni-multimodal` | Cross-modal correctness, shared processor behavior |
| `[Distributed]` | `vllm-omni-distributed` | Scaling, OmniConnector, multi-node invariants |
| `[Quantization]` | `vllm-omni-quantization` | Quality loss, loader compatibility, memory claims |
| `[Performance]` | `vllm-omni-perf` | Benchmarks, latency, throughput, cache tuning |
| `[Hardware]` | `vllm-omni-hardware` | Backend compatibility, device guards, platform assumptions |
| `[API]` | `vllm-omni-api` | OpenAI compatibility, request validation, response behavior |
| `[CI]` | `vllm-omni-cicd` | Pipeline correctness, deployment safety |
| `[Model]` | `vllm-omni-contrib` | Model integration patterns, tests, config wiring. Load [model-addition-checklist.md](model-addition-checklist.md) for dead-code scan, description/diff integrity, and copy-paste detection. |
| `[Bug]`, `[Bugfix]` | none by default | Use [tests-docs-checklist.md](tests-docs-checklist.md) for regression and coverage evidence |
| `[Refactor]` | none by default | Behavior preservation and invariant drift |
| `[Feature]` | none by default | Acceptance criteria, docs, tests. If the feature is a new model addition, load [model-addition-checklist.md](model-addition-checklist.md). |

## Multi-Skill Routing

Use one primary skill and add a secondary skill only when the diff crosses a true subsystem boundary.

| Scenario | Primary | Secondary |
|----------|---------|-----------|
| `[Performance]` + `[Distributed]` | `vllm-omni-perf` | `vllm-omni-distributed` |
| `[Performance]` + `[Model]` | `vllm-omni-perf` | `vllm-omni-contrib` |
| `[Model]` + `[Quantization]` | `vllm-omni-contrib` | `vllm-omni-quantization` |
| `[Feature]` + `[API]` | `vllm-omni-api` | none in most cases |
| `[Distributed]` + `[Hardware]` | `vllm-omni-distributed` | `vllm-omni-hardware` |

## Hardware Detection

Load `vllm-omni-hardware` when the diff shows backend-specific code even if the title prefix does not.

Patterns worth flagging:

- `is_npu`
- `is_cuda`
- `torch.cuda`
- `torch_npu`
- device-specific literals such as `cuda:0`

Review concerns:

- missing non-CUDA fallback paths
- platform-specific ops without guards
- hardcoded device assumptions
- memory handling that differs across platforms

## Delegation Triggers

Treat specialized reviewers as optional integrations. If the runtime has no `Agent(...)` or subagent tool, do the same checks manually and do not block on delegation.

| Trigger | Optional reviewer if available | Manual review focus |
|---------|--------------------------------|---------------------|
| new or changed `try/except` blocks | `pr-review-toolkit:silent-failure-hunter` | swallowed exceptions, empty fallbacks, missing logs, bad retry behavior |
| new `@dataclass` or `TypedDict` | `pr-review-toolkit:type-design-analyzer` | invariants, missing validation, unsafe defaults, optional-vs-required fields |
| test files changed | `pr-review-toolkit:pr-test-analyzer` | coverage gaps, unrealistic mocks, missing regression cases, weak assertions |
| `vllm_omni/entrypoints/` changes | `code-reviewer` | input validation, abuse resistance, unsafe parameter passthrough, bad error surfaces |
| config or validation code changes | `code-reviewer` | validation completeness, backward compatibility, edge cases, default handling |

Delegation limits:

- Max 2 delegated reviewers per PR
- Skip delegation for docs-only PRs
- Skip delegation for small PRs unless the risk is unusually high
- Delegated findings still count against the total comment budget

If no delegation tool exists:

- Apply the manual focus column directly during review
- Keep the same 5-comment budget
- Do not mention missing reviewer tooling in the PR unless the user explicitly asks

## Context Expansion Rules

Fetch more context when one of these is true:

- linked issue contains the actual acceptance criteria
- the diff changes shared infrastructure with prior art in adjacent PRs
- three lines of diff do not show cleanup, lifecycle, or invariant handling
- benchmark or quality claims reference data not included in the PR

Keep expansion bounded:

- 2-3 linked issues max
- 5 related PRs per important file max
- 3-5 code context fetches per review
