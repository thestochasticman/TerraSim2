# Vegetation

<!-- nav -->
← [Runs](runs.md) · [Index](README.md) · [Observations](observations.md) →
<!-- /nav -->

A site's vegetation enters the model as a map of what grows on each cell, made from a year of Sentinel-2 NDVI, and is used for two levers: a root depth per class and a demand factor per cell.

## The map

`VegetationMap` (`terrasim2/k/vegetation_map.py`) holds, per cell, `class_index` (0 grass, 1 tree, −1 unknown) and the NDVI `low`, `median` and `high` it was classified from (the 10th, 50th and 90th percentiles over the reference period). `compute_fraction(class)` gives the share of cells; `compute_root_depth(depth per class, unknown depth)` gives a `(rows, cols)` field; `compute_crop_coefficient()` gives a coefficient per cell from the low.

On disk it is `data/dev_sites/{stub}/vegetation/`: `manifest.json` (`version`, `rows`, `cols`, `classes`, `features`, `fraction`, `n_unknown`, `file`, `units`, `written_at`, `meta`) and `vegetation.npz`. `write_vegetation_map` and `load_vegetation_map` define the layout (`VegetationMap.FORMAT_VERSION` = 1); the loader refuses other versions or other class lists.

## Classification

`classify_vegetation(low, high, VegetationThresholds)` calls a cell a tree where the low stays at or above `tree_low_min` (0.4) and the swing high − low is at most `tree_amplitude_max` (0.2): an evergreen canopy keeps its greenness through the brownest season and moves by a fifth or less, while grass browns off. Cells with too few clear looks are −1.

The reference period is the site's own last year when the Sentinel-2 archive covers it, else calendar 2023 (`choose_reference_period`); `load_ndvi_features` takes the percentiles and the count of clear looks per cell from the lab's cube; `ingest_vegetation` assembles the map with provenance; `python -m troi_ingest.f.ingest_site_vegetation [stubs]` writes every site and checks the shape against the committed inputs. At Esdale 2% of cells are trees, along the tree lines and the riparian strip.

## Root depth per class

A `RunRequest` with `tree_root_depth` makes tree cells that deep and the rest `root_depth` (`compute_root_depth_field`); `SoilLayers.compute_hydraulics`, `SoilHydraulics`, `ModelInputs` and `load_model_inputs` all accept a field. At MRI, with a third of its cells under trees, the eighteen logger profiles were too few to test the lever.

## The cover lever

`compute_crop_coefficient(ndvi, ndvi_bare=0.1, ndvi_full=0.7, kc_bare=0.3, kc_full=1.1)` maps the NDVI low linearly onto an FAO-56 crop coefficient between bare ground and a closed canopy, NaN passing through. The service's `compute_demand_factor` divides it by its grid mean and raises it to the request's `cover_strength`, 1 where the map is unknown; `run_model` multiplies the reference evapotranspiration by it before every step. The division keeps the site's mean demand at the reference, so only the arrangement of demand within the site changes.

The strength is a site setting with a physical default of 0. At Esdale the hand campaign showed persistent cover lowering water content independently of aspect (partial r −0.56), and the lever at 4 raised the within-survey correlation from −0.13 to 0.33; at Tarrawarra's pasture any strength above 0 lowered it. See [evaluation.md](evaluation.md).

<!-- nav -->
← [Runs](runs.md) · [Index](README.md) · [Observations](observations.md) →
<!-- /nav -->
