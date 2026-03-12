# Common Pitfalls in vLLM-Omni

## Mixin + nn.Module MRO Issue

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

## Connector State Management

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

## Async vs Sync Path Differences

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

## Stage Configuration Validation

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

## Memory Management in Diffusion

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

## Input Validation in API Layer

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

## Tensor Parallelism Edge Cases

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

## Test Mock Mismatches

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

---

## Refactor Regressions Without API Changes

**Problem:**
`[Refactor]` PRs often keep the same function names and signatures while changing behavior through ordering, fallback, or state-lifetime changes.

```python
# Before
def init_stage(self, config):
    validate(config)
    self._connector = build_connector(config)
    return self._connector

# After refactor
def init_stage(self, config):
    self._connector = build_connector(config)
    validate(config)  # Connector can now be created with invalid config
    return self._connector
```

**What gets missed:**
- Validation now happens too late
- Exceptions change from "fail fast" to partial initialization
- Logging or metric emission order changes, hiding failures
- Cleanup happens on the happy path only

**Review Action:**
- Treat "no behavior change" as a claim that must be proved
- Compare ordering, exception types, return shapes, and side effects
- Ask for a regression test that pins the preserved behavior, not just successful execution

---

## Happy-Path Tests That Miss Real Failures

**Problem:**
Tests that assert only "returns something" or "does not crash" look reassuring but fail to lock down the actual bug-prone behavior.

```python
def test_generate():
    outputs = omni.generate("hello")
    assert outputs is not None
```

This will pass even if stage ordering, fallback behavior, cleanup, or validation regresses.

**Stronger test shape:**
```python
def test_generate_releases_connector_on_stage_failure():
    with pytest.raises(StageError):
        omni.generate("bad input")
    assert connector.is_released()
```

**Review Action:**
- Check whether the test asserts the contract that changed, not just the happy path
- Look for missing assertions on ordering, cleanup, error type, and distributed behavior
- Flag tests that would still pass if the original bug were reintroduced
