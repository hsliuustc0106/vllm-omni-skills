---
name: vllm-omni-perf-opt
description: Diagnose and optimize vLLM Omni diffusion workloads, especially Wan/Qwen/Flux-style image and video generation. Use when Codex is asked to analyze profiling traces, choose parallel strategies, inspect torch profiler trace.json or trace.json.gz timelines, estimate optimization ROI, investigate GPU idle/free bubbles, compare USP/CFG/HSDP/VAE parallelism, or design operator/host/quantization optimizations for vLLM Omni.
---

# vLLM Omni Performance Optimization

Use this skill to run a disciplined optimization loop for vLLM Omni diffusion workloads. Keep two ideas separate: real performance baselines are collected with low overhead, while torch profiler traces are diagnostic artifacts and may distort latency.

## First Questions

Before proposing changes, ask for the optimization scene if it is not already known:

- GPU model, card count, topology, and whether NVLink is present.
- Model and pipeline, for example Wan2.2 I2V A14B.
- User workload: resolution, frames, steps, batch/concurrency, CFG scales, prompt/image inputs.
- Three runnable commands for each model/workload, or scripts that generate them:
  - **Server startup command**: exact `vllm serve` command, environment variables, model path, port, parallelism flags, profiler flags, and precision/compile settings.
  - **User request command**: exact single-request client command (for example curl or Python client) with fixed prompt/media/seed/size/steps. Use this to validate correctness and collect per-request stage timings.
  - **User benchmark command**: exact repeatable benchmark command or script with warmup count, measured iteration count, concurrency/batch policy, output directory, and summary format.
- Current enabled strategies: USP/SP, CFG parallel, HSDP/FSDP, VAE patch parallel, torch.compile, profiler options.
- Optimization target: latency, throughput, memory, cost, or quality-preserving speed.
- Precision/quality tolerance: bf16/fp8/quantization/sparsity/approximate attention allowed or not.

## Workflow

1. **Freeze the measurement protocol and commands.**
   - Before analyzing parallel strategies or traces, establish the three commands for the target model/workload: server startup, single user request, and user benchmark.
   - Prefer checked-in scripts or one-off shell scripts over free-form commands in chat. The scripts should make workload variables explicit, including model path, port/base URL, prompt/media inputs, resolution, frames, steps, seed, warmup, measured iterations, concurrency, and output path.
   - Measurement reports must preserve the concrete process, not just the final numbers. For each tested configuration, write down the server startup command, the user request command, the user benchmark command or polling loop, the final server response metrics, and the client-side timing/HTTP result.
   - Present all duration and latency values in **milliseconds (ms)** in tables and summaries. If an API returns seconds, convert to ms before reporting. Keep raw units only inside quoted raw logs or source snippets.
   - Keep profiler modes separate in the command set:
     - Baseline/benchmark commands should avoid torch profiler and stack collection.
     - Diagnostic commands may enable torch profiler after a baseline identifies a bottleneck.
   - If any of the three commands is missing, ask for it or create a proposed script before proceeding.
   - Make clear which command is authoritative for correctness validation and which command is authoritative for performance numbers.

2. **Collect a real baseline.**
   - Disable PyTorch profiler and stack collection.
   - Disable or fix torch.compile state so A/B is fair.
   - Avoid `--enforce-eager` for production-speed baselines unless eager is the target.
   - Prefer `--log-stats` and `--enable-diffusion-pipeline-profiler` for low-overhead stage timing. PR 3069 has the relevant metrics/log-stats changes; if local code does not include them, fetch or cherry-pick the minimal metrics changes rather than merging unrelated PR drift.
   - Run warmup requests and exclude first-request lazy init.

3. **Model the parallel strategy before testing.**
   - Estimate compute and communication for self-attention, cross-attention, FFN, CFG, VAE encode/decode, and HSDP.
   - Select a small candidate matrix rather than exhaustively testing everything.
   - Typical 2-card candidates: `USP=2`, `CFG=2`, `USP=1/HSDP on-off`, VAE parallel on-off if memory allows.
   - Typical 4-card candidates: `USP=4`, `CFG=2 x USP=2`, `USP=2 x HSDP`, VAE parallel on-off.
   - Typical 8-card candidates for official CFG-enabled video diffusion models:
     - Primary candidate: `CFG=2 x USP=4` with VAE patch parallel across all 8 ranks.
     - Compare against: `CFG=1 x USP=8` to test whether larger sequence parallel groups beat CFG branch parallelism.
     - Isolate VAE parallelism: keep the DiT strategy fixed and compare VAE patch parallel on/off or different VAE patch sizes.
     - If long-video `diffuse` remains dominant and Ulysses all-to-all is suspected, test a hybrid sequence strategy such as `CFG=2 x USP=2 x Ring=2`.
     - Test HSDP off only if the model fits without it; treat HSDP primarily as a memory strategy until A/B proves otherwise.
   - Prefer USP/SP for long video token sequences; prefer CFG parallel when CFG doubles transformer forwards and sequence length is modest.
   - Convert workload shape to latent/patch token counts before choosing candidates. For video models, record frames, latent frames, latent HxW, patch size, approximate token count, and which stages should scale with the token count.

