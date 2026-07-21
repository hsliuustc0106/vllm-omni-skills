# Worker / Model-Runner Review Checklist

Load this when a PR touches `vllm_omni/worker/*` — the GPU worker (`base.py`, `gpu_ar_worker.py`,
`gpu_generation_worker.py`), the shared `OmniGPUModelRunner` base (`gpu_model_runner.py`), the AR /
generation runners (`gpu_ar_model_runner.py`, `gpu_generation_model_runner.py`), or the
memory/payload helpers — and the platform runner variants (`platforms/xpu/worker/*`). It encodes the
recurring findings from a function-by-function audit of this area so worker/runner PRs get consistent,
evidence-based review. Complements [architecture.md](architecture.md) (worker/stage system layout +
code-pattern review) and [blocker-patterns.md](blocker-patterns.md) (general merge blockers).

## Scope

**In scope:** `worker/base.py`, `worker/mixins.py`, `worker/gpu_model_runner.py` (shared base — a
cleanup here propagates to NPU for free), `worker/gpu_ar_model_runner.py`,
`worker/gpu_generation_model_runner.py`, `worker/gpu_ar_worker.py`, `worker/gpu_generation_worker.py`,
`worker/memory_utils.py`, `worker/gpu_memory_utils.py`, `worker/payload_span.py`,
`worker/sampling_utils.py`, `platforms/xpu/worker/*` (thin subclasses).

**Out of scope — do not review here:**
- `worker/omni_connector_model_runner_mixin.py` — owned by the OmniConnector maintainers; a runner PR
  may only *call* its public API. Flag misuse of the API, not its internals.
- `platforms/npu/worker/*` — diverged parallel hierarchy; route to the NPU model-runner-upgrade skill.

## How to use this in a review

Match depth to the PR, per the parent skill's calibration:
- **Default review** — run the **Priority-0 blocker scan** below, then apply lenses 1–9 only where the
  diff touches them. Surface blockers + a small set of high-signal findings; don't paste the full lens
  list.
- **Audit-depth review** (author asked for a line-by-line / audit pass, or the PR restructures the
  runner) — apply all lenses, produce a type-first rollup (Level 1 = error type, model-specific issues
  listed individually; Level 2 = `file:line — description`), and end with a suggested order.

**Evidence standard (hard rule):** never assert "dead" / "over-provisioned" / "never fires" from
reading. Confirm it — `grep` the field/flag/def across the repo, or run a small probe — and cite the
evidence. An unverified "this looks dead" is a non-blocking question, not a blocking finding.

**Per changed function, answer four things:** (a) what it does; (b) **upstream `GPUModelRunner` fork
body or OMNI delta?**; (c) **which model(s) require it?** (text-only pays nothing / it's for
talker-MTP / Fish-KV / …); (d) run the lenses.

## Priority 0 — worker/runner blocker patterns (check first)

Real correctness bugs outrank every cleanup. These patterns have all produced confirmed bugs in this
area; treat a match as blocking (REQUEST_CHANGES) until disproven:

- **Off-by-one on a size used as an index** — `x.clamp(max=size)` permits index `size`, OOB for a
  `size`-wide tensor (valid `0..size-1`). Almost always wants `size - 1`.
- **Early return shadowing a careful guard** — an unconditional `if not tokens: return` above a
  nuanced no-tokens block makes the latter unreachable, skipping the DP `_dummy_run(1)` that prevents
  a `coordinate_batch_across_dp` out-of-sync **hang**, and the `kv_connector_no_forward` path.
