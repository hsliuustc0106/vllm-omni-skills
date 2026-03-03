# FLUX Models

## FLUX.1-dev

- **HF ID**: `black-forest-labs/FLUX.1-dev`
- **Architecture**: Rectified flow transformer
- **Parameters**: ~12B
- **Min VRAM**: 40 GB
- **License**: Non-commercial (dev license)

```bash
vllm serve black-forest-labs/FLUX.1-dev --omni --port 8091
```

Recommended parameters:
- `num_inference_steps`: 50
- `guidance_scale`: 3.5
- Resolution: 1024x1024

## FLUX.2-klein

- **HF IDs**: `black-forest-labs/FLUX.2-klein-4B`, `black-forest-labs/FLUX.2-klein-9B`
- **Parameters**: 4B or 9B
- **Min VRAM**: 16 GB (4B), 32 GB (9B)

FLUX.2-klein is a smaller, faster variant designed for efficient inference.

```bash
vllm serve black-forest-labs/FLUX.2-klein-4B --omni --port 8091
```

Recommended parameters:
- `num_inference_steps`: 28
- `guidance_scale`: 3.0
- Resolution: 1024x1024

## Comparison

| Model | Speed | Quality | VRAM | License |
|-------|-------|---------|------|---------|
| FLUX.1-dev | Slower | Highest | 40 GB | Non-commercial |
| FLUX.2-klein-4B | Fast | Good | 16 GB | Check license |
| FLUX.2-klein-9B | Medium | Better | 32 GB | Check license |
