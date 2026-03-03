# Qwen-Omni Architecture

## Qwen2.5-Omni

### Architecture

Qwen2.5-Omni is a unified multimodal model with:
- **Vision encoder**: Processes image and video frames
- **Audio encoder**: Processes audio waveforms
- **Language model**: 7B or 3B parameter Qwen2.5 backbone
- **Audio decoder**: Generates speech output tokens

The model processes all modalities through a shared transformer backbone, enabling cross-modal reasoning.

### Model Variants

| Variant | Parameters | Min VRAM | Best For |
|---------|-----------|----------|----------|
| Qwen2.5-Omni-7B | 7B | 24 GB | Production |
| Qwen2.5-Omni-3B | 3B | 12 GB | Edge / constrained environments |

### Stage Configuration

Qwen2.5-Omni uses a multi-stage pipeline internally:
1. **Encoding stage**: Processes multi-modal inputs
2. **Prefill stage**: Language model prefill
3. **Decode stage**: Autoregressive text generation
4. **Audio generation stage**: Generates audio output (if requested)

Custom stage config:
```yaml
stages:
  - name: "thinker"
    stage_type: "ar"
    stage_args:
      runtime:
        max_batch_size: 4
  - name: "talker"
    stage_type: "ar"
    stage_args:
      runtime:
        max_batch_size: 4
```

## Qwen3-Omni

### Architecture

Qwen3-Omni extends Qwen2.5-Omni with a Mixture-of-Experts (MoE) architecture:
- **Total parameters**: 30B
- **Active parameters per token**: 3B
- **Architecture**: `Qwen3OmniMoeForConditionalGeneration`

The MoE design provides the capacity of a 30B model with the inference cost of a 3B model.

### Serving

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni \
  --tensor-parallel-size 2 --port 8091
```

Requires at least 48 GB total GPU memory across tensor parallel workers.

### Expert Parallelism

For multi-node deployments, expert parallelism distributes MoE experts across devices:

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni \
  --tensor-parallel-size 2 \
  --port 8091
```

## Capabilities Comparison

| Capability | Qwen2.5-Omni | Qwen3-Omni |
|-----------|-------------|-----------|
| Text input | Yes | Yes |
| Image input | Yes | Yes |
| Audio input | Yes | Yes |
| Video input | Yes | Yes |
| Text output | Yes | Yes |
| Audio output | Yes | Yes |
| MoE | No | Yes |
| Min GPUs | 1 | 2 |
