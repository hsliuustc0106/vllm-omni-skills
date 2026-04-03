# Python Style Guide (Google Style)

Key rules to check when reviewing Python code in vLLM-OMNI. Based on Google Python Style Guide.

## Imports
- Group order: `__future__` > stdlib > third-party > repo sub-packages
- Sort lexicographically within groups
- Use `import x` for packages/modules, `from x import y` for specific names
- No relative imports; use full package paths
- Never `import x, y` on one line

## Naming
- Modules/packages: `lower_with_under`
- Classes/Exceptions: `CapWords`
- Functions/methods/variables: `lower_with_under`
- Constants: `CAPS_WITH_UNDER`
- No type info in variable names (no `id_to_name_dict`)

## Formatting
- Max line length: 80 chars (exceptions: imports, URLs)
- 4 spaces indent, never tabs
- Use implicit line joining inside `()`, `[]`, `{}`
- Trailing commas when closing bracket is on separate line

## Common Review Flags
- `import math` inside function body -- "Move imports to the top"
- Imports not in alphabetical order -- "Please keep in alphabetical order"
- Mutable default arguments (`def f(x=[])`) -- always flag
- Bare `except:` or `except Exception: pass` -- always flag
- `logger.info(f"...")` -- should use `logger.info("...: %s", val)` for lazy formatting
- `+=` in loops for string concat -- use `''.join()` or `io.StringIO`
- `if len(seq):` -- should be `if seq:`
- `if x == None:` -- should be `if x is None:`