4. **Search for the best parallel configuration.**
   - Start with a small matrix that answers one question per comparison:
     - `CFG parallel vs larger USP`: compare `CFG=2 x USP=world/2` against `CFG=1 x USP=world` for CFG-enabled workloads.
     - `VAE patch parallel value`: compare the best DiT strategy with VAE patch parallel enabled and disabled.
     - `HSDP cost`: compare HSDP on/off only when both configurations fit memory.
     - `Ulysses vs Ring`: test a Ring/Ulysses hybrid only after long-sequence `diffuse` is confirmed dominant.
   - For each configuration, create or record a stable config id, for example `A_cfg2_usp4_vaepp8_hsdp_tiling`.
   - For each config id, capture:
     - exact server command and environment variables,
     - observed distributed setup from logs, such as SP groups, CFG groups, HSDP shard/replicate sizes, VAE patch size,
     - exact request command for every scenario,
     - final server response metrics and client-side elapsed time,
     - output artifact paths and any failed/empty responses.
   - Use one warmup request per scenario, then at least three measured repeats for the shortlisted config. For exploratory matrix pruning, one measured request is acceptable only if the margin is large; label it as one-shot.
   - Compare configurations by stage, not only end-to-end latency. A configuration can improve `diffuse` while hurting `vae.decode`; record both effects.
   - Select the best config only after checking the target metric, dominant stages, memory headroom, and output correctness.

5. **Run targeted A/B tests.**
   - Change one variable per test.
   - Keep model, input, seed, request parameters, GPU placement, and warmup policy fixed.
   - Record latency, stage timings, memory, output quality, and logs.
   - Report comparison tables in ms. Include at least end-to-end client time, server `inference_time`, server stage generation time if available, `vae.encode`, `diffuse`, `vae.decode`, and peak memory.

6. **Collect diagnostic trace only after narrowing hypotheses.**
   - Use torch profiler for a small number of requests.
   - Run two separate diagnostic traces instead of mixing concerns:
     - **Operator/shape trace**: enable `torch_profiler_record_shapes=True` and keep stack collection disabled. Use this to rank CUDA kernels, NCCL collectives, attention/MLP/norm/RoPE work, and shape-specific hot operators.
     - **Host-stack trace**: enable `torch_profiler_with_stack=True` and normally keep shape collection disabled. Use this to map CPU/Python host gaps, synchronization points, scheduler paths, and request handling overhead.
   - Keep both trace commands and reports separate from baseline/benchmark commands. Torch profiler latency is diagnostic only and must not be used as the final latency claim.
   - Prefer profiling only the narrowed dominant scenario, for example the highest-resolution/video-length case where `diffuse` dominates.
   - If profiler endpoints are available, run one warmup request first, then call `/start_profile`, run one profiled request, and call `/stop_profile`. This keeps model initialization and warmup out of the diagnostic trace.
   - Start by analyzing rank 0 only. Expand to more ranks only if rank 0 suggests imbalance, unclear GPU idle/free bubbles, high NCCL wait, server timing mismatch, CFG branch imbalance, or USP group stragglers.
   - Diagnostic reports must be written to disk and preserve: server command, profiler config, warmup/request/polling commands, trace artifact paths, rank analyzed, analyzer output or summary, and the decision about whether additional ranks are necessary.
   - Analyze both rank-level balance and device-level free bubbles when additional ranks are opened.

7. **Analyze host, communication, and operators.**
   - Find GPU idle/free intervals and map each large gap to the enclosing CPU/Python code.
   - Separate real GPU idle from profiler overhead such as CUPTI `Command Buffer Full`.
   - Compare NCCL kernel time to user annotations; annotations can overcount nested intervals.
   - Rank operator work by total CUDA time and by repeated small-kernel launch count.

8. **Produce an optimization plan.**
   - Classify candidates as P0/P1/P2.
   - For each candidate, state necessity, expected benefit, implementation path, validation plan, and quality risk.
   - Do not implement high-risk operator rewrites before proving the operator is a bottleneck for the target shapes.
   - End the plan with a user-facing candidate selection table. The assistant
     should not automatically choose a risky optimization just because it is
     technically possible. Present the options clearly and let the user decide
     which item is worth implementing based on latency target, engineering
     budget, memory headroom, and quality tolerance.
   - Organize the plan by optimization layer, not by a flat list of ideas:
     - host/runtime optimization,
     - measurement/benchmark reliability,
     - parallelism and communication,
     - VAE encode/decode and media pre/post processing,
     - operator fusion and layout cleanup,
     - attention main-path optimization,
     - algorithmic, precision, or approximation changes.
   - For each layer, tie every candidate back to evidence from baseline
     metrics, diagnostic trace, source code, or output quality requirements.
     Do not list generic optimizations without a trace or workload reason.

