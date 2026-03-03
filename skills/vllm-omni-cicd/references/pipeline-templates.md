# CI/CD Pipeline Templates

## Template 1: Simple Docker Deploy

For single-machine deployments:

```yaml
# .github/workflows/deploy.yml
name: Deploy vLLM-Omni
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: [self-hosted, gpu]
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t vllm-omni:${{ github.sha }} .
      - name: Stop old container
        run: docker stop vllm-omni || true
      - name: Start new container
        run: |
          docker run -d --name vllm-omni --gpus all \
            -p 8091:8091 vllm-omni:${{ github.sha }}
      - name: Wait for health
        run: |
          for i in $(seq 1 60); do
            if curl -sf http://localhost:8091/health; then
              echo "Server healthy"
              exit 0
            fi
            sleep 5
          done
          echo "Health check failed"
          exit 1
      - name: Validate
        run: python scripts/validate_deployment.sh http://localhost:8091
```

## Template 2: Kubernetes with ArgoCD

```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vllm-omni
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/vllm-omni-deploy
    path: k8s/
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: ml-inference
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Template 3: Multi-Model Deploy

For serving multiple models:

```yaml
# docker-compose.yml
services:
  image-gen:
    image: vllm/vllm-omni:v0.16.0
    command: vllm serve Tongyi-MAI/Z-Image-Turbo --omni --port 8091 --host 0.0.0.0
    ports:
      - "8091:8091"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  omni:
    image: vllm/vllm-omni:v0.16.0
    command: vllm serve Qwen/Qwen2.5-Omni-7B --omni --port 8092 --host 0.0.0.0
    ports:
      - "8092:8092"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  tts:
    image: vllm/vllm-omni:v0.16.0
    command: vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --omni --port 8093 --host 0.0.0.0
    ports:
      - "8093:8093"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - image-gen
      - omni
      - tts
```

## Template 4: Model Update Pipeline

For updating a deployed model to a new version:

```bash
#!/bin/bash
set -euo pipefail

NEW_MODEL="$1"
DEPLOY_NAME="vllm-omni"
NAMESPACE="ml-inference"

echo "Deploying model: $NEW_MODEL"

kubectl set env deployment/$DEPLOY_NAME MODEL_NAME="$NEW_MODEL" -n $NAMESPACE

echo "Waiting for rollout..."
kubectl rollout status deployment/$DEPLOY_NAME -n $NAMESPACE --timeout=600s

echo "Validating..."
SERVICE_URL=$(kubectl get svc $DEPLOY_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -sf "http://$SERVICE_URL:8091/health" || { echo "FAILED"; kubectl rollout undo deployment/$DEPLOY_NAME -n $NAMESPACE; exit 1; }

echo "Deployment successful"
```
