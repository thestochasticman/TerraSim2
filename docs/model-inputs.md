# Model inputs

<!-- nav -->
← [Overview](overview.md) · [Index](README.md) · [Soil](soil.md) →
<!-- /nav -->

`troi_ingest` prepares inputs and `terrasim2` reads them. They are exchanged as a `ModelInputs` object (`terrasim2/k/model_inputs.py`), in memory or as a folder on disk.

## The object

| Attribute | Type | Content |
|---|---|---|
| `grid` | `TerrainGrid` | `elevation` (m), `capacity` (mm) and `moisture` (mm) on `(rows, cols)` cells of `cell_size` m |
| `cell_map` | `CellToTileMap` | The SILO tile each cell reads |
| `rain`, `pet` | `TileSeries` | Daily rain and SILO `et_short_crop` reference evapotranspiration, mm, one column per tile, same dates |
| `soil` | `SoilLayers` or `None` | Per SLGA pixel and layer: plant-available fraction, texture class, Campbell parameters; a second `CellToTileMap` onto the pixels; the layer bounds; the `SoilConventions` used |
| `root_depth` | float or `(rows, cols)` array, m | The depth `capacity` was computed for |
| `latitude` | float, degrees | Middle of the bounding box; used for the solar ratio |
| `demand_factor` | `(rows, cols)` array or `None` | Multiplies the reference evapotranspiration each day. Set at run time; never written to disk |
| `meta` | dict | Provenance: stub, bbox, window, tiles, sources |

The constructor checks that `rain` and `pet` share dates, that each tile map indexes its source, and that the soil layers match the grid's shape.

`capacity` is the plant-available fraction summed over the soil layers within the root depth, in mm ([soil.md](soil.md)). `capacity.npy` holds it for the root depth in the manifest. `load_model_inputs(folder, root_depth)` recomputes it from the stored layers for another depth.

## On disk: format version 4

`write_model_inputs` and `load_model_inputs` (`terrasim2/f/`) define one folder per site. `load_model_inputs` refuses a folder whose `version` differs from `ModelInputs.FORMAT_VERSION` (4). Reading a folder needs only NumPy and the standard library.

| File | Content |
|---|---|
| `manifest.json` | `version`, `rows`, `cols`, `cell_size`, `n_tiles`, `start`, `end`, `n_days`, `variables`, `root_depth`, `latitude`, `written_at`, `meta`, and a `soil` block: `layer_bounds` (m), `n_tiles`, `textures`, file names, `conventions` (J/kg) and units |
| `elevation.npy` | `(rows, cols)` float, m |
| `capacity.npy` | `(rows, cols)` float, mm, at the manifest's root depth |
| `tile_index.npy` | `(rows, cols)` int, SILO tile per cell |
| `rain.csv`, `pet.csv` | `date`, then one column per tile, mm |
| `soil_tile_index.npy` | `(rows, cols)` int, SLGA pixel per cell |
| `soil_fraction.npy` | `(layers, pixels)`, plant-available fraction, m³/m³ |
| `soil_texture.npy` | `(layers, pixels)`, index into the twelve USDA classes |
| `soil_campbell.npy` | `(3, layers, pixels)`: θs (m³/m³), ψe (J/kg), b (dimensionless) |

`write_model_inputs` refuses a root-depth field. A folder carries one depth.

`troi_ingest.ingest_to_disk(troi)` writes to `{troi.out_dir}/model_inputs`. It skips writing when a manifest with the same version, stub, bbox and dates already exists there.

## Committed sites

`data/dev_sites/{stub}/` holds inputs for the lab example region and the six sites in `data/dense_sites.csv`, produced by `python -m troi_ingest.f.ingest_sites` and copied in. Tests in `terrasim2` and `app/api` read these folders and need no data store.

| Stub | Grid (rows × cols) | Days | Period | Observations | Vegetation map |
|---|---|---|---|---|---|
| `example` | lab example region | 31 | January 2024 | no | no |
| `tarrawarra` | 72 × 97 | 432 | 1995-09-25 to 1996-11-29 | yes | yes |
| `esdale` | 242 × 290 | 428 | 2025-04-30 to 2026-07-01 | yes | yes |
| `mri` | 901 × 444 | 2,078 | 2020-09-25 to 2026-06-03 | yes | yes |
| `llara` | 189 × 397 | 986 | 2021-10-19 to 2024-06-30 | yes | yes |
| `sasmas_stanley` | 132 × 223 | 1,461 | 2003-01-01 to 2006-12-31 | yes | yes |
| `nerrigundah` | 98 × 107 | 545 | 1997-04-24 to 1998-10-20 | no | yes |

Tarrawarra, SASMAS Stanley and Nerrigundah predate Sentinel-2. Their vegetation maps are made from 2023 imagery and may not describe the cover during their observation periods ([vegetation.md](vegetation.md)).
