# Scaling and Load Balancing Guide

## Single-Node Multi-GPU

### Tensor Parallelism

Splits model layers across GPUs. Best for latency-sensitive workloads:

```bash
vllm serve <model> --omni --tensor-parallel-size <N>
```

Rules of thumb:
- Use TP=2 for 24-48 GB models on dual-GPU
- Use TP=4 for 48 GB+ models on quad-GPU
- TP size must evenly divide the number of attention heads

### Pipeline Parallelism

Splits model stages across GPU groups. Increases throughput at the cost of latency:

```bash
vllm serve <model> --omni \
  --tensor-parallel-size 2 \
  --pipeline-parallel-size 2
```

Total GPUs used = tensor_parallel_size x pipeline_parallel_size.

## Multi-Node Serving

For models too large for a single node, use Ray for distributed execution:

```bash
ray start --head --port=6379

# On worker nodes
ray start --address=<head-ip>:6379

# Launch serving
vllm serve <model> --omni \
  --tensor-parallel-size 8 \
  --port 8091
```

## Load Balancing Multiple Instances

### Nginx Configuration

```nginx
upstream vllm_backends {
    least_conn;
    server 127.0.0.1:8091;
    server 127.0.0.1:8092;
    server 127.0.0.1:8093;
}

server {
    listen 80;
    location /v1/ {
        proxy_pass http://vllm_backends;
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }
}
```

### Health-Based Routing

Configure health checks so the load balancer skips unhealthy instances:

```nginx
upstream vllm_backends {
    server 127.0.0.1:8091;
    server 127.0.0.1:8092;
    health_check uri=/health interval=5s fails=3;
}
```

## Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-omni
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: vllm-omni
          image: vllm/vllm-omni:${VLLM_OMNI_VERSION}
          command: ["vllm", "serve", "Tongyi-MAI/Z-Image-Turbo", "--omni", "--port", "8091", "--host", "0.0.0.0"]
          ports:
            - containerPort: 8091
          resources:
            limits:
              nvidia.com/gpu: 1
          readinessProbe:
            httpGet:
              path: /health
              port: 8091
            initialDelaySeconds: 60
            periodSeconds: 10
```

## Autoscaling Considerations

- Monitor GPU utilization and request queue depth
- Scale based on p99 latency thresholds
- Diffusion models have higher per-request GPU time than AR models
- Consider separate pools for different modalities
