# Model Integration Patterns

## Integration Architecture

Every model in vLLM-Omni is composed of one or more stages, connected through the pipeline framework:

```
Input → [Stage 1] → [Stage 2] → ... → [Stage N] → Output
```

## Pattern 1: Single-Stage Diffusion Model

For standalone DiT models (FLUX, SD3, Z-Image):

```python
class MyDiffusionPipeline:
    """Single-stage diffusion pipeline."""

    def __init__(self, model_config):
        self.model = load_model(model_config)

    def generate(self, prompts, **kwargs):
        latents = self.model.encode_prompts(prompts)
        for step in range(num_inference_steps):
            latents = self.model.denoise_step(latents, step, **kwargs)
        images = self.model.decode_latents(latents)
        return images
```

Stage config:
```yaml
stages:
  - name: "diffusion"
    stage_type: "diffusion"
    stage_args:
      runtime:
        max_batch_size: 1
```

## Pattern 2: Multi-Stage AR + Diffusion

For models with both language understanding and image generation (Qwen-Image, BAGEL):

```python
class MyARDiTPipeline:
    """Two-stage: AR encoder + DiT decoder."""

    def __init__(self, model_config):
        self.ar_model = load_ar_model(model_config)
        self.dit_model = load_dit_model(model_config)

    def generate(self, prompts, **kwargs):
        tokens = self.ar_model.encode(prompts)
        latent_tokens = self.ar_model.generate_latents(tokens)
        images = self.dit_model.decode(latent_tokens, **kwargs)
        return images
```

Stage config:
```yaml
stages:
  - name: "ar_encoder"
    stage_type: "ar"
    stage_args:
      runtime:
        max_batch_size: 4
  - name: "dit_decoder"
    stage_type: "diffusion"
    stage_args:
      runtime:
        max_batch_size: 1
```

## Pattern 3: Omni-Modality Model

For models that accept and produce multiple modalities (Qwen-Omni):

The omni pattern uses the "thinker-talker" architecture:
- **Thinker**: Processes multi-modal inputs and generates text
- **Talker**: Generates audio output from the thinker's hidden states

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

## Pattern 4: TTS Model

For text-to-speech models (Qwen3-TTS):

Single AR stage that generates audio tokens, followed by a vocoder for waveform synthesis:

```yaml
stages:
  - name: "tts"
    stage_type: "ar"
    stage_args:
      runtime:
        max_batch_size: 4
```

## Testing Checklist for New Models

- [ ] Basic generation produces valid output
- [ ] Different prompt types work (short, long, special chars)
- [ ] Output format is correct (images have pixels, audio has samples)
- [ ] GPU memory stays within expected bounds
- [ ] Batch generation works (if applicable)
- [ ] Online serving mode works (API server)
- [ ] Stage config defaults are sensible
- [ ] Model appears in supported models list