## Priority Rules

- **P0:** low risk, likely useful, or required for trustworthy measurement. Examples: real baseline, warmup, targeted parallel A/B, disabling avoidable `empty_cache`, scheduler coefficient caching.
- **P1:** meaningful code changes with contained risk. Examples: cross-attention KV caching, VAE gather/broadcast reduction, AdaLayerNorm/RMSNorm/RoPE fusion after trace evidence.
- **P2:** high implementation or quality risk. Examples: FA to LA replacement, custom Triton/CUDA fused kernels, FP8/quantization, sparsity/Rainfusion-style acceleration.

Every implemented optimization needs A/B validation and quality regression. A/B means same workload and hardware before/after. Quality regression means checking generated image/video stability, artifacts, temporal flicker, and seed behavior when precision or approximate kernels change.

## Optimization Layers

After baseline, parallel-search, and diagnostic traces, summarize optimization
opportunities by layer. This is the core of the performance analysis: the goal
is to connect evidence to a scoped implementation and a validation plan.

### Host and Runtime Optimization

Purpose: remove CPU/Python stalls, synchronization points, allocator overhead,
and request-path overhead that leave GPU lanes empty.

Evidence to look for:

- High `idle_pct` or large `GAP` blocks in `trace_analyzer.py`.
- Host-stack trace lines such as `torch.cuda.empty_cache`,
  `cudaStreamSynchronize`, `cudaDeviceSynchronize`, Python locks, scheduler
  waits, image/video preprocessing, or repeated small allocation paths.
- Difference between client wall-clock time and server `inference_time_s`.

Typical candidates:

- Make avoidable `torch.cuda.empty_cache()` optional or guard it by memory
  headroom.
- Cache scheduler coefficients, timesteps, masks, or other tiny repeated CPU
  computations when the request shape/steps are fixed.
- Remove avoidable host-device synchronizations and blocking logging/stat calls.
- Move expensive preprocessing out of the critical path or cache fixed prompt,
  image, and transform work for benchmark scenarios.
- Ensure benchmark scripts record client-side elapsed time, HTTP status, output
  path, and server response metrics.

Priority guidance:

- Usually P0 when the change is measurement reliability or an obvious removable
  synchronization.
- Usually P1 when it changes scheduling, memory lifetime, or request execution
  order.

Validation:

- Re-run non-profiler baseline with same workload and seed.
- Confirm peak memory headroom if disabling cache cleanup.
- Confirm generated output exists and quality/seed behavior is unchanged.

### Parallelism and Communication Optimization

Purpose: choose the right decomposition for CFG branches, sequence tokens, model
weights, VAE tiles, and rank topology.

Evidence to look for:

- Baseline A/B across `CFG`, `USP/SP`, `Ring`, `HSDP/FSDP`, and VAE patch
  parallelism.
- Stage timing shifts: `diffuse`, `vae.encode`, `vae.decode`, and server
  end-to-end.
- NCCL kernel time from trace, not only `user_annotation` time.
- Rank imbalance across SP group ranks or CFG branch ranks.
- Memory headroom and OOM risk.

Typical candidates:

- `CFG=2 x USP=world/2` versus `CFG=1 x USP=world` for CFG-enabled models.
- VAE patch parallel on/off or patch size tuning.
- HSDP/FSDP on/off only if both configurations fit memory.
- Ulysses versus Ulysses+Ring only after long-sequence `diffuse` is confirmed
  dominant and all-to-all is suspected.
- Rank mapping/topology changes if all-rank traces show stragglers or NCCL wait.
- Buffer reuse or preallocation for FSDP/HSDP all-gather paths.

Priority guidance:

- P0/P1 for configuration-only changes with strong measured wins.
- P1 for buffer reuse or rank mapping changes.
- P2 for invasive distributed algorithm changes.

Validation:

- Measure by stage and memory, not only end-to-end.
- Use one-variable A/B with identical prompt/media/seed/shape/steps.
- When communication is suspected, compare rank0-3 in one USP group and rank0
  versus rank4 across CFG branches for `CFG=2 x USP=4`.

### VAE and Media Pipeline Optimization

Purpose: reduce encode/decode, tiling, split/gather, and media conversion time.

Evidence to look for:

- Large `vae.encode` or `vae.decode` in low-overhead stage timings.
- Host-stack gaps in VAE tile split, gather, merge, broadcast, or image/video
  transforms.
- VAE kernels or cuDNN convolution in operator trace.
- Whether every rank needs the final decoded tensor.

Typical candidates:

- Keep VAE patch parallel enabled when it has clear measured benefit.
- Reduce VAE gather/broadcast to only ranks that need the final media output.
- Reuse tile metadata, split buffers, or gather buffers.
- Evaluate bf16/autocast behavior for VAE only with visual quality checks.
- Avoid redundant image conversion, resize, or tensor construction in repeated
  benchmark runs.

