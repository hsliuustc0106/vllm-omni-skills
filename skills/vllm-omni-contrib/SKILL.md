---
name: vllm-omni-contrib
description: Contribute to vLLM-Omni by adding new model support, fixing bugs, or improving features. Use when integrating a new model into vllm-omni, setting up a development environment, writing tests, or submitting pull requests to the vllm-omni project.
---

# Contributing to vLLM-Omni

## Overview

vLLM-Omni welcomes contributions including new model integrations, bug fixes, performance improvements, and documentation. This skill covers the development workflow, model integration process, and testing practices.

## Development Environment Setup

### Step 1: Fork and Clone

```bash
git clone https://github.com/<your-username>/vllm-omni.git
cd vllm-omni
```

### Step 2: Install in Development Mode

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install vllm==0.16.0 --torch-backend=auto
uv pip install -e ".[dev]"
```

### Step 3: Install Pre-commit Hooks

```bash
pre-commit install
```

## Code Organization

```
vllm_omni/
├── entrypoints/          # API entry points (Omni, AsyncOmni, API server)
├── engine/               # OmniRouter, pipeline orchestration
├── stages/               # Stage implementations (AR, Diffusion)
├── models/               # Model-specific implementations
├── connectors/           # OmniConnector for disaggregation
├── worker/               # Worker processes for distributed execution
└── utils/                # Shared utilities
```

## Adding a New Model

### Step 1: Identify Model Architecture

Determine which category your model falls into:
- **AR-only**: Text generation models (use existing vLLM model support)
- **Diffusion-only**: Image/video generation (DiT architecture)
- **Multi-stage**: AR + Diffusion pipeline (e.g., Qwen-Image)
- **Omni**: Full multi-modal input/output (e.g., Qwen-Omni)

### Step 2: Implement Model Class

Create a new file in `vllm_omni/models/`:

```python
# vllm_omni/models/my_new_model.py

from vllm_omni.stages.base import BaseStage

class MyNewModelPipeline:
    """Pipeline for MyNewModel."""

    def __init__(self, model_config, ...):
        ...

    def generate(self, prompts, ...):
        ...
```

### Step 3: Register the Model

Add your model to the model registry so vLLM-Omni can discover it:

```python
# In the appropriate registry file
SUPPORTED_MODELS = {
    ...
    "MyNewModelPipeline": ("my_new_model", "MyNewModelPipeline"),
}
```

### Step 4: Add Stage Configuration

Create a default stage config YAML:

```yaml
# vllm_omni/configs/my_new_model.yaml
stages:
  - name: "main"
    stage_type: "diffusion"  # or "ar"
    stage_args:
      runtime:
        max_batch_size: 1
```

### Step 5: Write Tests

```python
# tests/models/test_my_new_model.py
import pytest
from vllm_omni.entrypoints.omni import Omni

@pytest.mark.parametrize("prompt", [
    "a simple test image",
    "a red circle on white background",
])
def test_basic_generation(prompt):
    omni = Omni(model="my-org/my-new-model")
    outputs = omni.generate(prompt)
    assert len(outputs) > 0
    assert outputs[0].request_output[0].images is not None
```

### Step 6: Add Documentation

Add your model to `docs/models/supported_models.md` with:
- Architecture name
- Model name
- Example HF model ID
- Any special requirements

## Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/models/test_my_new_model.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=vllm_omni --cov-report=html
```

## Code Style

- Follow the existing code patterns in the repository
- Use type hints consistently
- Run pre-commit hooks before committing:
  ```bash
  pre-commit run --all-files
  ```

## Pull Request Process

1. Create a feature branch: `git checkout -b feat/add-my-model`
2. Make changes and write tests
3. Run tests locally: `pytest tests/`
4. Run linting: `pre-commit run --all-files`
5. Push and open a PR against `main`
6. Fill in the PR template with description and test results
7. Address review feedback

## Troubleshooting Development

**Import errors after install**: Reinstall with `uv pip install -e .`

**Tests fail with GPU errors**: Some tests require a GPU. Run with `pytest -m "not gpu"` to skip GPU tests.

**Pre-commit hook fails**: Run `pre-commit run --all-files` to see specific issues.

## References

- For detailed model integration patterns, see [references/model-integration.md](references/model-integration.md)
