# vllm-omni-quantization Update Log

> Last updated: 2026-03-04
> [View all skills updates](../CHANGELOG.md) | [Back to index](README.md)

---

### 2026-04-01
**[PR #2337](https://github.com/vllm-project/vllm-omni/pull/2337)** - Add MUSA platform support for Moore Threads GPUs

**Added**:
- Add support for Moore Threads (MUSA) GPUs and expand the vllm-omni ecosystem.
- * Run [Qwen/Qwen2.5-Omni-3B](https://huggingface.co/Qwen/Qwen2.5-Omni-3B)
- * Run [Qwen/Qwen2.5-Omni-7B)](https://huggingface.co/Qwen/Qwen2.5-Omni-7B)

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-27
**[PR #1505](https://github.com/vllm-project/vllm-omni/pull/1505)** - Update installation instructions for vllm 0.16.0

**Changed**:
- As the vllm v0.16.0 is officially released, we do not need to use the prerelease to install.
- Tested on a new Dockerfile:
- ```Dockerfile

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-26
**[PR #1515](https://github.com/vllm-project/vllm-omni/pull/1515)** - fix offline text_to_image error from #1009

**Fixed**:
- fix #1512
- ```
- python examples/offline_inference/text_to_image/text_to_image.py   --model /workspace/models/black-forest-labs/FLUX.2-klein-4B     --prompt "a photo of a forest with mist swirling around the tree trunks. The word 'FLUX.2' is painted over it in big, red brush strokes with visible texture"   --height 768   --width 1360   --seed 42   --cfg-scale 4.0   --num-images-per-prompt 1   --num-inference-steps 40   --output outputs/flux2_klein_4b.png

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-03
**[PR #1539](https://github.com/vllm-project/vllm-omni/pull/1539)** - Enable curl retry aligned with openai

**Changed**:
- Add HTTP retry logic (max 3 attempts, 3s delay) to run_curl_multimodal_generation.sh for both Qwen2.5-Omni and Qwen3-Omni, fixing intermittent test failures caused by server-side TimeoutError when fetching remote media URLs.
- ```text
- tests/examples/online_serving/test_qwen2_5_omni.py::test_send_multimodal_request_003[omni_server0]

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-02-28
**[PR #1562](https://github.com/vllm-project/vllm-omni/pull/1562)** - Fix unexpected crash when init OmniDiffusion

**Fixed**:
- When init class of OmniDiffusion, it may cause unexpected crash since var "pipeline_class" may not be initialied.
- Fix unexpected crash when init OmniDiffusion.
- python examples/offline_inference/bagel/end2end.py --model /data/BAGEL-7B-MoT --modality text2img --prompts 'A cute cat'

**Updated in skill**:
- ✅ (auto-marked)

---


### 2026-03-02
**[PR #1598](https://github.com/vllm-project/vllm-omni/pull/1598)** - Fix load_weights error when loading HunyuanImage3.0

**Fixed**:
- Move some submodule load weights code of HunyuanImage3Pipeline to AutoWeightsLoader:load_weights, fix weights not initialized error.
- DiffusersPipelineLoader:load_weights added strictly weights load gap verification. Which reports bug when loading HunyuanImage3.0 mode. Move some submodule loading code to AutoWeightsLoader:load_weights to fix this bug.
- python examples/offline_inference/text_to_image/text_to_image.py --mode /data/HunyuanImage-3.0/ --prompt "A brown and white dog is running on the grass" --output output_image.png --num-inference-steps 50 --guidance-scale 5.0 --tensor-parallel-size 8 --seed 1234

**Updated in skill**:
- ✅ (auto-marked)

---


## 2026-03 - Week 1

---

*Maintained by vllm-omni-skills auto-update system*
*Archived every 4 weeks (aligned with vllm-omni release cycle)*
