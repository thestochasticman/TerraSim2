# Development

<!-- nav -->
← [Visualiser](visualiser.md) · [Index](README.md) · [History](history.md) →
<!-- /nav -->

## Environment

- **Python.** The lab's `borevitz_lab` conda environment, currently Python 3.11.15. `CLAUDE.md` asks for Python 3.12 syntax; the code uses no feature beyond 3.11 and runs in this environment.
- **Ingest.** `troi_ingest` needs the lab packages `troi`, `pysilo`, `pycopdem`, `pyslga` and `pysentinel2`, plus `rasterio` and `pandas`.
- **Model.** `terrasim2` needs NumPy, and zarr for run stores.
- **Service.** `app/api` adds FastAPI, pydantic and uvicorn.
- **Viewer.** Node, run in `app/visualiser` after `npm install`. Node 22.23 is in use, with Next.js 16.4.3, React 19.3 and three.js 0.186.

There is no lock file for the Python dependencies and no environment specification in the repository. Run every command from the repository root unless stated otherwise.

## Tests

Every Python unit file defines `t()`, which raises `AssertionError` on failure.

```
python tests.py --all              # terrasim2: every file
python tests.py <file> [...]       # given files
python tests.py                    # files changed since they last passed (hash cache in .tests_cache.json)
python tests.py --watch            # re-run a file in a subprocess when it is saved; a: all, q: quit
python troi_ingest/tests.py --all  # PASS / SKIP / FAIL; SKIP where a store is unreachable
python app/api/tests.py --all      # PASS / SKIP / FAIL
cd app/visualiser && npm test      # vitest
```

A file's hash is recorded only when its `t()` passes. On 24 November 2026, with the code at `4f45710`, all 64 `terrasim2` files and all 21 `app/api` files passed.

No continuous integration runs these tests. Tests confirm each unit's behaviour on small hand-computed or random cases. Physical correctness rests on the cited equations and on the evaluation in [evaluation.md](evaluation.md).

## Branches and pull requests

- Work goes on feature branches, one pull request each.
- `main` received pull requests 1 to 13 and 31.
- `soil-physics-with-python` is a long-lived branch for work following *Soil Physics with Python*. It received pull requests 14 to 28. Work for it branches from it and returns to it by pull request.
- There is no `dev` branch and there are no release tags.

## Conventions

The conventions in [overview.md](overview.md) are enforced by review only. `CLAUDE.md` states them and lists the file tree. Update the tree when adding a file.

## Regenerating the committed data

`data/dev_sites/` holds 27 MB of inputs, observations and vegetation maps. Regenerate them when a format version, `data/dense_sites.csv` or the compiled observation file changes. This needs the lab's stores.

```
python -m troi_ingest.f.ingest_sites                 # inputs      → {out_dir}/{stub}/model_inputs
python -m troi_ingest.f.ingest_site_observations     # observations → {out_dir}/{stub}/observations
python -m troi_ingest.f.ingest_site_vegetation       # vegetation  → {out_dir}/{stub}/vegetation
```

Then copy the folders into `data/dev_sites/{stub}/` by hand. When a layout changes, increase the relevant `FORMAT_VERSION`; the loaders refuse other versions.

## Evaluation scripts

The scripts that produced [evaluation.md](evaluation.md) and the figures in `docs/figures/` are not in the repository. The service's comparison route is the only scoring path in the repository, and it differs from the evaluation as described in [service.md](service.md).
