# TerraSim2

Process-based soil moisture modelling on terrain, with a React app for visualising the simulation.

## Python structure

- Python 3.12 or later. Use modern syntax directly (`X | None`, `tuple[int, int]`). No `from __future__ import annotations`.
- The Python package is `terrasim2/` at the repo root.
- All classes live in `terrasim2/k/`. All functions live in `terrasim2/f/`.
- One file is exactly one function or one class. The file name is the function name (`terrasim2/f/bucket_step.py` defines `bucket_step`) or the class name in snake case (`terrasim2/k/grid.py` defines `Grid`).
- Write as many small functions as needed. There is no `utils.py` or any file that bundles several functions together.
- A function may take class objects or other functions as inputs.
- Every function name is a verb, whether it is a free function in `f/` or a method on a class. `_field` is wrong; `_create_field` is right. `cell()` is wrong; `get_cell()` is right. The only exceptions are properties, which are nouns, and the test functions `t`, `t1`, `t2` and so on.

### Current tree

```
TerraSim2/
├── CLAUDE.md
├── tests.py
├── .tests_cache.json      # written by tests.py; per-file hash of last passing version
└── terrasim2/
    ├── __init__.py
    ├── k/
    │   ├── __init__.py
    │   └── terrain_grid.py
    └── f/__init__.py
```

### Tests

- Every function file and every class file defines a `t()` function that tests the unit in that file.
- `t()` may be split into `t1()`, `t2()`, `t3()` and so on for tooling. `t()` calls them in order. Each raises `AssertionError` on failure. `t()` returns nothing on success.
- `tests.py` at the repo root is the test runner. It finds files in `terrasim2/k/` and `terrasim2/f/` that were edited since they last passed, imports each one, and calls its `t()`. It reports pass or fail per file.
- `tests.py` tracks edits with a cache of per-file content hashes. A file's hash is recorded only when its `t()` passes. `tests.py --all` runs every file regardless.
