# vLLM-Omni Architecture

## Overview

vLLM-Omni extends vLLM for omni-modal (multi-modal) model serving, supporting text, image, video, and audio generation. It provides a unified inference engine with OpenAI-compatible APIs for both LLM and diffusion models.

**Key Differentiators from vLLM:**
- Multi-stage pipeline architecture (e.g., Thinker → Talker → Code2Wav)
- Diffusion Transformer (DiT) model support
- Inter-stage communication via shared memory connectors
- Stage-level concurrency control

---

## Five-Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│  1. User Interface Layer                            │
│     OpenAI-compatible API, CLI, Python SDK          │
├─────────────────────────────────────────────────────┤
│  2. Orchestration Layer                             │
│     Omni, AsyncOmni - coordinates stages            │
├─────────────────────────────────────────────────────┤
│  3. Engine Layer                                    │
│     ModelExecutor, Scheduler, KV cache management   │
├─────────────────────────────────────────────────────┤
│  4. Execution Layer                                 │
│     Workers (GPUARWorker, GPUGenerationWorker)      │
├─────────────────────────────────────────────────────┤
│  5. Model Layer                                     │
│     OmniLLM, OmniDiffusion, model implementations   │
└─────────────────────────────────────────────────────┘
```

---

## Key Directories

| Directory | Purpose | Critical? | Review Focus |
|-----------|---------|-----------|--------------|
| `vllm_omni/entrypoints/` | API server, CLI | High | Input validation, error handling |
| `vllm_omni/engine/` | Engine, scheduler | **Critical** | Concurrency, state management |
| `vllm_omni/model_executor/` | Model execution | **Critical** | Weight loading, memory |
| `vllm_omni/diffusion/` | Diffusion support | High | Latent cache, generation |
| `vllm_omni/connectors/` | Inter-stage IPC | High | Shared memory, cleanup |
| `vllm_omni/stages/` | Stage definitions | High | Lifecycle, state |
| `vllm_omni/config/` | Configuration | Medium | Validation, defaults |
| `vllm_omni/utils/` | Utilities | Low | Test coverage |

---

## Core Components

### Entry Points

**Synchronous:** `Omni` class
```python
from vllm_omni import Omni
llm = Omni(model="Qwen/Qwen2.5-Omni-7B")
outputs = llm.generate("Hello")
```

**Asynchronous:** `AsyncOmni` class
```python
from vllm_omni import AsyncOmni
llm = AsyncOmni(model="Qwen/Qwen2.5-Omni-7B")
outputs = await llm.generate("Hello")
```

### Stage Types

| Type | Worker Classes | Use Case |
|------|---------------|----------|
| `llm` | `GPUARWorker`, `GPUGenerationWorker` | Text generation, multimodal understanding |
| `diffusion` | Diffusion-specific workers | Image/video generation |
| `audio` | Audio workers | TTS, audio synthesis |

### Connectors

| Connector | Use Case | Performance |
|-----------|----------|-------------|
| `OmniShmConnector` | Same-machine inter-process | Fastest |
| `OmniZmqConnector` | Distributed/multi-node | Network-capable |

---

## Multi-Stage Pipeline

### Example: Qwen-Omni Audio Generation

```
┌─────────┐     ┌─────────┐     ┌───────────┐
│ Thinker │ ──▶ │ Talker  │ ──▶ │ Code2Wav  │
│ (LLM)   │     │ (LLM)   │     │ (Audio)   │
└─────────┘     └─────────┘     └───────────┘
     │               │                │
   Text/Audio     Text Code      Audio Output
   Understanding  Generation     Synthesis
```

### Configuration (YAML)

```yaml
stages:
  - name: thinker
    type: llm
  - name: talker
    type: llm
  - name: code2wav
    type: audio
```

---

## Data Flow

```
Request → API Layer → AsyncOmni/Omni
                         │
                         ▼
                    Stage Coordinator
                    (YAML config)
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Stage 1        Stage 2        Stage N
      (Worker)       (Worker)       (Worker)
          │              │              │
          └──────────────┴──────────────┘
                         │
                    OmniConnector
                    (Shm/Zmq)
                         │
                         ▼
                    Response