Priority guidance:

- P0/P1 if VAE is a large share of the target workload or if a host gap is
  obvious and low risk.
- Lower priority when `diffuse` dominates and VAE is already patch-parallelized.

Validation:

- Compare `vae.encode`, `vae.decode`, server end-to-end, and peak memory.
- Check output video integrity, artifacts, flicker, and seed stability.

### Operator Fusion and Layout Cleanup

Purpose: reduce high-frequency small kernels, memory bandwidth pressure, layout
conversions, and launch overhead in transformer and VAE blocks.

Evidence to look for:

- Top operator tables showing many `aten::copy_`, `aten::cat`,
  `split_with_sizes_copy`, `aten::add`, `aten::mul`, `aten::div`, norm,
  activation, RoPE, or reshape/layout kernels.
- `ops_rankN.xlsx` `by_shape` sheet showing repeated small shapes inside the
  same block path.
- Trace lanes showing many short kernels between larger GEMM/attention kernels.
- Source code patterns with repeated elementwise chains or layout conversions.

Typical fusion targets:

- AdaLayerNorm / RMSNorm / LayerNorm plus scale/shift fusion.
- RoPE fusion with Q/K layout preparation when shapes are stable.
- Residual add, scale, gate, and elementwise chains.
- MLP gate/up/down cleanup, such as fusing activation and multiply around
  GEMM outputs when feasible.
- QKV projection and reshape/split/cat path cleanup.
- Attention pre/post layout cleanup to avoid unnecessary copies, cats, and
  splits around sequence parallel all-to-all.

Priority guidance:

- P1 when implemented with existing PyTorch/Triton/local helper patterns and
  validated against exact outputs or tolerances.
- P2 when it requires custom CUDA/Triton kernels, changes numerics, or touches
  attention math directly.

Validation:

- First prove the operator family is material for the target shape.
- Use non-profiler A/B for latency and stage timing.
- Use quality regression checks for generated video stability.
- Check compile behavior and graph breaks if using `torch.compile`.

### Attention Main-Path Optimization

Purpose: address the dominant self-attention cost when FlashAttention or other
attention kernels dominate CUDA time.

Evidence to look for:

- Operator trace where FlashAttention/SDPA kernels dominate total CUDA time.
- Attention shape from `ops_rankN.xlsx` `by_shape`, model code, or trace
  metadata.
- Whether attention cost scales with latent frames, latent H/W, patch size, or
  CFG duplication.
- Layout/copy/all-to-all work around attention.

Typical candidates:

- Verify the attention backend and shape are on the intended fast kernel path.
- Compare supported attention backends only with identical workload and quality
  settings.
- Reduce attention input size by safe model/config choices when allowed:
  latent resolution, frame count, patching, boundary ratio, or windowing.
- Remove avoidable layout conversions before/after attention.
- Reuse condition-side KV or other static inputs if the model structure allows.
- Consider custom kernels, sparse/window/linear attention, or approximation only
  after quality risk is accepted.

Priority guidance:

- P1 for backend/config/layout changes with preserved math.
- P2 for approximate attention, sparsity, custom kernels, or any change that can
  alter quality/temporal consistency.

Validation:

- Always include output quality and seed behavior checks.
- Compare `diffuse`, server end-to-end, peak memory, and attention kernel time
  in diagnostic traces if needed.

### Algorithmic, Precision, and Approximation Optimization

Purpose: reduce mathematical work or precision cost beyond local code cleanup.

Evidence to look for:

- A single operator family dominates even after low-risk runtime, parallel, and
  fusion work.
- Memory bandwidth or compute utilization suggests precision or quantization
  could matter.
- The user explicitly allows quality-preserving or approximate methods.

Typical candidates:

- FP8/quantization for transformer or selected projections.
- Sparsity or Rainfusion-style acceleration.
- Reduced steps, scheduler changes, distillation, or caching across frames.
- Approximate attention or linear attention.

Priority guidance:

- Usually P2 because quality, numerics, and implementation risk are high.

Validation:

- Requires strict A/B, visual quality review, temporal flicker checks, seed
  stability, and possibly human evaluation.

### Interpolation, Super-Resolution, and E2E Pipeline Optimization

Purpose: optimize the whole user-visible video product, not only the base
diffusion invocation. Some deployments trade base-model latency against
post-processing, interpolation, or super-resolution stages.

Evidence to look for:

- E2E latency breakdown across base generation, interpolation, super-resolution,
  encoding, storage, and response streaming.
- Fast/slow GPU or fast/slow stage analysis across multiple cards and pipeline
  stages.
- User quality target: resolution, FPS, temporal smoothness, and acceptable
  post-processing artifacts.

Typical candidates:

- Add or optimize a frame interpolation stage when it reduces required base
  model frames for the same perceived FPS.
- Add or optimize a super-resolution model when generating lower base
  resolution plus SR is faster for the target quality.
