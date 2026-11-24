# Vegetation

<!-- nav -->
← [Runs](runs.md) · [Index](README.md) · [Observations](observations.md) →
<!-- /nav -->

A vegetation map classifies each cell as tree or grass from one year of Sentinel-2 NDVI. The service uses it for two optional settings: a tree root depth, and a demand factor. The model does not use it unless a request sets one of these.

## The map

`VegetationMap` (`terrasim2/k/vegetation_map.py`) holds per cell `class_index` (0 grass, 1 tree, −1 unknown) and the NDVI `low`, `median` and `high`, which are the 10th, 50th and 90th percentiles over the year. Its methods:

- `compute_fraction(class)` gives the share of cells in a class.
- `compute_root_depth(depth per class, unknown depth)` gives a depth field.
- `compute_crop_coefficient()` gives a crop coefficient from `low`.

On disk: `data/dev_sites/{stub}/vegetation/manifest.json` and `vegetation.npz`, written and read by `write_vegetation_map` and `load_vegetation_map` (`VegetationMap.FORMAT_VERSION` = 1).

## Classification

`classify_vegetation(low, high, VegetationThresholds)` classifies a cell as tree where `low` ≥ `tree_low_min` (0.4) and `high` − `low` ≤ `tree_amplitude_max` (0.2), and as grass otherwise. A cell with fewer than 8 cloud-free observations in the year is unknown. The thresholds were set by hand. They have not been checked against mapped tree cover at any site.

The year of imagery is the 12 months ending on the site's end date, if Sentinel-2 (from July 2015) covers them, else calendar 2023 (`choose_reference_period`). Tarrawarra, SASMAS Stanley and Nerrigundah predate Sentinel-2, so their maps describe 2023, not their observation periods.

| Site | Tree share | Imagery |
|---|---|---|
| Tarrawarra | 17.8% | 2023 |
| Esdale | 1.7% | 2025-07-02 to 2026-07-01 |
| MRI | 34.4% | 2025-06-04 to 2026-06-03 |
| Llara | 7.7% | 2023-07-02 to 2024-06-30 |
| SASMAS Stanley | 0.7% | 2023 |
| Nerrigundah | 6.7% | 2023 |

`load_ndvi_features` (troi_ingest) computes the percentiles and clear-look counts from the lab's Sentinel-2 cube. `python -m troi_ingest.f.ingest_site_vegetation [stubs]` writes the maps.

## Tree root depth

When a `RunRequest` sets `tree_root_depth`, tree cells take that depth and all other cells, unknown included, take `root_depth` (`compute_root_depth_field`). Capacity and hydraulics are then computed per cell. This setting has not been evaluated. MRI, the site with the most tree cover, has four logger profiles with the layers needed for scoring.

## Demand factor (cover)

`compute_crop_coefficient(ndvi, ndvi_bare=0.1, ndvi_full=0.7, kc_bare=0.3, kc_full=1.1)` maps the NDVI low linearly to a crop coefficient Kc, clipped to [0.3, 1.1], with NaN passed through. The service's `compute_demand_factor` returns (Kc / grid-mean Kc)^`cover_strength`, with 1 where Kc is NaN. `run_model` multiplies the reference evapotranspiration by this factor every day. The linear NDVI-to-Kc mapping is the one TerraSim version 1 used. Its end points are fixed defaults and were not fitted to any site.

`cover_strength` defaults to 0, which sets no factor. The evaluation chose 4 at Esdale and 0 elsewhere ([evaluation.md](evaluation.md)).
