# Ingest

<!-- nav -->
← [Evaluation](evaluation.md) · [Index](README.md) · [Service](service.md) →
<!-- /nav -->

`troi_ingest` turns a `Troi` (the lab's description of a region and date range, with a `Config` naming the data stores) into the folders the model reads. It is the only program that touches a data store or a lab package. It imports `terrasim2` for the objects it builds; `terrasim2` never imports it.

## The stores

Each store fills itself on first contact and never downloads a pixel twice; the `troi` family of lab packages manages them under `troi.config`.

| Quantity | Source | Native | Package | Treatment |
|---|---|---|---|---|
| rain, demand | SILO `daily_rain` and `et_short_crop` (FAO-56 short crop) | 0.05° | `pysilo` | each cell reads its nearest SILO point; one column per tile (`compute_silo_tiles`, `load_silo_series`, `load_rain`, `load_pet`) |
| elevation | Copernicus GLO-30 | 30 m | `pycopdem` | bilinear onto the Sentinel-2 10 m lattice (`load_elevation`) |
| soil | SLGA v2 clay, sand, silt, bulk density at six depths | 90 m | `pyslga` | nearest pixel per cell (`compute_slga_tiles`); each layer through `prepare_soil_layer` (`load_soil_layers`) |
| vegetation | Sentinel-2 surface reflectance, one year of NDVI | 10 m, 5 days | `pysentinel2` | 10th, 50th and 90th percentiles and clear-look count per cell (`load_ndvi_features`) |
| observations | the lab's compiled dense-site parquet | points | pandas | located on the window; averaged per station, day and depth (`ingest_observations`) |

## The window

`compute_window(bbox)` fits a bounding box to the 10 m EPSG:6933 lattice and returns `(row0, row1, col0, col1)`; everything is projected onto that window, so the grid, the soil tiles, the climate tiles, the observations and the vegetation map all share rows and columns. `locate_points_on_window(lon, lat, bbox)` places points on it.

## Functions and commands

| Function | What it does |
|---|---|
| `ingest(troi)` | `Troi` → `ModelInputs` in memory with soil layers, capacity at `ROOT_DEPTH` (0.3 m), latitude, and provenance in `meta` |
| `ingest_to_disk(troi)` | Writes to `{troi.out_dir}/model_inputs`; skips the work when a manifest with the same version, stub, bbox and dates is already there |
| `read_dense_sites()` | `data/dense_sites.csv` → one dict per site (stub, bbox, start, end) |
| `make_site_troi(stub, config)` | A `Troi` for a site from the table |
| `ingest_sites(stubs)` | Every site (or the given stubs) to disk; `python -m troi_ingest.f.ingest_sites [stubs]` |
| `ingest_observations(stub)` | The site's observations on its window as a `SiteObservations` |
| `ingest_site_observations(stubs)` | Every site with observations to `{out_dir}/{stub}/observations`; `python -m troi_ingest.f.ingest_site_observations [stubs]`; checks the shape against the committed inputs |
| `choose_reference_period(start, end)` | The year of imagery a vegetation map is made from: the site's own last year within the archive, else 2023 |
| `ingest_vegetation(stub, thresholds)` | The reference period's NDVI features classified into a `VegetationMap` |
| `ingest_site_vegetation(stubs)` | Every site to `{out_dir}/{stub}/vegetation`; `python -m troi_ingest.f.ingest_site_vegetation [stubs]` |
| `make_test_troi()` | A `Troi` for the example region with a throwaway registry; tests only |

After running the three `ingest_site_*` commands, copy the folders into `data/dev_sites/{stub}/` so that the model's tests, the service and the viewer see them without a store ([development.md](development.md)).

## Provenance

The manifest's `meta` records the stub, bbox, CRS, window, tiles, root depth and a `sources` block naming each dataset and how it was treated, e.g. `"soil": "SLGA v2 clay, sand, silt and bulk density at six depths via pyslga, nearest 90 m pixel; Campbell curve from the geometric mean diameter (Bittelli et al. 2015 eqs. 2.36, 5.36, 5.37), theta_s = 1 - bulk density / 2650; available water between -10 and -500 J/kg (SoilConventions, calibrated against APSoil's measured limits)"`. The conventions the fraction was read at are in the manifest's `soil.conventions`, so a folder is never read under a different convention than it was written with.

<!-- nav -->
← [Evaluation](evaluation.md) · [Index](README.md) · [Service](service.md) →
<!-- /nav -->