- Analyze E2E2 pipeline behavior: client request, service scheduling, diffusion,
  VAE/media, post-process, file write, and response.
- Identify fast/slow cards or stages and rebalance pipeline placement.

Priority guidance:

- P1 when using proven interpolation/SR components without changing diffusion
  math.
- P2 when quality risk is high or the pipeline adds significant operational
  complexity.

Validation:

- Measure E2E wall-clock, per-stage server timings, output FPS/resolution,
  artifacts, flicker, and user-visible quality.

### Successful Practice Examples

Use this section as a practical candidate library. These are not automatic
recommendations; each item still needs evidence, an implementation path, and
quality validation for the target model/workload.

| Layer | Practice example | Typical evidence | Priority | Validation focus |
|---|---|---|---|---|
| Operator / attention | Replace FA with LA when the target shape benefits | FA dominates CUDA time; LA is supported for the shape and quality tolerance | P2 | `diffuse` latency, quality, temporal stability |
| Operator / attention | Add LA preprocessing | LA chosen but preprocessing overhead or layout mismatch appears in trace | P1/P2 | preprocessing time, attention time, output quality |
| Operator / attention | LA for selected heads to reduce downclock/frequency pressure | GPU frequency or kernel behavior suggests full attention path causes downclock | P2 | frequency logs, latency, quality |
| Operator / cross-attn | Change cross-attention layout to BSND to remove transpose | Trace/source shows repeated transpose/copy around cross-attn | P1 | copy/transpose kernel reduction, exactness |
| Operator / fusion | Fuse AdaLayerNorm + LayerNorm path | Repeated norm + scale/shift + elementwise kernels | P1 | latency, numerical tolerance |
| Operator / fusion | Replace RMSNorm small kernels with fused RMSNorm | RMSNorm appears as many small kernels | P1 | latency, numerical tolerance |
| Operator / precision | Convert fp32 LayerNorm to bf16 where safe | fp32 norm path is visible and quality allows bf16 | P1/P2 | quality, stability, latency |
| Operator / RoPE | Move RoPE earlier into forward to avoid repeated prep | RoPE prep repeated per block/step or causes layout churn | P1 | kernel count, correctness |
| Operator / RoPE | Replace RoPE small kernels with fused RoPE | RoPE elementwise kernels are high-frequency | P1/P2 | latency, numerical tolerance |
| Operator / RoPE/layout | Remove small kernels before/after RoPE | Trace shows copy/reshape/cat/split around RoPE | P1 | layout kernel count, compile behavior |
| VAE / fusion | Replace VAE RMSNorm kernels | VAE norm kernels material in encode/decode trace | P1 | `vae.encode/decode`, video artifacts |
| Parallel / cross-attn | Make cross-attention non-parallel | Condition token count is small and SP overhead dominates cross-attn | P1 | `diffuse`, NCCL, correctness |
| Parallel / VAE | Enable/tune VAE parallelism | VAE encode/decode is large or OOM risk requires tiling/parallelism | P0/P1 | VAE time, memory, output correctness |
| VAE / precision | Convert VAE float path to bf16 | VAE float kernels are slow and bf16 quality is acceptable | P1/P2 | artifacts, flicker, seed stability |
| Host/runtime | Remove multiple `free` / `empty_cache` sections in pipeline | Host-stack trace shows repeated free/empty_cache gaps | P0/P1 | latency, peak memory, OOM safety |
| Host/VAE | Reduce VAE gather wait | Host-stack or all-rank trace shows gather wait around VAE | P1 | rank balance, VAE decode, output file correctness |
| Host/framework | Reduce omni framework scheduling overhead | Client vs server or trace shows request scheduling gaps | P1 | E2E latency, throughput |
| Communication | Communication ratio analysis | Need to distinguish NCCL kernel time from annotation overcount | P0 | kernel-level NCCL totals, rank comparison |
| Parallel / memory | HSDP on/off or HSDP buffer optimization | HSDP affects memory or all_gather allocation gaps | P1 | memory, latency, OOM risk |
| Sparse/quant | Rainfusion 2.0 style sparsity | Attention/DiT compute remains dominant and quality tolerance exists | P2 | quality, speed, stability |
| Sparse/quant | VAE decode quantization | VAE decode dominates target scenario and quality tolerance exists | P2 | artifacts, flicker, decode time |
| Interpolation | Frame interpolation optimization | Fewer generated frames plus interpolation meets FPS/quality target | P1/P2 | E2E latency, motion artifacts |
| Super-resolution | Add or optimize SR model | Lower base resolution plus SR may beat high-res base generation | P1/P2 | E2E latency, detail/artifact quality |
| E2E | E2E performance and fast/slow-card analysis | Multi-stage or multi-card service has stragglers | P0/P1 | per-stage time, per-rank time, user wall-clock |

### Optimization Plan Template

Use this table shape when reporting the next work items:

