---
name: vllm-omni-cicd
description: Set up CI/CD pipelines for vLLM-Omni model deployments including Docker builds, automated testing, rolling updates, and deployment validation. Use when creating deployment pipelines, automating model serving updates, setting up Docker workflows, or configuring GitHub Actions for vllm-omni.
---

# vLLM-Omni CI/CD

## Overview

This skill covers CI/CD patterns for deploying and updating vLLM-Omni model serving infrastructure. It includes Docker image builds, automated testing, deployment validation, and rollback strategies.

## Docker Build

### Production Dockerfile

```dockerfile
FROM vllm/vllm-omni:$VLLM_OMNI_VERSION

ARG MODEL_NAME
ENV MODEL_NAME=${MODEL_NAME}

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -sf http://localhost:8091/health || exit 1

EXPOSE 8091

CMD ["sh", "-c", "vllm serve ${MODEL_NAME} --omni --port 8091 --host 0.0.0.0"]
```

Build and push:

```bash
docker build --build-arg MODEL_NAME=Tongyi-MAI/Z-Image-Turbo \
  -t my-registry/vllm-omni-z-image:latest .
docker push my-registry/vllm-omni-z-image:latest
```

### Pre-downloading Models

For faster container startup, bake model weights into the image:

```dockerfile
FROM vllm/vllm-omni:$VLLM_OMNI_VERSION

RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download('Tongyi-MAI/Z-Image-Turbo', local_dir='/models/z-image')"

ENV MODEL_PATH=/models/z-image
CMD ["sh", "-c", "vllm serve ${MODEL_PATH} --omni --port 8091 --host 0.0.0.0"]
```

## GitHub Actions Pipeline

### Basic CI

```yaml
name: vLLM-Omni CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pre-commit
      - run: pre-commit run --all-files

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --ignore=tests/gpu
```

### Build and Push Docker Image

```yaml
  docker:
    needs: [lint, test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}/vllm-omni:${{ github.sha }}
```

### GPU Integration Tests

```yaml
  gpu-test:
    runs-on: [self-hosted, gpu]
    needs: [lint]
    steps:
      - uses: actions/checkout@v4
      - run: |
          docker run --gpus all --rm \
            -v $(pwd):/workspace \
            vllm/vllm-omni:$VLLM_OMNI_VERSION \
            pytest /workspace/tests/gpu/ -v
```

## Deployment Strategies

### Rolling Update (Kubernetes)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-omni
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
        - name: vllm-omni
          image: my-registry/vllm-omni:latest
          readinessProbe:
            httpGet:
              path: /health
              port: 8091
            initialDelaySeconds: 120
            periodSeconds: 10
          resources:
            limits:
              nvidia.com/gpu: 1
```

### Blue-Green Deployment

1. Deploy new version alongside existing ("green" alongside "blue")
2. Run validation against green deployment
3. Switch traffic to green
4. Tear down blue after confirmation

```bash
# Deploy green
kubectl apply -f deployment-green.yaml

# Validate green
python scripts/validate_deployment.sh http://green-service:8091

# Switch traffic
kubectl patch service vllm-omni -p '{"spec":{"selector":{"version":"green"}}}'

# Teardown blue (after validation period)
kubectl delete deployment vllm-omni-blue
```

## Deployment Validation

After every deployment, validate:

1. **Health check**: `/health` returns 200
2. **Model loaded**: `/v1/models` returns expected model
3. **Inference works**: Send a test prompt, verify response
4. **Latency acceptable**: Response time within SLA

Use the validation script:

```bash
./scripts/validate_deployment.sh http://localhost:8091
```

## Rollback

### Kubernetes

```bash
kubectl rollout undo deployment/vllm-omni
```

### Docker Compose

```bash
docker compose pull  # pulls previous known-good tag
docker compose up -d
```

## Monitoring in CI/CD

- Check GPU memory usage post-deployment
- Monitor p50/p99 latency after rollout
- Set up alerts for health check failures
- Log model version and git SHA for traceability

## References

- For deployment pipeline templates, see [references/pipeline-templates.md](references/pipeline-templates.md)


## Recent Updates (Auto-generated)

**Source**: [[CI] Modify some CI test cases to run on L4 environment to reduce H100 resource usage.](https://github.com/vllm-project/vllm-omni/pull/1543)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Debug] Merge vllm pull 35368](https://github.com/vllm-project/vllm-omni/pull/1534)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Feature][Wan2.2] Speed up diffusion model startup by multi-thread weight loading](https://github.com/vllm-project/vllm-omni/pull/1504)

### Changes
- New feature: [Feature][Wan2.2] Speed up diffusion model startup by multi-thread weight loading

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Platform] Enable layerwise offload on all hardware](https://github.com/vllm-project/vllm-omni/pull/1492)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[XPU][NPU][ROCM] enable cpu_offloading flag for non_cuda](https://github.com/vllm-project/vllm-omni/pull/1488)


*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Test] Reduce Perf test case and fix modify stage config](https://github.com/vllm-project/vllm-omni/pull/1449)

### Changes
- Bug fix: [Test] Reduce Perf test case and fix modify stage config

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Bugfix] Race condition in MultiprocExecutor when concurent access to Scheduler](https://github.com/vllm-project/vllm-omni/pull/1448)

### Changes
- Bug fix: [Bugfix] Race condition in MultiprocExecutor when concurent access to Scheduler

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Qwen3TTS][Feat] Streaming output](https://github.com/vllm-project/vllm-omni/pull/1438)

### Changes
- New feature: [Qwen3TTS][Feat] Streaming output

*Updated: 2026-03-04*


## Recent Updates (Auto-generated)

**Source**: [[Doc][Test][Misc] ComfyUI test, more screenshot, and code cleaning](https://github.com/vllm-project/vllm-omni/pull/1435)


*Updated: 2026-03-04*