```

---

## Memory Management

### KV Cache (LLM Stages)
- Paged attention inherited from vLLM
- Block-based memory allocation
- Prefix caching for repeated contexts

### Diffusion Latent Cache
- Intermediate latent storage
- Timestep-based scheduling
- Memory-pressure aware

---

## Supported Models

### Omni-Modal Models
- Qwen3-Omni
- Qwen2.5-Omni
- Qwen3-TTS (CustomVoice, VoiceDesign, Base)
- MiMo-Audio
- Bagel

### Diffusion Models
- Z-Image
- Qwen-Image
- Wan2.2 (video)
- FLUX

---

## Review Considerations

### Critical Paths (High Impact)
- `vllm_omni/engine/` — scheduler changes affect all workloads
- `vllm_omni/model_executor/` — model loading bugs break inference
- `vllm_omni/connectors/` — communication bugs cause hangs/crashes

### High-Risk Patterns
1. **Stage coordination changes** — can break multi-stage pipelines
2. **Memory management in connectors** — shared memory leaks
3. **Worker lifecycle changes** — affect tensor parallelism
4. **Input validation gaps** — engine crashes instead of 400 errors

### Testing Requirements
| Component | Test Requirement |
|-----------|------------------|
| LLM stages | Actual model inference |
| Diffusion stages | Generation quality |
| Connectors | Load testing, memory leak check |
| Multi-stage | End-to-end pipeline |
| API endpoints | Input validation, error responses |

---

## Code patterns for review

*This section holds the former standalone `code-patterns.md` material (async, validation, connectors, logging, etc.).*

### Async Function Complexity

**Guidelines:**
- Each `await` is a potential failure point and state transition
- Consider splitting long async chains into smaller helpers
- Watch for race conditions in complex async flows
- Use `return_exceptions=True` for parallel operations

**Good:**
```python
async def process_batch(requests: list[Request]) -> list[Response]:
    validated = [_validate_request(r) for r in requests]
    results = await asyncio.gather(
        *[_process_single(r) for r in validated],
        return_exceptions=True
    )
    return [_handle_result(r) for r in results]
```

**Bad:**
```python
async def process_batch(requests: list[Request]) -> list[Response]:
    results = []
    for r in requests:
        results.append(await _process_single(r))  # Sequential, no error handling
    return results
```

---

### Deferred Output Materialization

**When to inspect:** PRs that move `OmniModelRunnerOutput`, connector output, full-payload accumulation, token/logprob bookkeeping, or multimodal CPU conversion into background threads, async wrappers, or delayed builders.

**Review checklist:**
- Snapshot all per-step runner and connector state synchronously before launching deferred work. Do not call drain/clear getters from background code after the next `execute_model()` step can start.
- Treat nested mutable containers and device tensors as live until copied with explicit lifetime/stream ownership. Shallow copies are insufficient if later steps can reuse list, dict, or tensor contents.
- Handle non-CUDA accelerators explicitly when using stream/event copy code; CUDA-only snapshots can leave XPU/NPU tensors live.
- Keep stateful accumulation (`_pending_full_payload_send`, chunk-ready sets, finished/kv signal sets) on the owning step, or guard it with cycle-owned state/locks.
- Bound or serialize background builders; one daemon thread/task per step can race shared state and add GIL/resource pressure.
- Preserve reset/shutdown cleanup for async resources: close clients, cancel and await tasks, and acquire session locks before mutating or dropping session state.

**Blocking examples:**
- Connector signals attach to the wrong step or are cleared before the right output consumes them.
- Full-payload rows are dropped, duplicated, or reordered under overlap.
- CPU copies race with source-buffer reuse because source tensors/buffers were not retained or synchronized.
- Reset or shutdown drops state while an in-flight request/task continues using it.

---

### Distributed Execution Patterns

**When complexity is justified:**
- Tensor parallelism synchronization across workers
- Pipeline parallelism stage coordination
- Distributed KV cache management
- Multi-node communication patterns

**Critical questions:**
- Is distributed complexity isolated from business logic?
- Are distributed failure modes handled?
- Is there a clear fallback for single-device execution?

**Pattern:**
```python
def get_world_size() -> int:
    """Returns 1 if not in distributed mode."""
    if not dist.is_initialized():
        return 1
    return dist.get_world_size()