| Priority | Layer | Candidate | Evidence | Expected benefit | Implementation path | Validation | Quality risk |
|---|---|---|---|---|---|---|---|
| P0 | Host/runtime | Guard `empty_cache` | Host-stack gap points to `torch.cuda.empty_cache` | Small latency reduction, less idle | Add config/env guard | Non-profiler A/B, memory check | Low |
| P1 | Operator fusion | RMSNorm/AdaLayerNorm fusion | High-frequency norm/elementwise kernels | Lower launch/bandwidth overhead | Use existing fusion helper or targeted Triton | A/B + output check | Medium |
| P1/P2 | Attention | Attention layout/backend investigation | FA kernel dominates CUDA time | Potentially large | Inspect shapes/backend and remove layout copies | A/B + trace + quality | Medium/high |

Then present a short selection prompt using the same rows:

```text
Which candidate should we implement next?

1. P0 Host/runtime: guard empty_cache
   - Expected benefit: small but low-risk latency reduction.
   - Risk: possible memory increase/OOM if memory headroom is insufficient.

2. P1 Operator fusion: inspect by_shape and implement first norm/RoPE/layout fusion
   - Expected benefit: medium if high-frequency small kernels are confirmed.
   - Risk: numerical/compile/quality validation needed.

3. P1/P2 Attention: FA/LA/backend/layout investigation
   - Expected benefit: potentially large.
   - Risk: high quality and implementation risk.
```

If the user has not chosen an item, default to explaining tradeoffs and asking
which candidate to execute. Only proceed autonomously on low-risk P0 measurement
or instrumentation fixes.

## Analysis Helpers

### Torch profiler trace format

PyTorch exports Chrome trace / Perfetto-compatible JSON. The file is usually
named `trace_rankN.json` or `trace_rankN.json.gz`. The top-level payload is
normally:

```json
{
  "traceEvents": [
    {
      "name": "kernel or annotation name",
      "cat": "kernel",
      "ph": "X",
      "ts": 1234567890,
      "dur": 1234,
      "pid": 123,
      "tid": 456,
      "args": {}
    }
  ]
}
```

Key fields:

- `traceEvents`: list of timeline events. Some tools may emit a raw list
  directly; handle both forms.
- `name`: event name, such as a CUDA kernel, `nccl:all_to_all`,
  `pipeline_forward`, or a Python function path.
- `cat`: category. Common categories:
  - GPU work: `kernel`, `gpu_memcpy`, `gpu_memset`.
  - CPU/host work: `python_function`, `user_annotation`, `cpu_op`,
    `cuda_runtime`, `cuda_driver`.
- `ph`: event phase. Duration events are usually `X`; instant/counter/metadata
  events may not have useful duration.
- `ts`: start timestamp in microseconds.
- `dur`: duration in microseconds.
- `pid` and `tid`: process/thread lanes used by Chrome/Perfetto to draw the
  timeline.
- `args`: optional metadata such as shapes, stack info, stream ids, or labels.

Timeline interpretation:

- A horizontal bar is one event spanning `[ts, ts + dur]` on a `pid`/`tid` lane.
- GPU lanes contain kernels/memcpy/memset. CPU lanes contain Python functions,
  PyTorch ops, annotations, and CUDA runtime calls.
- A GPU free bubble is a time interval where no GPU event is active between two
  adjacent merged GPU busy intervals.
- User annotations can contain nested CUDA kernels. Do not treat annotation
  duration as kernel time without comparing it to the underlying `kernel`
  events. This is especially important for NCCL annotations.
- `Command Buffer Full` is profiler/CUPTI overhead and is not a model
  optimization target.

Use `scripts/trace_analyzer.py` for local torch profiler traces:

```bash
python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
  vllm_profile/.../trace_rank0.json.gz \
  vllm_profile/.../trace_rank1.json.gz \
  --min-gap-ms 5
```

Correct usage patterns:

```bash
# Analyze one rank first.
python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
  vllm_profile/.../trace_rank0.json.gz \
  --min-gap-ms 5 \
  --topn 20

# Compare several ranks when imbalance is suspected.
python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
  vllm_profile/.../trace_rank0.json.gz \
  vllm_profile/.../trace_rank1.json.gz \
  vllm_profile/.../trace_rank2.json.gz \
  vllm_profile/.../trace_rank3.json.gz \
  --min-gap-ms 5 \
  --topn 20

# Lower the threshold to inspect small CPU scheduling or VAE gaps.
python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
  vllm_profile/.../trace_rank0.json.gz \
  --min-gap-ms 1 \
  --topn 50
```

Parameter reference:

