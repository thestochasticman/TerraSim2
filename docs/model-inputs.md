# Model inputs

<!-- nav -->
← [Overview](overview.md) · [Index](README.md) · [Soil](soil.md) →
<!-- /nav -->

The model assumes its inputs are already prepared. `troi_ingest` prepares them; `terrasim2` consumes them. The object they exchange is `ModelInputs` (`terrasim2/k/model_inputs.py`).

## The object

| Attribute | Type | What it is |
|---|---|---|
| `grid` | `TerrainGrid` | Elevation, capacity and moisture arrays on `(rows, cols)` cells of `cell_size` m (10 m on the Sentinel-2 lattice) |
| `cell_map` | `CellToTileMap` | Which tile of the climate source each cell reads; one map per source lattice |
| `rain`, `pet` | `TileSeries` | Daily rainfall and short-crop reference evapotranspiration, mm, one column per tile, on the same dates |
| `soil` | `SoilLayers` or `None` | The layered soil per SLGA pixel: a second `CellToTileMap` onto the 90 m pixels, the layer bounds, and per pixel and layer the plant-available fraction, the textural class and the Campbell curve parameters, with the `SoilConventions` the fraction was read at |
| `root_depth` | `float` or `(rows, cols)` array | The depth the capacity was computed for; a field when roots differ by vegetation class |
| `latitude` | `float` | Degrees, the bounding box's middle; what the sun's path over the terrain is computed from |
| `demand_factor` | `(rows, cols)` array or `None` | A positive field the reference evapotranspiration is multiplied by before every step; set at run time by the cover lever, never written to disk |
| `meta` | `dict` | Free-form provenance: stub, bbox, window, tiles, sources |
| `dates`, `n_days`, `shape` | | Derived from the series and the grid |

The constructor checks that the series share dates, that the tile maps index their sources, and that the soil layers lie on the grid.

A cell's capacity is the plant-available fraction summed over the soil layers the roots reach, in mm (`compute_capacity_map`). `capacity.npy` holds it for the root depth recorded in the manifest; `load_model_inputs(folder, root_depth)` recomputes it from the layers for another depth and records that depth instead. A run sees the soil as one `SoilHydraulics` built from the layers at the inputs' root depth ([soil.md](soil.md)).

## On disk: format version 4

One folder per site. `write_model_inputs` and `load_model_inputs` (`terrasim2/f/`) define the layout; `load_model_inputs` refuses any other `ModelInputs.FORMAT_VERSION`.

| File | Contents |
|---|---|
| `manifest.json` | `version`, `rows`, `cols`, `cell_size`, `n_tiles`, `start`, `end`, `n_days`, `variables`, `root_depth`, `latitude`, `written_at`, `meta`, and a `soil` block with `layer_bounds` (m), `n_tiles`, `textures`, the soil file names, the `conventions` (field-capacity and wilting-point suctions, J/kg) and units |
| `elevation.npy` | `(rows, cols)` float, m |
| `capacity.npy` | `(rows, cols)` float, mm over the manifest's root depth |
| `tile_index.npy` | `(rows, cols)` int, the climate tile each cell reads |
| `rain.csv`, `pet.csv` | `date` then one column per tile, mm |
| `soil_tile_index.npy` | `(rows, cols)` int, the SLGA pixel each cell reads |
| `soil_fraction.npy` | `(layers, pixels)` plant-available fraction, m³/m³ |
| `soil_texture.npy` | `(layers, pixels)` index into the twelve USDA classes |
| `soil_campbell.npy` | `(3, layers, pixels)`: θs (m³/m³), ψe (J/kg), b (dimensionless) |

`write_model_inputs` refuses a root-depth field: inputs on disk carry the producer's one depth. The manifest's `soil.conventions` records what the stored fraction was read between, and `SoilLayers` reads its hydraulics at the same suctions, so a folder written under one convention is never silently read under another.

`troi_ingest.ingest_to_disk(troi)` writes to `{troi.out_dir}/model_inputs` and skips the work when a manifest with the same version, stub, bbox and dates is already there.

## The committed sites

`data/dev_sites/{stub}/` holds prepared inputs for the lab example region (`example`, January 2024) and the six validation sites of `data/dense_sites.csv`, produced by `python -m troi_ingest.f.ingest_sites` and copied in. Observations (`observations/`) and vegetation maps (`vegetation/`) sit beside the inputs where they exist ([observations.md](observations.md), [vegetation.md](vegetation.md)). Everything in `terrasim2` and `app/api` that needs real inputs loads these; nothing in `terrasim2` ever calls `troi_ingest` or needs a data store.

| Site | Grid | Days | Observations | Vegetation map |
|---|---|---|---|---|
| `example` | lab example region | 31 | – | – |
| `tarrawarra` | 72 × 97 | 432 (1995-09-25 to 1996-11-29) | yes | yes |
| `esdale` | 242 × 290 | 428 | yes | yes |
| `mri` | 901 × 444 | 2078 | yes | yes |
| `llara` | 189 × 397 | 986 | yes | yes |
| `sasmas_stanley` | 132 × 223 | 1461 | yes | yes |
| `nerrigundah` | | 545 | none in the compiled file | yes |

Regenerate and re-copy the folders when the format version or the site table changes ([development.md](development.md)).

<!-- nav -->
← [Overview](overview.md) · [Index](README.md) · [Soil](soil.md) →
<!-- /nav -->