```

---

### KV Cache Management

**Guidelines:**
- Ensure clear separation between allocation, update, and cleanup
- Document invariants and assumptions
- Use type system to enforce valid states
- Always handle cleanup in error paths

**Pattern:**
```python
class KVCache:
    def allocate(self, num_blocks: int) -> None:
        assert self._state == CacheState.UNINITIALIZED
        self._blocks = [Block() for _ in range(num_blocks)]
        self._state = CacheState.ALLOCATED

    def update(self, block_id: int, kv_data: Tensor) -> None:
        assert self._state == CacheState.ALLOCATED
        self._blocks[block_id].update(kv_data)

    def free(self) -> None:
        self._blocks = []
        self._state = CacheState.UNINITIALIZED
```

---

### Input Validation Pattern

**Guidelines:**
- Validate early (API layer, not engine)
- Return actionable error messages
- Use clean HTTP status codes (400 for client errors)

**Pattern:**
```python
def _validate_request(self, request: Request) -> str | None:
    """Returns error message or None if valid."""
    if not request.input:
        return "Input cannot be empty"

    if request.param and request.param not in VALID_PARAMS:
        return f"Invalid param '{request.param}'. Valid: {VALID_PARAMS}"

    return None

def handle_request(self, request: Request) -> Response:
    error = self._validate_request(request)
    if error:
        return Response(status_code=400, content={"error": error})
    return self._process(request)
```

---

### Connector Communication

**Guidelines:**
- Use context managers for resource cleanup
- Handle timeouts explicitly
- Implement proper error propagation

**Pattern:**
```python
async def send_to_next_stage(self, data: Tensor) -> None:
    try:
        async with self.connector.acquire(timeout=30.0) as channel:
            await channel.send(data)
    except TimeoutError:
        logger.error("Stage communication timeout")
        raise StageError("Downstream stage unavailable")
    except Exception as e:
        logger.error(f"Stage communication failed: {e}")
        raise
```

---

### Stage Lifecycle

**Guidelines:**
- Stages are configured at init time
- Runtime reconfiguration requires full teardown
- State must be properly managed across stage boundaries

**Pattern:**
```python
class Stage:
    def __init__(self, config: StageConfig):
        self._validate_config(config)
        self.config = config
        self._state = StageState.INITIALIZED

    async def start(self) -> None:
        assert self._state == StageState.INITIALIZED
        await self._allocate_resources()
        self._state = StageState.RUNNING

    async def stop(self) -> None:
        if self._state == StageState.RUNNING:
            await self._release_resources()
        self._state = StageState.STOPPED
```

---

### Test Coverage Requirements

| Code Type | Requirement |
|-----------|-------------|
| New features | Happy path + edge cases + error handling |
| Bug fixes | Regression test + edge cases around fix |
| Performance | Benchmarks with before/after measurements |
| Distributed | Must test in distributed mode |
| Quantization | Memory savings + quality impact measured |
| API endpoints | Input validation + error responses |

---

### Code Quality Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Function length | 100+ lines | Review for split opportunities |
| Complexity | 11+ | Requires refactoring |
| Nesting depth | 4+ levels | Requires refactoring |
| Parameters | 7+ | Consider parameter object |

---

### Error Handling Pattern

**Guidelines:**
- Use specific exception types
- Include actionable context in messages
- Don't silently swallow errors

**Pattern:**
```python
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class EngineError(Exception):
    """Raised when engine operation fails."""
    pass

def process(self, request: Request) -> Response:
    try:
        return self._process_internal(request)
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return Response(status_code=400, content={"error": str(e)})
    except EngineError as e:
        logger.error(f"Engine error: {e}")
        return Response(status_code=500, content={"error": "Internal error"})
```

---

### Logging Pattern

**Guidelines:**
- Use appropriate log levels
- Include relevant context
- Avoid logging sensitive data

```python
# Good
logger.info(f"Processing request {request_id} with model {model_name}")
logger.warning(f"Slow response time: {elapsed_ms}ms for {endpoint}")
logger.error(f"Failed to load model {model_path}: {e}")

# Bad
logger.info("Processing request")  # No context
print(f"Error: {e}")  # Wrong logging method
logger.debug(f"User token: {token}")  # Sensitive data
```
