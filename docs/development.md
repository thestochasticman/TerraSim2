# Development

<!-- nav -->
← [Visualiser](visualiser.md) · [Index](README.md) · [History](history.md) →
<!-- /nav -->

## Environment

Python 3.12 or later in the lab's `borevitz_lab` conda environment, which carries the lab packages the ingest needs (`troi`, `pysilo`, `pycopdem`, `pyslga`, `pysentinel2`). `terrasim2` itself needs NumPy, and zarr for run stores; `app/api` adds FastAPI and uvicorn. The viewer needs Node (`npm install` in `app/visualiser`).

Run everything from the repository root.

## Tests

Every Python unit file defines `t()`; the runners find files, import them and call it.

```
python tests.py --all             # terrasim2: every file
python tests.py <file>            # one file
python tests.py                   # only files edited since they last passed (hash cache in .tests_cache.json)
python tests.py --watch           # keep running: rerun a file in a fresh subprocess when it is saved; a: all, q: quit
python troi_ingest/tests.py --all # PASS / SKIP / FAIL; SKIP where a store is not reachable
python app/api/tests.py --all
cd app/visualiser && npm test     # vitest; `npm run test:changed` runs only files edited since the last commit
```

A file's hash is recorded only when its `t()` passes, so `tests.py` without arguments is the counterpart of `vitest --changed`.

## Branches and pull requests

- Work goes on feature branches with one pull request each. There is no `dev` branch.
- `main` is the release line. `soil-physics-with-python` is a long-lived branch for programming modules of *Soil Physics with Python*; work for it goes on branches off it, with one pull request each into it. The model, evaluation and lever work of November 2026 landed there (PRs 14–28).
- Each pull request's description records what was measured, so the branch history doubles as the evaluation log ([history.md](history.md)).

## Conventions

The rules in [overview.md](overview.md) are enforced by review, not tooling: one unit per file, verbs for functions, units in docstrings, a `t()` in every file, no bundling. `CLAUDE.md` at the root is the compact statement of them, with the current tree; keep it current when adding a file.

## Regenerating the committed data

`data/dev_sites/` holds about 17 MB of prepared inputs, observations and vegetation maps. Regenerate when the inputs' format version, the site table or the observation file changes:

```
python -m troi_ingest.f.ingest_sites                 # every site in data/dense_sites.csv → {out_dir}/{stub}/model_inputs
python -m troi_ingest.f.ingest_site_observations     # every site with observations → {out_dir}/{stub}/observations
python -m troi_ingest.f.ingest_site_vegetation       # every site → {out_dir}/{stub}/vegetation
```

then copy the folders into `data/dev_sites/{stub}/`. The example region's inputs (`example`) are regenerated the same way from its own `Troi`. Bump `ModelInputs.FORMAT_VERSION` (or the observations' or vegetation map's) whenever the layout changes; the loaders refuse other versions.

## Evaluating a site

The evaluation scripts that produced the settings and scores in [evaluation.md](evaluation.md) are not part of the package; they run the steps directly on a committed site and score the result. The service's comparison route and the viewer's comparison panel are the in-product equivalent, with the differences noted in [observations.md](observations.md).

<!-- nav -->
← [Visualiser](visualiser.md) · [Index](README.md) · [History](history.md) →
<!-- /nav -->
