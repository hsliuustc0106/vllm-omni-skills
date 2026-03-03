# vllm-omni-skills: Test Design

## Validation Strategy

All skills are validated automatically via `scripts/validate_all.py`. The validator checks four categories of requirements.

## 1. Structural Validation

| Check | Rule |
|-------|------|
| Frontmatter exists | SKILL.md starts with `---` YAML block |
| `name` field | Present, non-empty, max 64 chars, lowercase letters/digits/hyphens only |
| `description` field | Present, non-empty, max 1024 chars |
| Body length | SKILL.md body (after frontmatter) is under 500 lines |
| No extra frontmatter fields | Only `name` and `description` allowed |

## 2. Reference Integrity

| Check | Rule |
|-------|------|
| Internal links resolve | Every `[text](path)` link in SKILL.md points to an existing file |
| One-level depth | Reference files do not contain links to further reference files |
| No orphaned files | Every file in `references/` is linked from SKILL.md |

## 3. Content Quality

| Check | Rule |
|-------|------|
| Description has WHAT | Description explains what the skill does |
| Description has WHEN | Description includes trigger context ("Use when...") |
| Third person | Description does not start with "I" or "You" |
| Consistent naming | Skill directory name matches frontmatter `name` field |

## 4. Script Validation

| Check | Rule |
|-------|------|
| Syntax check (Python) | `py_compile.compile()` succeeds for all `.py` files |
| Syntax check (Shell) | `bash -n` succeeds for all `.sh` files |
| Executable bit | Scripts have executable permissions |

## Running Validation

```bash
python scripts/validate_all.py
```

Exit codes:
- `0`: All checks pass
- `1`: One or more checks failed (details printed to stderr)

## Adding New Skills

When adding a new skill, run validation before committing:

```bash
python scripts/validate_all.py skills/your-new-skill/
```