| Parameter | Required | Default | Meaning | When to use |
|---|---:|---:|---|---|
| `traces` | yes | none | One or more `trace.json` or `trace.json.gz` files. Each file is analyzed independently and printed as a separate section. | Pass one rank first, usually `trace_rank0.json.gz`. Pass multiple ranks when checking rank imbalance or comparing CFG/SP groups. |
| `--min-gap-ms` | no | `5.0` | Minimum GPU free-bubble duration to print, in milliseconds. The script computes merged GPU busy intervals from `kernel`, `gpu_memcpy`, and `gpu_memset`; gaps between those intervals above this threshold are reported. | Use `5` for normal profiling. Use `1` to inspect small host/VAE/scheduler gaps. Use `10` or `20` when traces are noisy and only large stalls matter. |
| `--topn` | no | `20` | Number of large gaps, top GPU/operator names, and top NCCL-like entries to print. | Use `20` for normal reports. Use `50` or higher when searching for many small kernels or many small idle gaps. |

Choose the command by question:

| Question | Command pattern | Read these output sections |
|---|---|---|
| Is this rank GPU-idle-bound? | `trace_analyzer.py trace_rank0.json.gz --min-gap-ms 5` | `gpu_span_s`, `busy_union_s`, `idle_union_s`, `idle_pct`. If `idle_pct` is low, prioritize kernel/operator work. If high, inspect `GAP` sections. |
| What code caused GPU idle bubbles? | `trace_analyzer.py trace_rank0.json.gz --min-gap-ms 1 --topn 50` on a host-stack trace | Each `GAP` block. Look at `prev`, `next`, and `in python_function ... file.py(line)` lines. |
| What are the hottest real GPU kernels? | `trace_analyzer.py trace_rank0.json.gz --min-gap-ms 5 --topn 30` on an operator/shape trace | `Top GPU/operator events by total duration`. Prefer `cat=kernel` style entries over annotations. |
| Is NCCL/communication the bottleneck? | Same command, optionally across all ranks | `Top NCCL-like events by category`. Compare `cat=kernel` or `cat=gpu_user_annotation` against total GPU span. Treat `cat=user_annotation` as an enclosing range that can overcount. |
| Is there rank imbalance? | Pass all relevant ranks in one command, for example rank0-3 for one USP group or rank0 and rank4 for CFG groups | Compare each rank section's `gpu_span_s`, `idle_pct`, top kernels, and NCCL totals. A straggler usually has longer span or other ranks show large idle gaps waiting near NCCL/sync events. |
| Are small VAE/scheduler gaps worth investigating? | `trace_analyzer.py trace_rank0.json.gz --min-gap-ms 1 --topn 50` on host-stack trace | `GAP` blocks containing VAE paths, scheduler paths, `empty_cache`, `cudaStreamSynchronize`, or allocation paths. |

Detailed example:

```bash
python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
  vllm_profile/wan22_A_720p_host_stack/20260429-094937_stage_0_diffusion_1777456177/trace_rank0.json.gz \
  --min-gap-ms 5 \
  --topn 20
```

Example output shape:

```text
== vllm_profile/.../trace_rank0.json.gz
events=2348143 gpu_events=136631 cpu_events=1738849
gpu_span_s=103.023 busy_union_s=102.504 idle_union_s=0.519 idle_pct=0.50
gaps_ge_5.000ms count=6 sum_s=0.125

GAP 63.872 ms ts=2377726779991->2377726843863
  prev kernel 0.034 ms void at::native::elementwise_kernel<...>
  next kernel 0.011 ms void at::native::vectorized_elementwise_kernel<...>
  in   python_function 60.748 ms <built-in function _cuda_emptyCache>
  in   python_function 60.761 ms torch/cuda/memory.py(268): empty_cache

Top GPU/operator events by total duration:
       320 total=   71.955s max=  447.996ms void cutlass::device_kernel<flash::...>
       640 total=    0.688s max=    8.460ms ncclDevKernel_SendRecv(...)

Top NCCL-like events by category:
       640 total=   53.888s max=  447.968ms cat=user_annotation nccl:all_to_all
       640 total=    0.688s max=    8.460ms cat=kernel ncclDevKernel_SendRecv(...)
```

How to read that example:

- `events`, `gpu_events`, `cpu_events`: confirms the trace contains both CPU
  and GPU events. If `gpu_events=0`, the profiler did not capture CUDA work or
  the trace is not the right file.
- `gpu_span_s=103.023`: the first-to-last GPU event window is about
  `103023 ms`.
- `busy_union_s=102.504`: after merging overlapping GPU kernels/memcpys, the
  GPU was busy for about `102504 ms`.
- `idle_union_s=0.519` and `idle_pct=0.50`: rank 0 has only about `519 ms`
  free bubble time, so it is not primarily host-idle-bound.
- `gaps_ge_5.000ms count=6 sum_s=0.125`: six printed gaps are at least
  `5 ms`, totaling about `125 ms`.
- A `GAP` block identifies the free bubble. `prev` is the last GPU event
  before the bubble, `next` is the first GPU event after it, and `in` lines are
  CPU/Python/user-annotation intervals covering the midpoint of the bubble.
  In the example, the largest bubble maps to `torch.cuda.empty_cache`.
- `Top GPU/operator events by total duration` is actual device work. In the
  example, FlashAttention is dominant.
