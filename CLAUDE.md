# TerraSim2

Process-based soil moisture modelling on terrain, with a React app for visualising the simulation.

## Python structure

- Python 3.12 or later. Use modern syntax directly (`X | None`, `tuple[int, int]`). No `from __future__ import annotations`.
- The Python package is `terrasim2/` at the repo root.
- All classes live in `terrasim2/k/`. All functions live in `terrasim2/f/`.
- One file is exactly one function or one class. The file name is the function name (`terrasim2/f/bucket_step.py` defines `bucket_step`) or the class name in snake case (`terrasim2/k/grid.py` defines `Grid`).
- Write as many small functions as needed. There is no `utils.py` or any file that bundles several functions together.
- A function may take class objects or other functions as inputs.
- Every physical quantity states its unit in the docstring entry for each parameter and attribute. No unit comments in code lines.
- Every function name is a verb, whether it is a free function in `f/` or a method on a class. `_field` is wrong; `_create_field` is right. `cell()` is wrong; `get_cell()` is right. The only exceptions are properties, which are nouns, and the test functions `t`, `t1`, `t2` and so on.

### Current tree

```
TerraSim2/
├── CLAUDE.md
├── tests.py
├── .tests_cache.json      # written by tests.py; per-file hash of last passing version
├── terrasim2/
│   ├── __init__.py
│   ├── k/
│   │   ├── __init__.py
│   │   └── terrain_grid.py
│   └── f/__init__.py
└── app/                   # Next.js + TypeScript; see App structure
    ├── package.json       # scripts: dev, build, lint, test, test:changed
    ├── vitest.config.mts
    ├── public/terrain/sample.json         # synthetic 40x40 hill; replaced by Python output later
    └── src/
        ├── app/
        │   ├── layout.tsx                 # root html, fonts, metadata
        │   ├── page.tsx                   # renders <TerrainViewer url="/terrain/sample.json" />
        │   └── globals.css
        ├── c/                             # every .tsx has a .test.tsx beside it
        │   ├── TerrainViewer.tsx          # fetches via useTerrainGrid, shows status/error, loads scene client-only
        │   ├── TerrainViewer.module.css
        │   ├── TerrainScene.tsx           # Canvas, camera frame, lights, OrbitControls, TerrainSurface
        │   └── TerrainSurface.tsx         # the mesh; must sit inside a Canvas
        ├── f/                             # every .ts has a .test.ts beside it
        │   ├── buildTerrainMesh.ts        # TerrainGrid -> vertex positions and triangle indices
        │   ├── createTerrainGeometry.ts   # TerrainGrid -> Three.js BufferGeometry with normals
        │   ├── frameTerrainCamera.ts      # TerrainGrid -> camera target, position, near, far
        │   ├── parseTerrainGrid.ts        # JSON -> TerrainGrid
        │   └── readPositiveInteger.ts
        ├── h/
        │   └── useTerrainGrid.ts          # fetch + parse a terrain JSON by url
        └── t/
            ├── TerrainGrid.ts
            └── TerrainMesh.ts
```

### Tests

- Every function file and every class file defines a `t()` function that tests the unit in that file.
- `t()` may be split into `t1()`, `t2()`, `t3()` and so on for tooling. `t()` calls them in order. Each raises `AssertionError` on failure. `t()` returns nothing on success.
- `tests.py` at the repo root is the test runner. It finds files in `terrasim2/k/` and `terrasim2/f/` that were edited since they last passed, imports each one, and calls its `t()`. It reports pass or fail per file.
- `tests.py` tracks edits with a cache of per-file content hashes. A file's hash is recorded only when its `t()` passes. `tests.py --all` runs every file regardless.

## App structure

- The visualisation app is `app/` at the repo root: Next.js with TypeScript. The terrain renders as a 3D mesh with orbit controls via Three.js.
- `app/src/c/` holds components, one per file, file named after the component.
- `app/src/f/` holds pure functions, one per file, same rules as the Python `f/`. No React, no browser APIs.
- `app/src/h/` holds hooks, one per file, each named `useSomething`.
- `app/src/t/` holds types shared by more than one file, one type per file, file named after the type. A type used by a single file stays in that file.
- `app/src/app/` is the Next.js routing folder. Pages compose components and hold no logic.
- Function names are verbs here too. Components and hooks are the exceptions: a component is a noun, a hook is `use` plus a noun.

### Tests

- Every file in `c/`, `f/` and `h/` has a test file beside it with the same name and a `.test.ts` or `.test.tsx` suffix. This is the app's equivalent of `t()`; tests stay out of the source file so they stay out of the browser bundle.
- Pure functions are tested against hand-computed outputs. Components are rendered in a test DOM and asserted on. The 3D scene is asserted on its scene graph, not on pixels.
- Vitest is the runner. `vitest --changed` runs only tests for files edited since the last commit, the counterpart of `tests.py`.
