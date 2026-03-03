# Model-Specific Serving Configurations

## Image Generation Models

### Z-Image-Turbo (Tongyi-MAI/Z-Image-Turbo)

```bash
vllm serve Tongyi-MAI/Z-Image-Turbo --omni --port 8091
```
- Min GPU memory: 8 GB
- Default resolution: 1024x1024
- Supports: text-to-image

### Qwen-Image (Qwen/Qwen-Image)

```bash
vllm serve Qwen/Qwen-Image --omni --port 8091
```
- Min GPU memory: 24 GB
- Default resolution: 1024x1024
- Supports: text-to-image with multi-stage pipeline (AR + DiT)

### FLUX.1-dev (black-forest-labs/FLUX.1-dev)

```bash
vllm serve black-forest-labs/FLUX.1-dev --omni --port 8091
```
- Min GPU memory: 40 GB
- Default resolution: 1024x1024
- Supports: text-to-image

### Stable-Diffusion-3.5-medium

```bash
vllm serve stabilityai/stable-diffusion-3.5-medium --omni --port 8091
```
- Min GPU memory: 12 GB
- Supports: text-to-image

### BAGEL-7B-MoT (ByteDance-Seed/BAGEL-7B-MoT)

```bash
vllm serve ByteDance-Seed/BAGEL-7B-MoT --omni --port 8091
```
- Min GPU memory: 24 GB
- Supports: text-to-image, image understanding

### GLM-Image (zai-org/GLM-Image)

```bash
vllm serve zai-org/GLM-Image --omni --port 8091
```
- Min GPU memory: 24 GB
- Supports: text-to-image

## Video Generation Models

### Wan2.2-T2V-A14B

```bash
vllm serve Wan-AI/Wan2.2-T2V-A14B-Diffusers --omni --port 8091
```
- Min GPU memory: 48 GB
- Supports: text-to-video

### Wan2.2-I2V-A14B

```bash
vllm serve Wan-AI/Wan2.2-I2V-A14B-Diffusers --omni --port 8091
```
- Min GPU memory: 48 GB
- Supports: image-to-video

## Omni-Modality Models

### Qwen2.5-Omni-7B

```bash
vllm serve Qwen/Qwen2.5-Omni-7B --omni --port 8091
```
- Min GPU memory: 24 GB
- Supports: text, image, audio input; text, audio output

### Qwen3-Omni-30B-A3B-Instruct

```bash
vllm serve Qwen/Qwen3-Omni-30B-A3B-Instruct --omni \
  --tensor-parallel-size 2 --port 8091
```
- Min GPU memory: 48 GB (2x GPU recommended)
- MoE architecture: 30B total, 3B active
- Supports: text, image, audio, video input; text, audio output

## Audio / TTS Models

### Qwen3-TTS

```bash
vllm serve Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --omni --port 8091
```
- Min GPU memory: 8 GB
- Supports: text-to-speech with custom voice cloning

### MiMo-Audio-7B-Instruct

```bash
vllm serve XiaomiMiMo/MiMo-Audio-7B-Instruct --omni --port 8091
```
- Min GPU memory: 24 GB
- Supports: audio understanding, text-to-speech

### Stable-Audio-Open

```bash
vllm serve stabilityai/stable-audio-open-1.0 --omni --port 8091
```
- Min GPU memory: 8 GB
- Supports: text-to-audio (music, effects)