- **Silent wrong-data fallback** — on index-out-of-range returning `v[0]` (request 0's payload)
  instead of raising ships the wrong request's output with no signal.
- **In-place mutation of engine-shared state** — mutating `scheduler_output` (e.g. `custom_metadata`)
  without the `replace()`-copy the ngram path uses contaminates the engine-core process's copy.
- **`bool(value)` on a maybe-tensor** — raises "Boolean value of Tensor with more than one element is
  ambiguous" when the marker is a multi-element tensor/ndarray.
- **Jointly-constraining asserts** — `assert shape[0]==1` + `assert shape[0]==num_reqs` silently
  forces `num_reqs==1` (batching unsupported, no error); a sibling branch asserting only
  `len(list)==1` silently **misaligns** payloads for batches.
- **capture ≠ replay** — a `_dummy_run` copy missing the base's `has_preprocess` input branch captures
  the CUDA graph on `input_ids` while runtime feeds `inputs_embeds`.

### Confirmed-bug catalogue (recurrence check)

| Pattern | Known instance |
| --- | --- |
| `clamp(max=size)` off-by-one (OOB index) | AR `sample_tokens` prompt_token_ids vocab correction |
| Early return shadows no-tokens guard (DP hang + `kv_connector_no_forward` skipped) | generation `execute_model` |
| OOB fallback returns `v[0]` (wrong request's payload, silent) | AR `_unwrap_lists` in combined prefix-cache mm payload |
| In-place mutation of engine-shared `scheduler_output` | AR `execute_model` `custom_metadata` write (ngram path `replace()`-copies; this doesn't) |
| `bool(value)` on maybe-tensor crash | AR `_is_sparse_audio_marker` |
| Joint asserts force `num_reqs==1` / len-1 list misaligns batch | generation `sample_tokens` tensor + list branches |
| capture≠replay: `_dummy_run` copy missing `has_preprocess` branch | generation `_dummy_run` |
| Silent KV-transfer-metadata drop (bare `except Exception`) | AR `execute_model` `get_kv_transfer_metadata` |
| `None`-fallthrough to default sampler (wrong tokens for custom sampler) | AR `_sample` `prefer_model_sampler` |
| Stale memoization keyed before data arrives | AR `_request_needs_downstream_stage_payload` (`final_stage_id` None → caches True forever) |

## Review lenses

Each = *the tell* → *why it matters* → *fix direction*. Tags: **(blocker)** likely wrong behavior;
**(drift)** rebase/fork hazard; **(cleanup)** quality-only.

1. **Provenance — upstream fork vs OMNI delta.** *(drift)* Omni tells: `model_intermediate_buffer`,
   `make_omni_output`, `talker_mtp`, connector calls, `additional_information`, per-request
   `model.preprocess`/`postprocess`, hardcoded model names. Upstream tells: `query_start_loc`,
   `CpuGpuBuffer`, `num_scheduled_tokens`, `cudagraph`, `spec_decode`. **Unmarked deltas are silent
   fork drift** → mark `# OMNI:` so rebases notice; large fork bodies (`_update_states`, `_dummy_run`,
   `_preprocess`) need per-delta markers.

2. **Dead code (verify with grep).** *(cleanup)* Write-only fields (`_omni_last_model_output`);
   uncalled helpers (only the `def` matches — `_decode_and_store_request_payloads`); **dead extension
   points** — a `getattr(model, "supports_X", False)` flag *no model declares* (grep across
   `model_executor/models/`; if absent the branch is dead, e.g. `_sampled_token_ids_cpu_override`);
   dead defensive guards (`if callable(x)` where `x` is a tensor attr — `CpuGpuBuffer.cpu`); unused
   params.

3. **Deprecated / legacy remnants.** *(cleanup)* Back-compat aliases
   (`runtime_additional_information`), deprecated methods still called
   (`_update_additional_information`, `_merge_additional_information_update`), no-longer-used wire
   fields (`pooler_output`). `additional_information` is the canonical case — 3 names for one concept;
   converge on `model_intermediate_buffer` and retire aliases.

4. **Divergent duplicates (base ↔ AR ↔ generation).** *(drift)* Match method names across the 3 runner
   files; dangerous copies **differ subtly** (AR's trailing `-1` truncation in
   `_build_model_sampler_output_token_ids`; AR's `skips_...` short-circuit in
   `_sampling_metadata_for_model_sampler`; `_dummy_run` ~90% dup). **NamedTuple forks**
   (`ExecuteModelState`) can't be fixed by inheritance (you cannot extend a `typing.NamedTuple`) —
   guard with a field-parity test + `# OMNI:` on added fields; watch for silent field-order/type
   drift. Merge target: the `OmniModelState` hook (B-align).

5. **Model-specific logic in the generic runner (biggest theme — list each individually).**
   *(blocker for structure)* Tells: hardcoded arch strings / allowlists (`_OMNI_CONNECTOR_INIT_ARCHS`);
   `__class__.__name__ == "…"` checks (MiMoAudio); model-name-keyed behavior
   (`qwen3_tts_request_seed`, MammothModa2 `generated_len`, `thinker_reply_part_per_request`); the ~30
   `getattr(self.model, "<cap>", …)` probes; "Only required by X" comments. Fix: move behind a
   **model-declared capability on `OmniModelState`** (prefer `get_model_state_cls()` over any arch
   allowlist). See the model→feature map below.

6. **Wrapper vs raw model.** *(blocker)* `self.model` may be a `CUDAGraphWrapper`/`UBatchWrapper`.
   `isinstance` / `supports_X(...)` **must** use `self.get_model()` (unwraps); attr access via
   `__getattr__` is inconsistent. Rule: bind `model = self.get_model()` once per function, use it for
   both the check and the calls.

7. **Silent failures.** *(blocker)* `try/except Exception` that logs + drops (prompt_embeds decode
   swallowing a native tensor); `traceback.print_exc()` to stdout (use `logger.exception`); `getattr`
   fallbacks that silently skip real work. Ask: *does swallowing this hide a bug?* If yes → narrow the
   except / raise.

8. **Fork-fragility (rebase hazards).** *(drift)* `getattr` on `input_batch`/`model_config` internals
   (renamed attr → silent skip of backfill); `dataclasses.replace` assuming a type stays a dataclass;
   `self.pin_memory` coupling assuming base reads it; imports of upstream modules that may not exist
   (`vllm.compilation.breakable_cudagraph`); **stale over-provisioning** from an old upstream formula
   (FA3 `scheduler_metadata` resize) — verify empirically. Mark `# OMNI:`.

9. **Async / threading correctness.** *(blocker)* Event recorded but never waited
   (`async_copy_ready_event.record()` with no reader `.synchronize()`); daemon thread started in
   `__init__` (a background exception only surfaces if the result is awaited — at minimum
   `logger.exception` in the thread); `non_blocking=True` D2H copies read before completion;
   `torch.Event()` vs `torch.cuda.Event()` device backing. Ask: *who synchronizes, and does every
   reader wait first?*
   **Deferred-builder anti-patterns** (the async-omni-output cluster):
   - *Implicit snapshot boundary* — a closure capturing N locals encodes "everything the background
     thread reads must be frozen" as convention; a missed copy compiles fine and races. Fix: a frozen
     snapshot dataclass + one `capture()`.
   - *Cross-thread live-state access* — trace the whole deferred call graph for reads/writes of
     `self.requests` / `input_batch` / `model_intermediate_buffer` / connector state
     (`accumulate_full_payload_output`). Verify per site whether it's main-thread-only (check actual
     callers) or a real race.
   - *Dual-mode function with an implicit contract* — same body runs inline (sync) and on a thread
     (async) with mode differences as scattered `if`s. One builder + typed snapshot + mode asserts.
   - *Clone-before-copy* — CUDA-graph output buffers are reused by step N+1; payloads must be
     `clone()`d on the producing stream before the copy stream D2H-copies them.
   - *Eager side-effects can't defer* — postprocess that writes cross-step state
     (`hidden_states['last']`) must run on the hot path before snapshotting; only pure output assembly
     may defer (`postprocess_already_applied` travels in the snapshot).

10. **Implicit cross-phase state.** *(cleanup)* Instance attrs written in `_preprocess` and read later
    in `sample_tokens`/`_build_model_kwargs_extra` (`_omni_num_scheduled_tokens_np`) → should be
    `ExecuteModelState` fields, not mutable attrs. Base methods reaching **subclass-only** attrs via
    `hasattr` (`_downstream_payload_cache`) → layering smell; own the lifecycle in one place.

11. **Naming / docstring / type-hint drift.** *(cleanup)* Stale docstrings ("Align with v0.14.0");
    wrong return annotations (`-> dict` returns a tuple; `-> dict[str,dict]` returns `None`); `object`
    where `torch.Tensor` is meant; misleading names
    (`_collect_additional_information_for_prefill` that only overlays prompt_embeds). Report the
    ~120-method missing-docstring gap as ONE count-per-file sweep item, not per-line.

12. **Style / structure.** *(cleanup)* `*args/**kwargs` + `kwargs.pop(...)` + `if kwargs: raise` (make
    the signature explicit); imports-inside-functions — **distinguish** a deliberate lazy-dep (keep:
    `fish_kvcache_backend`, `breakable_cudagraph`) from a hoistable import-safe one (hoist:
    `ray_utils`, `RoutedExpertsLists`); over-long functions (`_update_states`, `_dummy_run` — split);
    inner-helper closures — make a method.

13. **Test coverage.** *(blocker for refactors)* Flag untested modules (`base.py`, `memory_utils.py`,
    `payload_span.py` have no direct unit tests) — "add L1 CPU characterization tests before any
    refactor that moves them." Everything in `tests/worker/` is CPU-only L1/L2.

14. **CUDA-graph capture == replay contract.** *(blocker)* The `has_preprocess` buffer path in
    `_dummy_run` must mirror `_preprocess` (same fixed persistent buffers, sized to
    `max(max_num_reqs, max_cudagraph_capture_size)`) — capture and replay must read the same
    addresses. Changing one without the other is a silent capture≠runtime bug.

15. **Subsystem-level redundancy.** *(investigate)* Beyond dead functions, ask whether a *whole
    subsystem's premise* still holds: find the original justification (git log / PR / rebase notes) →
    check whether upstream or the orchestrator has since absorbed it → list the investigation steps and
    the full removal cluster. Known candidates: cross-stage `prompt_embeds` decode+overlay (upstream
    `EngineCoreRequest` now carries `prompt_embeds` natively); per-process NVML memory estimation
    (only earns its keep if stages still init in parallel on one device — check orchestrator + measure
    init cost). File as "Possibly-redundant subsystem: `<name>`" with numbered questions.

16. **Misplaced code units.** *(cleanup)* Free functions and dataclasses defined inside a runner
    module (payload helpers `_to_cpu_contiguous`/`_ensure_tensor_values`, `ExecuteModelState`,
    `OmniAsyncGPUModelRunnerOutput`, snapshot types) → move to `utils` / a neutral data module. This
    also fixes backwards imports (generation runner importing from the AR runner).

## Model → feature map (which model needs the model-specific code)

| Feature / code | Gating signal | Model(s) |
| --- | --- | --- |
| talker-MTP (`_init_talker_mtp`, `_talker_mtp_forward`, AR graph capture) | `talker_mtp` / `talker` / `talker_mtp_graph_safe` | fish_speech, qwen3_tts, qwen3_omni |
| Fish-KV attention extensions (`_maybe_attach_attention_metadata_extensions`, `_prewarm_attention_capture_workspaces`) | Fish-KV attention backend | fish_speech (fish-kv) |
| GLM-Image M-RoPE decode fixup (`_calc_mrope_positions`, `_fixup_precomputed_mrope_decode_positions`) | `precomputed_mrope_decode` | glm_image_ar |
| Higgs `omni_query_start_loc` | `supports_omni_query_start_loc` | higgs_audio_v3_talker |
| MammothModa2 `generated_len` (image-grid EOL constraint) | (injected for all; only it consumes) | mammoth_moda2 |
| MiMoAudio req-infos | `__class__.__name__ == "MiMoAudioForConditionalGeneration"` | mimo_audio |
| `qwen3_tts_request_seed` | `sampling_params.extra_args["qwen3_tts_request_seed"]` | qwen3_tts |
| custom-sampler decode history (`_build_model_sampler_output_token_ids`, `_sampling_metadata_for_model_sampler`) | `prefer_model_sampler` | cosyvoice3, higgs_audio3, hunyuanimage3, glm_tts |
| force `output_token_ids` tracking (`_maybe_enable_output_token_ids_for_model_sampler`) | `prefer_model_sampler` + `logitsprocs_need_output_token_ids` | hunyuan_image3 |
| connector init allowlist (`_OMNI_CONNECTOR_INIT_ARCHS`) | `model_config.model_arch` ∈ set | Qwen3OmniMoe, Qwen2_5Omni, CovoAudio, MiMoAudioModel, Qwen3TTSTalker, Qwen3TTSCode2Wav, CosyVoice3, DyninOmni — **AR**: +IndexTTS2Talker; **generation**: +IndexTTS2S2MelDecoder (divergent!) |

## Capability-probe catalogue (~30 `getattr/hasattr(self.model, …)`)

B-align consolidates these scattered probes into a declared capability object on `OmniModelState`.
Inputs/preprocess: `has_preprocess`, `preprocess_batch`, `preprocess_decode_batch`,
`prepare_runner_inputs`. Outputs/postprocess: `has_postprocess`, `postprocess_uses_hidden_states`,
`postprocess_uses_multimodal_outputs`, `postprocess_uses_req_infos`, `make_omni_output`,
`gpu_resident_buffer_keys`. Sampler: `prefer_model_sampler`, `sample`,
`skips_model_sampler_output_token_history`, `logitsprocs_need_output_token_ids`. Positions:
`supports_mrope`, `precomputed_mrope_decode`, `supports_omni_query_start_loc`,
`supports_omni_decode_step_metadata`. Talker-MTP: `talker_mtp`, `talker`, `talker_mtp_graph_safe`,
`mtp_hidden_size`. Connector/lifecycle: `flush_pending_metadata`, `on_requests_finished`,
`get_kv_transfer_metadata`. **Dead:** `supports_sampled_token_ids_cpu_override` (no model declares it).

Rule of thumb: a probe reading a per-model flag → a capability that belongs on the model state; the
runner branching on the *result* to run model-specific code → that code belongs behind a hook.

## Upstream-vs-omni tells

- **Upstream vocabulary:** `query_start_loc`, `CpuGpuBuffer` (`.cpu`/`.gpu`/`.np` — `.cpu` is a tensor
  *attribute*, never callable), `num_scheduled_tokens`, `slot_mappings`, `spec_decode_metadata`,
  `cudagraph_mode`, `ExecuteModelState`, `inputs_embeds`, `_prepare_inputs`.
- **Omni deltas:** `model_intermediate_buffer` / `additional_information` /
  `runtime_additional_information` (same concept, 3 names), `make_omni_output`,
  `model.preprocess`/`postprocess`, `talker_mtp`, connector (`init_omni_connectors`,
  `_local_stage_payload_cache`), `OmniKVTransferManager`, `prompt_embeds` cross-stage overlay,
  hardcoded arch names, `request_token_spans`.

Two-phase flow is **both** upstream and omni: `execute_model()` runs forward, returns `None`, stores
an `ExecuteModelState`; `sample_tokens()` reads it, samples, builds output. Don't claim omni "added"
two-phase — it didn't.

## Async-omni-output pipeline (PR #4476; qwen3_omni-only)

Two async layers: upstream `AsyncGPUModelRunnerOutput` (sampled-token/logprobs non-blocking D2H) +
omni's `OmniAsyncGPUModelRunnerOutput` (defers the whole `OmniModelRunnerOutput` build to a daemon
thread). Flow in `sample_tokens`: ① CPU metadata snapshot (scheduler_output `replace()`-copy, req_ids,
query_start_loc clone) → ② gate `_should_use_async_omni_output()` (async scheduling ∧ no prefix cache
∧ no spec decode ∧ `async_chunk` ∧ no routed-experts ∧ model flags) → ③ **eager postprocess** on live
GPU tensors (talker writes `hidden_states['last']` for next step's preprocess — cannot defer) → ④ GPU
payload snapshot: clone-on-producing-stream → dedicated copy stream D2H → event → ⑤ construct async
output (starts daemon builder) → ⑥ `input_batch.set_async_sampled_token_ids(...)`. Engine
`get_output()` → join → re-raise background exception → `super().get_output()`. When reviewing changes
here, walk the deferred builder's whole call graph for the anti-patterns in lens 9.

## Known gotchas (verify against these)

- **`typing.NamedTuple` cannot be extended by inheritance** — why `ExecuteModelState` is a full copy,
  not a subclass. Reduce drift with composition or a field-parity test.
- **`CpuGpuBuffer.cpu` is a tensor attribute, never callable** — so `if callable(...)` guards on it
  are dead.
- **`get_model()` unwraps `CUDAGraphWrapper`/`UBatchWrapper`; `self.model` relies on `__getattr__`** —
  `isinstance`/`supports_X` must use `get_model()`.
- **FA3 `scheduler_metadata` size = `1 + round_up(batch,4)*4`, split-count-independent** (verified by
  real run) — omni's resize to `max_num_seqs*max_num_splits+1` is a stale v0.16 over-provision (~10×).
- **`torch.Event()` may be CPU-backed**; upstream async output uses `torch.cuda.Event()` — verify
  device backing before trusting `.record()`/`.synchronize()` to gate GPU copies.
- **Two-places coupling:** `_OMNI_CONNECTOR_INIT_ARCHS` (runner) **and**
  `omni_scheduling_coordinator._FULL_PAYLOAD_INPUT_STAGES` must be kept in lock-step — forgetting the
  latter is a **silent Stage-1 consumer hang**. Flag any PR that edits one without the other.
- **CUDA-graph capture == replay:** `_dummy_run` `has_preprocess` buffer path must mirror
  `_preprocess`.
- **Anchor hygiene:** inline-comment insertions shift line numbers — after annotating, re-grep every
  anchor cited in a rollup and refresh.

## The B-align through-line

Most structural findings (divergent duplicates + model-specific logic) converge on one destination:
extract model logic into a v1 **`OmniModelState`** mirroring `worker_v2/OmniModelState` (the B-align /
MR-V2 direction). In review, name that destination rather than proposing ad-hoc per-site fixes — a PR
that adds *another* arch allowlist or `__class__.__name__` check is moving away from it and worth a
non-blocking nudge. Note `OmniModelState` does not exist on `main` yet; it is the target state, so
today the workers force `use_v2_model_runner = False` to keep the omni hooks on the v1 runner.

## Tests & CI

- CPU-only L1/L2 suite in `tests/worker/` (`test_gpu_ar_model_runner.py`,
  `test_gpu_generation_model_runner.py`, `test_omni_gpu_model_runner.py`, `test_omni_connector_mixin.py`,
  `test_process_gpu_memory.py`). Markers: `core_model` = L1&L2, `advanced_model` = L3, `full_model` = L4.
  For running these on hardware, see [verification.md](verification.md).
- Untested (require characterization tests before any refactor that moves them): `base.py`,
  `memory_utils.py`, `payload_span.py`.

## Suggested order (audit rollups)

1. **Now** (low risk, CPU-testable): dead/stale, deprecated, dead guard, silent-failure,
   wrapper-vs-raw, naming/docs/type-hints, non-lazy import hoists. Guard with `tests/worker/`; add
   missing characterization tests first.
2. **Investigate** (may unlock large removals): `prompt_embeds` overlay subsystem; process-level
   memory estimation.
3. **Structural** (MR-V2 / B-align): merge duplicates + evict every model-specific type into
   `OmniModelState`.
