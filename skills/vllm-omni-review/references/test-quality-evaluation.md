# Test Quality Evaluation

Reviewer-side evaluation of test quality in PRs. This is **blocking**: must complete before issuing a verdict.

This is distinct from the blocker scan's binary "tests exist?" check. This evaluates *whether the tests would actually catch bugs*.

**Requires a local clone** of `vllm-project/vllm-omni` for runtime analysis. Static analysis runs without a clone.

---

## 1. Hardware Detection

See [perf-verification.md](perf-verification.md) Section 2 for the canonical hardware detection logic. Same `PLATFORM`, `GPU_COUNT`, `GPU_MODEL`, `VRAM_PER_GPU_GB` variables are used here.

---

## 2. Static Analysis (always runs)

Runs on the diff itself — no clone or hardware required.

### 2.1 Assertion Quality

**Flag these:**

| Anti-pattern | Example | Why it's a problem |
|-------------|---------|-------------------|
| `assert True` | `assert result is not None` | Passes for any non-None value, including wrong results |
| No assertion at all | Function called, return value discarded | Test never fails — it's dead code |
| Bare `pass` in test body | `def test_something(): pass` | Test does nothing |
| Asserts implementation detail | `assert len(internal_cache) == 3` | Breaks on refactors, tests coupling not behavior |
| Float equality | `assert output == 0.123` | Floating point noise causes flaky failures |

### 2.2 Anti-Patterns

| Pattern | Detection | Severity |
|---------|-----------|----------|
| No explicit assertions | Test function has no `assert`/`pytest.raises`/`AssertionError` | High |
| Swallowed errors | `try/except` in test without `pytest.raises` | High |
| Run-level conditional assertions | `if RUN_LEVEL > 1: assert ...` (test always passes at L1) | Medium |
| Hardcoded model names | `model = "Qwen/Qwen2.5-Omni-7B"` without fixture/parametrize | Low |
| Missing `xfail`/`skipif` for known failures | Test expected to fail but not marked | Medium |
| State leakage between tests | Shared mutable fixtures without cleanup | High |

### 2.3 Marker Compliance

Check that test markers match the repo's CI conventions. Reference: `https://docs.vllm.ai/projects/vllm-omni/en/latest/contributing/ci/tests_markers/`

| Marker | Expected usage |
|--------|---------------|
| `@pytest.mark.core_model` | Tests using small/supported models that run in CI L1-L2 |
| `@hardware_test(res=..., num_cards=...)` | Tests requiring specific GPU resources |
| `@pytest.mark.huge_model` | Tests requiring large models (70B+) |
| `@pytest.mark.skipif(condition)` | Platform-specific skips |
| Custom run-level markers | Per CI level configuration |

**Check:** New tests have appropriate markers. Unmarked tests with large models or multi-GPU will fail in CI.

### 2.4 Edge Case Coverage

Scan for coverage of:

- Error paths: invalid inputs, wrong types, empty strings, None values
- Boundary conditions: batch_size=0, sequence_length=1, max dimensions
- Concurrent access: multiple simultaneous requests (for server/entrypoint tests)
- Cleanup: resources freed in error paths, no dangling connections

---

## 3. Runtime Analysis (hardware-dependent)

### 3.1 Find affected test files

```bash
# Changed test files
CHANGED_TESTS=$(git diff --name-only <base>...<head> -- 'tests/')

# Source files that changed
CHANGED_SRC=$(git diff --name-only <base>...<head> -- 'vllm_omni/' | grep -v '__pycache__')

# Map source → test files via grep (more robust than path convention)
for src_file in $CHANGED_SRC; do
    module=$(echo "$src_file" | sed 's|/|.|g; s|\.py$||; s|^vllm_omni\.||')
    # Find test files that import this module
    grep -rl "from vllm_omni\.$module\|import vllm_omni\.$module" tests/ 2>/dev/null
done | sort -u
```

### 3.2 Hardware-aware filtering

Match test markers against available hardware (from [perf-verification.md](perf-verification.md) Section 2):

| Marker requirement | Action when hardware unavailable |
|-------------------|--------------------------------|
| `num_cards=4` but reviewer has 2 | Skip, note in report |
| `@pytest.mark.H100` on non-H100 | Skip, note in report |
| `@hardware_test(res="1024x1024")` but insufficient VRAM | Skip, note in report |
| `@pytest.mark.core_model` | Always runnable (fits on any GPU) |
| `@pytest.mark.huge_model` | Skip unless 80GB+ GPU available |

### 3.3 Run tests

```bash
pytest <affected_tests> \
    --run-level core_model \
    -v \
    --tb=short \
    --timeout=60 \
    -x 2>&1 | tee test_output.log
```

Use `core_model` by default. Use `advanced_model` only when hardware is sufficient and tests require it.

### 3.4 Categorize failures

| Category | Indicators | Action |
|----------|-----------|--------|
| **Test bug** | Test logic is wrong, assertion checks wrong value | Non-blocking suggestion |
| **Code bug** | Test reveals actual issue in PR code | Blocking — REQUEST_CHANGES |
| **Infrastructure** | Missing dependency, port conflict, GPU OOM | Skip, note in report |
| **Flaky** | Inconsistent pass/fail across runs | Note as flaky, do not block |

### 3.5 Runtime signals

- **Slow tests (>60s):** Flag — may indicate resource contention or inefficient test setup
- **GPU memory leaks:** Check `torch.cuda.max_memory_allocated()` trend across tests — if it grows monotonically, there's a leak
- **Skipped tests:** Report count and reasons (especially hardware-related skips)

---

## 4. Quality Assessment (internal use)

This assessment is for the **reviewer's internal analysis** — do not post the full assessment on the PR. Instead, flag the worst 1-2 issues as inline comments (counting against the comment budget).

### Assessment dimensions

| Dimension | A | B | C | D |
|-----------|---|---|---|---|
| **Assertion quality** | Asserts specific expected values with tolerances | Asserts output shape/type but not value | Only `assert not None` or `assertTrue(result)` | No assertions or bare `pass` |
| **Edge case coverage** | Error paths + boundary + concurrent | Error paths + boundary | Only error paths | Happy path only |
| **Marker compliance** | All tests properly marked | Minor gaps (1-2 unmarked) | Significant gaps | No markers or wrong markers |
| **Anti-patterns** | None found | Minor (1 non-critical) | Moderate (2-3 issues) | Severe (no assertions, swallowed errors) |

### How to use

1. Score each dimension A-D
2. Identify the worst dimension — that's the most actionable feedback
3. If any dimension is D, that's a blocker (tests won't catch real bugs)
4. Convert the worst 1-2 findings into specific inline comments for the PR

---

## 5. When to Activate

| PR characteristic | Action |
|-------------------|--------|
| Adds or modifies test files | Full analysis (static + runtime if hardware matches) |
| Touches core code (`engine/`, `stages/`, `connectors/`) without adding tests | Static analysis of existing tests for the changed area + flag missing coverage |
| Test-only PR | Full analysis — test quality IS the review |
| Doc-only PR | Skip |
| Config-only PR | Skip |

---

## 6. Delivery

1. **Local report first** — output assessment and findings to the user
2. **Ask before posting** — "Post test quality findings as PR comments? (y/n)"
3. If posting, convert findings to inline comments (max 2) — counts against comment budget
4. If a D-grade dimension or code bug is found, escalate to REQUEST_CHANGES via normal verdict workflow
5. Always report which tests were skipped due to hardware constraints
