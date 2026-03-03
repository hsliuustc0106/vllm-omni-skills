# Image Editing Workflows

## Supported Editing Models

| Model | HF ID | Capabilities |
|-------|-------|-------------|
| Qwen-Image-Edit | `Qwen/Qwen-Image-Edit` | Instruction-based editing |
| Qwen-Image-Edit-2509 | `Qwen/Qwen-Image-Edit-2509` | Enhanced editing |
| LongCat-Image-Edit | `meituan-longcat/LongCat-Image-Edit` | Instruction-based editing |

## Offline Editing

```python
from vllm_omni.entrypoints.omni import Omni

omni = Omni(model="Qwen/Qwen-Image-Edit")
outputs = omni.generate(
    prompt="Remove the person from the background",
    images=["input.jpg"],
)
outputs[0].request_output[0].images[0].save("edited.png")
```

## API-Based Editing

```bash
vllm serve Qwen/Qwen-Image-Edit --omni --port 8091
```

Send the source image as base64 in the request:

```python
import base64
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8091/v1", api_key="unused")

with open("input.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="Qwen/Qwen-Image-Edit",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": "Change the background to a beach scene"},
        ],
    }],
)
```

## Editing Prompts

Effective editing instructions:
- "Change the sky to a sunset"
- "Remove the text from the sign"
- "Make the car red instead of blue"
- "Add snow to the ground"
- "Convert to black and white, keeping only the flowers in color"

Avoid vague instructions like "make it better" or "improve the quality."
