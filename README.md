# TerraSim2

Process-based soil moisture modelling on terrain, with a React app for visualising the simulation.

## What is in the repo

| part | what it is | depends on |
|---|---|---|
| `terrasim2/` | the model: grid, tiles, bucket step, run loop, input reader and writer | numpy |
| `troi_ingest/` | prepares model inputs from a `Troi` by reading the lab data stores and projecting onto the Sentinel-2 grid | troi, pycopdem, pysilo, pysentinel2, rioxarray, and `terrasim2` |
| `data/` | `dense_sites.csv` and `dense_sites.md`: the validation sites with bbox, dates and caveats | |
| `dev_data/{stub}/model_inputs/` | committed prepared inputs: the lab's example region and the six validation sites | |
| `app/` | Next.js + TypeScript 3D terrain viewer | node |

`terrasim2` never imports `troi_ingest` or any lab package. The handoff between them is a `ModelInputs` object, in memory or as a folder on disk.
