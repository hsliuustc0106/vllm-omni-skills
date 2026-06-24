# Blocker Patterns Library

Each pattern includes: the anti-pattern, why it's dangerous, and required fix.

Cross-references point to [architecture.md](architecture.md) (section **Code patterns for review**) for "how to fix" guidance.

## Exception Handling

### Pattern: Silent Swallow
```python
# BLOCKER: Silent exception swallow
try:
    result = risky_operation()
except:
    pass  # or: except Exception: pass
```

**Why dangerous:** Hides all failures, makes debugging impossible.

**Required fix:** At minimum, log the exception. Better: catch specific exceptions.

**Cross-ref:** See [Error Handling Pattern](architecture.md#error-handling-pattern) for proper exception handling with logging.

---

### Pattern: Broad Catch with Continue
```python
for item in items:
    try:
        process(item)
    except Exception:
        continue  # silently skips
```

**Why dangerous:** Partial failure with no visibility.

**Required fix:** Log failure, increment counter, or fail fast.

**Cross-ref:** See [Error Handling Pattern](architecture.md#error-handling-pattern) for proper exception handling with logging.

---

### Pattern: Overly Broad except Clause
```python
# BLOCKER: catches every exception type, including ones you didn't think of
try:
    evt = build_event(...)
    return evt
except Exception:
    return None
```

**Why dangerous:** Too flexible. If you catch an exception type you don't expect, it is almost always an unhandled edge case that should surface and be *fixed* — not be swallowed into `None`/`pass`. Real clusters: `vllm_omni/metrics/stats.py` (`except Exception: return None` ×4), `vllm_omni/metrics/{modality,utils}.py`.

**Required fix:** Catch the **specific** types you actually expect (`ValueError`, `KeyError`, `OSError`, `torch.cuda.OutOfMemoryError`, `msgspec.ValidationError`, …). At a genuine top-level / best-effort boundary (metrics, signal handlers), at minimum log; never swallow into `pass`/`return None` on a path that should fail loudly (init, config validation, weight loading, request handling). The repo backs this with ruff `BLE001` (currently suppressed in `vllm_omni/patch.py` via `# noqa: BLE001`) — prefer fixing over suppressing.

**Cross-ref:** See [Error Handling Pattern](architecture.md#error-handling-pattern) for proper exception handling with logging.

---

### Pattern: Uninitialized Variable
```python
result = obj.method().nested.value  # potential AttributeError
```

**Why dangerous:** Crashes with `AttributeError` if any step returns `None`.

**Required fix:** Add explicit None guards before accessing attributes.

```python
if obj is not None and obj.method() is not None:
    result = obj.method().nested.value
```

**Cross-ref:** See [None Safety](architecture.md#input-validation-pattern) for guard patterns.

---

## Resource Management

### Pattern: Unclosed Resource
```python
f = open(path)  # no 'with' statement
content = f.read()
# f never closed
```

**Why dangerous:** Resource leaks, especially in long-running servers instances.

**Required fix:** Use context managers (`with open(...) as f:`).

**Cross-ref:** See [Connector Communication](architecture.md#connector-communication) for proper connector usage with context managers.

---

### Pattern: Shared Mutable State
```python
shared_list = []  # modified by concurrent coroutines
async def append(item):
    shared_list.append(item)
```

**Why dangerous:** Race conditions, corrupted state.

**Required fix:** Use `asyncio.Lock` or thread-safe structures.

**Cross-ref:** See [Distributed Execution Patterns](architecture.md#distributed-execution-patterns) for thread safety alternatives.

---

## None Safety

### Pattern: Unchecked Chain
```python
result = obj.method().nested.value  # no None checks
```

**Why dangerous:** `AttributeError` if any step returns `None`.

**Required fix:** Add explicit None guards before each access, or use `getattr()` with defaults.

```python
# Option 1: Explicit None checks
if obj is not None:
    method_result = obj.method()
    if method_result is not None:
        result = method_result.nested.value

# Option 2: getattr with default
result = getattr(getattr(obj, "method", lambda: None)(), "nested", None)
```

**Cross-ref:** See [Input Validation Pattern](architecture.md#input-validation-pattern) for early validation guidance.

---

### Pattern: Missing None Check
```python
def process(data):
    if data is None:
        return None
    # Missing None check!
    result = process(data)  # Silent failure
    return True
```

**Why dangerous:** Hides bugs, makes debugging impossible.

**Required fix:** Add explicit None check and log a warning. Better: `return None`.

**Cross-ref:** See [Input Validation Pattern](architecture.md#input-validation-pattern) for validation guidance.

---

## Type Safety

### Pattern: kwargs String-Lookup Passthrough
```python
# BLOCKER-prone: raw dict + string keys duplicated across files
def forward(self, **kwargs):
    if (
        "runtime_additional_information" in kwargs
        and "model_intermediate_buffer" not in kwargs
    ):
        ...
```

**Why dangerous:** The compiler can't see a missing or misspelled key, so failures are silent; unknown keys are silently dropped. This exact guard is copy-pasted across `cosyvoice3`, `indextts2` (×3), `qwen3_tts`, and `qwen3_omni` — each copy is a new place for the strings to drift.

**Required fix:** Prefer explicit typed params. The repo already has the right primitive: `msgspec.Struct` with `forbid_unknown_fields=True` rejects unknown keys instead of silently dropping them (see `_StructBase` in `vllm_omni/data_entry_keys.py`, `MoriPullRequest` in the mori connector). A `@dataclass` or `TypedDict` works too. If `**kwargs` is unavoidable (vLLM base-class compat), centralize the key strings as module constants behind one typed accessor.

**Cross-ref:** See [Input Validation Pattern](architecture.md#input-validation-pattern) for validation guidance.

---

### Pattern: Any-Typed Signature / Wrong Annotation
```python
# BLOCKER-prone: Any disables the checker for that position
def _extract_mm_output(engine_outputs: Any) -> dict[str, Any]:
    ...
```

**Why dangerous:** `Any` disables type checking for that position, so typos and wrong shapes pass silently. It is often leaked from tests: `SimpleNamespace` fakes force the consuming production code to be typed `Any`, which then propagates outward into public signatures. Wrong annotations (e.g. `-> bool` returning `Optional[bool]`) are worse — actively misleading.

**Required fix:** Replace `Any` with the concrete type, a `Protocol`, or a `Union`; if a type is genuinely dynamic, prefer `object` + `isinstance` narrowing over `Any`. In tests, replace `SimpleNamespace` with the real class, a small `@dataclass`/`TypedDict`, or a `Protocol` + fake so the system under test stays typed.

**Cross-ref:** See [Input Validation Pattern](architecture.md#input-validation-pattern) for validation guidance.

---

## Breaking Change Detection

### Pattern: Function Signature Change
```python
# BLOCKER: No backward compatibility
# Old signature: def get_user(user_id: int):
# New signature adds a non-optional parameter:
def get_user(user_id: int, include_profile: bool):  # Breaking change!
    pass
```

**Why dangerous:** Breaks existing code that depends on this function.

**Required fix:** Add deprecation path or maintain backward compatibility for 1-2 releases. Document migration.

**Cross-ref:** See [API Endpoints](architecture.md#connector-communication) for API compatibility guidance.

---

### Pattern: Removed Public API
```python
# BLOCKER: No deprecation path
def remove_feature(name):
    pass
```

**Why dangerous:** Breaks existing code that depends on this function.
**required fix:** If removal is necessary, provide replacement. Otherwise, document breaking change and deprecation timeline.
**Cross-ref:** See [API Endpoints](architecture.md#connector-communication) for OpenAI compatibility guidance
---

### Pattern: Changed Default
```python
class Config:
    def __init__(self):
        self.default_value = "on"  # Was "off" - breaking change!
```

**Why dangerous:** Breaks existing code that depends on this default.

**Required fix:** Document the change clearly. If intentional, provide rollback code or migration script.

**Cross-ref:** See [API Endpoints](architecture.md#connector-communication) for API compatibility guidance.

---

## Memory Management

### Pattern: Unbounded Latent Cache
```python
class DiffusionModel:
    def generate(self, prompt):
        self.latent_cache.append(create_latents())  # Never cleared!
        return decode(self.latent_cache[-1])
```

**Why dangerous:** Memory leaks accumulate across generations.
**required fix:** Explicitly clear latent cache after generation. Add memory-pressure handling.
**Cross-ref:** See [Memory Management in Diffusion](blocker-patterns.md#memory-management-in-diffusion) for latent cache lifecycle guidance
---

## Async Safety

### Pattern: Blocking Call in Async
```python
# BLOCKER: Blocking call blocks event loop
async def process(self, request):
    result = blocking_call()  # Blocks event loop!
    return result
```

**Why dangerous:** Blocks event loop, prevents concurrent requests.
**required fix:** Use `asyncio.to_thread()` or await pattern.
**Cross-ref:** See [Async Function Complexity](architecture.md#async-function-complexity) for async patterns
---

### Pattern: Hardcoded Timeout
```python
def connect(url):
    response = requests.get(url, timeout=30.0)  # Hardcoded - no flexibility!
```

**Why dangerous:** No flexibility, hides issues in testing.

**Required fix:** Make timeout configurable or add timeout parameter to CLI flags.

**Cross-ref:** See [Connector Communication](architecture.md#connector-communication) for proper connector usage.

---

### Pattern: Hardcoded Retry Count
```python
MAX_RETRIES = 3  # No justification, no backoff

for attempt in range(MAX_RETRIES):
    try:
        response = requests.get(url, timeout=5)
    except TimeoutError:
        pass  # Silent retry, no logging
```

**Why dangerous:** Can cause infinite retry loops or delays without visibility.

**Required fix:** Use exponential backoff with configurable max retries or circuit breaker pattern.

**Cross-ref:** See [Stage Lifecycle](architecture.md#stage-lifecycle) for lifecycle management.

---

### Pattern: Sequential Async in Loop
```python
# BLOCKER: No parallelism
results = []
for r in requests:
    result = await _process_single(r)  # Sequential, slow
    return results
```

**Why dangerous:** Poor throughput, no parallelism benefits.

**Required fix:** Use `asyncio.gather()` with `return_exceptions=True` for parallel execution.

**Cross-ref:** See [Async Function Complexity](architecture.md#async-function-complexity) for proper async patterns.

---

### Pattern: Device-Specific Code
```python
# BLOCKER: No non-CUDA fallback
if torch.cuda.is_available():
    x = x.to(device)
else:
    x.cpu()  # Missing non-CUDA path!
```

**Why dangerous:** Crashes on non-CUDA systems.

**Required fix:** Check `torch.cuda.is_available()` first and use appropriate fallback.

**Cross-ref:** See [Distributed Execution Patterns](architecture.md#distributed-execution-patterns) for distributed patterns.

---

## API Boundaries

### Pattern: Unsafe Parameter Passthrough
```python
# BLOCKER: No validation before passing to API
user_input = request.json.get("model")
response = model.generate(request.json["prompt"])
```

**Why dangerous:** Arbitrary code execution, model injection.

**Required fix:** Validate all user inputs before passing to model.

**Cross-ref:** See [Input Validation Pattern](architecture.md#input-validation-pattern) for validation guidance.

---

### Pattern: Missing Response Validation
```python
# BLOCKER: No validation after calling API
async def create_item(self, request):
    # Missing: validation
    # Could return invalid responses
        return {"error": "Internal server error"}
```

**Why dangerous:** API contract violations.

**Required fix:** Validate responses match schema and handle errors explicitly.

**Cross-ref:** See [Error Handling Pattern](architecture.md#error-handling-pattern) for proper error handling patterns.

---

## Security

### Pattern: Hardcoded Secrets
```python
# BLOCKER: Hardcoded credentials
API_KEY = "sk-abc123"
DATABASE_PASSWORD = "secret123"
```

**Why dangerous:** Credential exposure in logs, git history.

**Required fix:** Use environment variables or secret management systems.

**Cross-ref:** See [Logging Pattern](architecture.md#logging-pattern) for proper logging practices.

---

### Pattern: Insecure Deserialization
```python
import pickle  # DANGEROUS: loading untrusted data
data = pickle.loads(user_input)
```

**Why dangerous:** Remote code execution (RCE).

**Required fix:** Never use `pickle.loads()` on untrusted data. Use safe deserialization libraries.

**Cross-ref:** See [Error Handling Pattern](architecture.md#error-handling-pattern) for safe error handling patterns.

---

### Pattern: SQL Injection
```python
# BLOCKER: No parameterized queries
cursor.execute(user_input)  # Direct string interpolation
```

**Why dangerous:** Data breach.

**Required fix:** Use parameterized queries (prepared statements, ORM).

**Cross-ref:** See [Input Validation Pattern](architecture.md#input-validation-pattern) for validation guidance.

---

### Pattern: Unsafe String Formatting with User Input
```python
# BLOCKER: User-controlled format string enables code injection
user_template = request.args.get("template")  # e.g., "{user.__class__.__mro__}"
msg = user_template.format(user=current_user)  # Can leak internal state!

# BLOCKER: eval/exec with user input
result = eval(user_expression)  # Remote code execution!
query = f"SELECT * FROM {user_table}"  # SQL injection via string formatting
```

**Why dangerous:** `str.format()` with user-controlled templates can access object attributes. `eval()`/`exec()` execute arbitrary code. String formatting into SQL/HTML enables injection.

**Required fix:**
- For templates: use sandboxed template engines (Jinja2 with autoescape) or whitelist allowed placeholders
- For SQL: use parameterized queries, never string interpolation
- For code execution: never pass user input to `eval()`/`exec()`

**Note:** Normal f-strings like `f"Hello, {name}!"` are safe - they don't execute code, just interpolate.

**Cross-ref:** See [Input Validation Pattern](architecture.md#input-validation-pattern) for validation guidance.

---

## Test Coverage

### Pattern: Missing Regression Test
```python
# BLOCKER: Bug fix without regression test
def fix_bug():
    pass  # Bug fixed
```

**Why dangerous:** Bug may resurface in future PRs.

**Required fix:** Add a regression test that reproduces the original bug.

**Cross-ref:** See [Test Coverage Requirements](architecture.md#test-coverage-requirements) for test coverage requirements.

---

### Pattern: Weak Assertions
```python
# BLOCKER: Assertion too weak
def test_result():
    result = compute()
    assertTrue(result)  # Passes even if result is wrong!
```

**Why dangerous:** False confidence in test results.

**Required fix:** Use meaningful assertions that verify actual behavior.

**Cross-ref:** See [Test Coverage Requirements](architecture.md#test-coverage-requirements) for test coverage requirements.

---

### Pattern: Mock Mismatch
```python
# Production
class Model(nn.Module, Mixin):
    pass

# Test mock - different Mro
class MockModel(Mixin):  # Missing nn.Module
    pass
```

**Why dangerous:** Tests pass but hide real bugs.

**Required fix:** Ensure mocks match production inheritance hierarchy.

**Cross-ref:** See [Test Mock Mismatches](blocker-patterns.md#test-mock-mismatches) for mock testing guidance.

---

### Pattern: Only Happy Path Test
```python
# BLOCKER: No edge case tests
def process(self, data):
    result = self._process(data)
    # Happy path only
    return result
```

**Why dangerous:** Edge cases not tested, bugs only surface in production.

**Required fix:** Add tests for error handling, edge cases (empty, null, boundary).

**Cross-ref:** See [Test Coverage Requirements](architecture.md#test-coverage-requirements) for test coverage requirements.

---

### Pattern: No Performance Benchmark
```python
# BLOCKER: Performance optimization without benchmark data
def optimize():
    pass  # Faster!
    return data
```

**Why dangerous:** Claims without evidence.

**Required fix:** Run benchmarks with `pytest` or manual timing, document results.

**Cross-ref:** See [Test Coverage Requirements](architecture.md#test-coverage-requirements) for test coverage requirements.

---

### Pattern: Missing Memory Measurement
```python
# BLOCKER: Memory optimization without memory measurement
pass
```

**Why dangerous:** Cannot verify memory savings.

**Required fix:** Use memory profiling tools and report peak and delta.

**Cross-ref:** See [Memory Management in Diffusion](blocker-patterns.md#memory-management-in-diffusion) for latent cache lifecycle guidance.

---

### Pattern: No Distributed Test
```python
# BLOCKER: Distributed changes without distributed test
def test_distributed(self):
    pass
```

**Why dangerous:** Distributed bugs only surface in distributed environments, not unit tests.

**Required fix:** Test in distributed mode with `torchrun`.

**Cross-ref:** See [Tensor Parallelism Edge Cases](blocker-patterns.md#tensor-parallelism-edge-cases) for distributed testing guidance.

---

## Documentation

### Pattern: Missing Migration Guide
```python
# BLOCKER: Breaking change without migration guide
def migrate_config():
    pass
```

**Why dangerous:** Users unable to upgrade.

**Required fix:** Document breaking changes in RELEASE_NOTES.md. Provide migration instructions.

**Cross-ref:** See [API Endpoints](architecture.md#connector-communication) for OpenAI compatibility guidance.

---

### Pattern: Missing Usage Examples
```python
# BLOCKER: New feature without usage examples
def add_feature():
    pass
```

**Why dangerous:** Users can't understand how to use the feature.

**Required fix:** Add usage examples, docstrings.

**Cross-ref:** See [Comment Style](review-execution.md#comment-style) for review comment guidance.

---

## Part 2: Common pitfalls (footguns and review prompts)

*This part holds the former standalone `pitfalls.md` material (MRO, connector state, async vs sync, diffusion memory, API validation, tensor parallel, test mocks).*

### Mixin + nn.Module MRO Issue

**Problem:**
When a mixin class is listed **after** `nn.Module` in inheritance, the mixin's `__init__` will **not** be called because `nn.Module.__init__()` doesn't call `super().__init__()`.

```python
# BROKEN - Mixin's __init__ won't be called
class MyModel(nn.Module, SomeMixin):
    def __init__(self):
        super().__init__()  # Only calls nn.Module.__init__!
        self.mixin_method()  # CRASH: mixin attributes not initialized
```

**Solution - Lazy Initialization:**
```python
class SomeMixin:
    @property
    def _internal_state(self) -> set:
        if not hasattr(self, '_internal_state_storage'):
            self._internal_state_storage = set()
        return self._internal_state_storage
```

**Red Flag in Tests:**
If test mocks inherit only from the mixin (not `nn.Module`), they won't catch this bug because the test's `super().__init__()` WILL call the mixin's `__init__`.

**Review Action:**
- Check inheritance order when you see mixins
- If mixin has `__init__` that sets attributes, flag it
- Verify tests use realistic class hierarchy

---

### Connector State Management

**Problem:**
Connectors use shared memory. Improper cleanup leads to leaks and crashes.

```python
# BROKEN - No cleanup on error
def send_data(self, data):
    self.shm_buffer.write(data)
    raise ValueError("oops")  # Buffer never released!
```

**Solution - Context Managers:**
```python
def send_data(self, data):
    with self.shm_buffer.acquire() as buf:
        buf.write(data)
        # Automatically released even on error
```

**Review Action:**
- Check error paths in connector code
- Look for `try/finally` or context managers
- Verify cleanup in all branches

---

### Async vs Sync Path Differences

**Problem:**
`AsyncOmni` and `Omni` have different code paths. Changes may work in one but not the other.

```python
# Works in sync path
def process(self, request):
    result = blocking_call()  # OK in sync
    return result

# Breaks in async path
async def process(self, request):
    result = blocking_call()  # Blocks event loop!
    return result
```

**Solution:**
```python
async def process(self, request):
    result = await asyncio.to_thread(blocking_call)
    return result
```

**Review Action:**
- Check if PR modifies shared code paths
- Verify both sync and async are tested
- Look for blocking calls in async code

---

### Stage Configuration Validation

**Problem:**
Stage configs are loaded at init time. Invalid configs may not fail until runtime.

```python
# Config loaded but not validated
config = load_yaml("stages.yaml")
# ... much later ...
stage = create_stage(config["unknown_stage"])  # Crash!
```

**Solution - Eager Validation:**
```python
config = load_yaml("stages.yaml")
validate_stage_config(config)  # Fail fast
```

**Review Action:**
- Check for config validation at load time
- Verify all required fields are checked
- Look for defaults that mask invalid configs

---

### Memory Management in Diffusion

**Problem:**
Diffusion models manage large latent caches. Memory leaks accumulate across generations.

```python
# BROKEN - Latent cache grows unbounded
class DiffusionModel:
    def generate(self, prompt):
        self.latent_cache.append(create_latents())  # Never cleared!
        return decode(self.latent_cache[-1])
```

**Solution:**
```python
class DiffusionModel:
    def generate(self, prompt):
        latents = create_latents()
        try:
            return decode(latents)
        finally:
            del latents  # Explicit cleanup
```

**Review Action:**
- Check latent cache lifecycle
- Verify cleanup in generation loops
- Look for memory-pressure handling

---

### Input Validation in API Layer

**Problem:**
Invalid requests that reach the engine can cause crashes instead of clean errors.

```python
# BROKEN - Validation happens in engine
def create_speech(self, request):
    # Missing validation here
    return self.engine.generate(request)  # Engine crashes!
```

**Solution - Validate Early:**
```python
def create_speech(self, request):
    error = self._validate_request(request)
    if error:
        return BadRequest(error)  # Clean 400 response
    return self.engine.generate(request)
```

**Review Action:**
- Check validation before engine calls
- Verify all parameters are validated
- Ensure error messages are actionable

---

### Tensor Parallelism Edge Cases

**Problem:**
Code may work single-GPU but break with tensor parallelism.

```python
# Works on single GPU
def forward(self, x):
    return self.layer(x) + self.bias  # bias not replicated!
```

**Solution:**
```python
def forward(self, x):
    return self.layer(x) + self.bias.data  # Explicitly access data
```

**Review Action:**
- Check if changes affect distributed execution
- Verify tensor parallel tests exist
- Look for rank-specific logic

---

### Test Mock Mismatches

**Problem:**
Tests may mock classes differently from production, hiding bugs.

```python
# Production
class Model(nn.Module, Mixin):
    pass

# Test mock - different MRO!
class MockModel(Mixin):  # Missing nn.Module
    pass
```

This hides the MRO bug described above.

**Review Action:**
- Compare mock inheritance to production
- Check if mocks skip critical base classes
- Verify mock behavior matches production
