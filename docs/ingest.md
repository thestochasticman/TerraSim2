# Ingest

<!-- nav -->
← [Evaluation](evaluation.md) · [Index](README.md) · [Service](service.md) →
<!-- /nav -->

`troi_ingest` turns a `Troi` (the lab's description of a region and date range, with a `Config` naming the data stores) into the folders the model reads. It is the only program that reads a data store or imports a lab package. It imports `terrasim2` to build its objects. `terrasim2` does not import `troi_ingest`.

Running it requires the lab's stores and packages. Without them its tests report SKIP. The committed folders in `data/dev_sites/` were produced by it and are what the rest of the repository uses.

## Sources and treatment

| Quantity | Source | Native resolution | Read through | Treatment |
|---|---|---|---|---|
| Rain, reference evapotranspiration | SILO `daily_rain`, `et_short_crop` (FAO-56 short crop) | 0.05° | `pysilo` | Each cell centre snapped to the nearest SILO point; one series per distinct point (`compute_silo_tiles`, `load_silo_series`) |
| Elevation | Copernicus GLO-30 | 30 m | `pycopdem` | Bilinear resampling onto the 10 m window (`load_elevation`) |
| Soil | SLGA v2 clay, sand, silt, bulk density, six depths | 90 m | `pyslga` | Nearest pixel per cell (`compute_slga_tiles`); each layer through `prepare_soil_layer` (`load_soil_layers`) |
| Vegetation | Sentinel-2 analysis-ready data (Digital Earth Australia), NDVI | 10 m | `pysentinel2` | Cloud-masked; 10th, 50th, 90th percentiles and clear-look count per cell over one year (`load_ndvi_features`) |
| Observations | The lab's compiled dense-site parquet | points | `pandas` | Placed on the window, filtered, averaged per station, day and depth (`ingest_observations`) |

## The window

`compute_window(bbox)` returns the `(row0, row1, col0, col1)` of the 10 m EPSG:6933 lattice that covers the bounding box. Every source is placed on this window, so inputs, observations and vegetation maps share rows and columns. `locate_points_on_window(lon, lat, bbox)` places points on it.

## Functions and commands

| Function | Result |
|---|---|
| `ingest(troi)` | `ModelInputs` in memory, with soil layers, capacity at `ROOT_DEPTH` (0.3 m), latitude and provenance |
| `ingest_to_disk(troi)` | The same written to `{troi.out_dir}/model_inputs`; skipped if a manifest with the same version, stub, bbox and dates exists |
| `read_dense_sites()` | `data/dense_sites.csv` as one dict per site |
| `make_site_troi(stub, config)` | A `Troi` for one site |
| `ingest_sites(stubs)` | `python -m troi_ingest.f.ingest_sites [stubs]`: inputs for every site, or the given stubs |
| `ingest_observations(stub)` | `SiteObservations` for one site |
| `ingest_site_observations(stubs)` | `python -m troi_ingest.f.ingest_site_observations [stubs]`: writes `{out_dir}/{stub}/observations`; checks the shape against the committed inputs |
| `choose_reference_period(start, end)` | The year of imagery for a vegetation map |
| `ingest_vegetation(stub, thresholds)` | `VegetationMap` for one site |
| `ingest_site_vegetation(stubs)` | `python -m troi_ingest.f.ingest_site_vegetation [stubs]`: writes `{out_dir}/{stub}/vegetation`; checks the shape against the committed inputs |
| `make_test_troi()` | A `Troi` for the example region, for tests |

The outputs are written under the `troi` output directory. Copying them into `data/dev_sites/{stub}/` is a manual step ([development.md](development.md)).

## Provenance

Each manifest's `meta` records the stub, bbox, CRS, window, tiles, root depth and a `sources` block that names each dataset and its treatment in words. The manifest's `soil.conventions` records the suctions at which the soil fraction was read.