- `Top NCCL-like events by category` includes both real kernels and enclosing
  annotations. In the example, `cat=user_annotation nccl:all_to_all` is
  `53.888s`, but the actual `cat=kernel ncclDevKernel_SendRecv` is only
  `0.688s`; do not use the annotation alone as communication time.

Recommended workflow with `trace_analyzer.py`:

1. Start with rank 0 on the operator/shape trace:

   ```bash
   python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
     vllm_profile/.../operator_shapes/.../trace_rank0.json.gz \
     --min-gap-ms 5 \
     --topn 20
   ```

   Decide whether the rank is kernel-bound, communication-heavy, or idle-heavy.

2. If `idle_pct` is high or a gap is unclear, run rank 0 on the host-stack
   trace:

   ```bash
   python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
     vllm_profile/.../host_stack/.../trace_rank0.json.gz \
     --min-gap-ms 1 \
     --topn 50
   ```

   Use `python_function` lines to map gaps to code paths.

3. If communication or imbalance is suspected, compare multiple ranks:

   ```bash
   python3 skills/vllm-omni-perf-opt/scripts/trace_analyzer.py \
     vllm_profile/.../trace_rank0.json.gz \
     vllm_profile/.../trace_rank1.json.gz \
     vllm_profile/.../trace_rank2.json.gz \
     vllm_profile/.../trace_rank3.json.gz \
     --min-gap-ms 5 \
     --topn 20
   ```

   Compare `gpu_span_s`, `idle_pct`, and NCCL kernel totals. For
   `CFG=2 x USP=4`, compare rank0-3 within one USP group; compare rank0 and
   rank4 to sample both CFG branches.

4. If the top kernels are clear but shapes matter, open `ops_rankN.xlsx` and
   inspect `by_shape`; the analyzer intentionally does not print tensor shapes.

What the analyzer reports:

- `events`, `gpu_events`, `cpu_events`: basic trace size and whether GPU/CPU
  data was captured. `events` is the total number of entries in
  `traceEvents`; `gpu_events` and `cpu_events` are filtered subsets, not a
  complete partition. The analyzer only counts GPU events whose `cat` is one of
  `kernel`, `gpu_memcpy`, or `gpu_memset`, and CPU events whose `cat` is one of
  `python_function`, `user_annotation`, `cpu_op`, `cuda_runtime`, or
  `cuda_driver`. Events with missing `ts`, missing `dur`, or `dur <= 0` are
  skipped for analysis, and metadata/counter/flow/instant/unknown-category
  events remain in the total `events` count. Therefore
  `events != gpu_events + cpu_events` is normal.
- `gpu_span_s`: wall-clock span from first GPU event start to last GPU event
  end.
- `busy_union_s`: union of all GPU kernel/memcpy/memset intervals after
  merging overlaps.
- `idle_union_s` and `idle_pct`: inferred GPU free bubble time. High values
  suggest host stalls, synchronization waits, scheduling gaps, or rank
  imbalance.
- `gaps_ge_Xms`: count and total duration of GPU free bubbles at or above the
  threshold.
- Each `GAP`: previous GPU event, next GPU event, and enclosing CPU/Python or
  user annotation events. Use this to map idle bubbles back to code paths.
- `Top GPU/operator events by total duration`: actual GPU kernel/memcpy/memset
  time, grouped by event name.
- `Top NCCL-like events by category`: NCCL-related names grouped by category.
  Prefer `cat=kernel` or `cat=gpu_user_annotation` for actual device work;
  treat `cat=user_annotation` as an enclosing range that may overcount nested
  time.

Analyzer limitations:

- It is a summary helper, not a full trace viewer. Use Perfetto or Chrome
  tracing for visual lane-level inspection.
- It merges all GPU streams to compute device-level busy/idle. It does not
  attribute overlap to individual streams.
- It does not parse tensor shapes directly from `args`; use `ops_rankN.xlsx`
  `by_shape` or PyTorch key averages for shape-grouped operator analysis.
- It does not prove quality or final latency. Re-test any optimization with
  non-profiler baseline/benchmark commands.

Read `references/optimization-playbook.md` when drafting the optimization table or comparing candidate techniques.

## vLLM Omni Heuristics

- Cross-attention usually should not use USP/SP when text/image condition token count is much smaller than latent video tokens. Confirm via trace; in Wan2.2 I2V, self-attention dominates cross-attention.
- VAE bf16/autocast is often worthwhile but requires visual quality checks.
- VAE patch parallel can help decode/encode but may add gather/merge/broadcast overhead. Check whether all ranks need the final decoded tensor.
- HSDP/FSDP is primarily a memory strategy. If the model fits without it, run an on/off latency comparison.
- Scheduler work can create small host/device gaps; cache tiny solve coefficients when timesteps/order are known.
- `torch.cuda.empty_cache()` can prevent OOM but creates synchronization/idle. Make it optional if memory headroom is sufficient.
- `Command Buffer Full` in profiler output is profiler overhead, not a model optimization target.
