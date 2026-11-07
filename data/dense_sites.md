# Dense soil moisture sites

Validation sites with dense in-situ soil moisture, evaluated from `~/Downloads/Dense_sites` on 2026-10-27.
The machine-readable version is `dense_sites.csv` in this folder. That file is the source of truth;
this page carries the same table plus the caveats.

Bboxes are west, south, east, north in EPSG:4326, the station extent padded by about 200 m.
Tarrawarra uses the bbox its own documentation prescribes.

| stub | site | centre (lat, lon) | bbox | extent | stations | dates |
|---|---|---|---|---|---|---|
| esdale | Esdale | -35.096, 148.933 | 148.918, -35.108, 148.948, -35.085 | 2.7 x 2.5 km | 78 campaign points + 7 Phenode loggers | campaign 2025-04-30 to 2025-07-17 (9 dates); Phenode 2025-06-10 to 2026-07-01 |
| llara | Llara | -30.259, 149.860 | 149.840, -30.267, 149.881, -30.250 | 4.0 x 1.9 km | 31 loggers in two clusters 2.5 km apart | 2021-10-19 to 2024-06-30 |
| mri | MRI (Mulloon) | -35.243, 149.608 | 149.585, -35.286, 149.631, -35.200 | 4.2 x 9.5 km | 18 loggers in three clusters | 2020-09-25 to 2026-06-03 |
| sasmas_stanley | SASMAS Stanley | -32.096, 150.134 | 150.122, -32.102, 150.145, -32.090 | 2.2 x 1.3 km | 7 of the 26 stations | 2003-01 to 2006-12 |
| tarrawarra | Tarrawarra | -37.656, 145.440 | 145.435, -37.659, 145.445, -37.652 | 0.9 x 0.7 km | 3610 point measurements, 13 survey dates | 1995-09-25 to 1996-11-29 |
| nerrigundah | Nerrigundah | -32.318, 151.716 | 151.711, -32.323, 151.722, -32.314 | 1.0 x 1.0 km | 13 TDR profiles + a 20 m grid campaign | 1997-04-24 to 1998-10-20; met and rain 1996 to 1998 |

## Caveats

- **Esdale is two observation sets of different kinds.** The campaign is 78 locations measured by hand on 9 separate dates, 2025-04-30 to 2025-07-17: dense in space, sparse in time, nine snapshots of the paddock. The Phenode loggers are 7 fixed sensors at 10 cm depth recording continuously from 2025-06-10 to 2026-07-01: dense in time, sparse in space. They overlap for about five weeks, June to mid July 2025. The campaign tests a modelled map; the loggers test a modelled time series. The CSV's single date range spans both. **The Phenode loggers are timing-only until calibrated.** All seven read 0.20–0.27 m³/m³ over the whole year, with means of 0.23–0.25 and 5th–95th percentiles about 0.21–0.26, through a winter and a summer in which the hand campaign on the same paddock went from 0.07 to 0.23 within a fortnight; on the five days both were read the loggers sat at 0.25 against the hand probe's 0.16–0.23. Their levels and amplitudes are compressed, as a generic factory calibration gives; their timing co-moves (pairwise r 0.72). Score the site on the campaign (stable from date to date, r 0.55 between dates across the 78 points), and use the overlap dates for a soil-specific calibration if the raw logger readings are kept.
- **Sentinel-2 only exists from mid-2015.** Esdale, Llara and MRI are fully covered. SASMAS Stanley, Tarrawarra and Nerrigundah predate it. SILO rain and the DEM cover every date, so the model runs on all six; anything needing imagery cannot.
- **SASMAS is a network, not a dense site.** Its 26 stations span 78 km. Only the Stanley cluster, S1 to S7, is dense. Station G6 alone runs to 2020-12.
- **MRI is three clusters** 9 km end to end. One bbox for now; three smaller ones would be tighter.
- **Nerrigundah's coordinates are inferred.** Raw data is on AGD66 AMG zone 56 and a local system. The bbox is the surveyed DEM's extent, 633 x 618 m, converted to lon-lat. TDR profile positions are in a PDF appendix, not parsed.
- **Tarrawarra** came through an upstream AGD66 conversion with a documented rotation. The bbox is from the converted points.
- **The source folder is a partial copy.** Its READMEs reference prepared observation files for Llara, MRI and Nerrigundah, and a `Validation_tables` folder, that are not present. Llara and MRI observations are in `all_sites_observations.parquet`. Nerrigundah has raw files only.

## Observations on disk

`python -m troi_ingest.f.ingest_site_observations` reads `all_sites_observations.parquet` (expected at `~/Downloads/Dense_sites/`, or pass another path) and writes one `observations/` folder per site with observations, copied into `data/dev_sites/{stub}/observations/`. Each folder is `manifest.json` plus `observations.npz` with one array per column: `dates`, `row`, `col` (the cell on the site's Sentinel-2 window), `station`, `depth_top`, `depth_bottom` (m), `vwc` (m3 m-3) and `n` (readings averaged). A station's readings on one day over one depth interval are averaged, weighted by `n`. Points outside the window or the site's dates are dropped and counted in the manifest's `meta`.

| stub | file sites | observations | stations | dates | depth intervals |
|---|---|---|---|---|---|
| esdale | esdale, phenode | 2,767 | 86 | 360 | 0–0.076 m (campaign), 0–0.1 m (Phenode) |
| llara | llara | 366,240 | 32 | 955 | 0.05–0.15 m and on in 0.1 m steps |
| mri | mri | 179,287 | 18 | 1,930 | 0.05–0.15 m and on in 0.1 m steps |
| sasmas_stanley | sasmas, the 7 Stanley stations inside the bbox | 8,936 | 7 | 1,452 | 0–0.3, 0–0.6, 0–0.9 m |
| tarrawarra | tarrawarra | 8,644 | 3,610 points | 19 (13 campaigns, some over two or three days) | 0–0.3 m |
| nerrigundah | none in the file | | | | |

## Vegetation maps on disk

`python -m troi_ingest.f.ingest_site_vegetation` reads a year of Sentinel-2 NDVI from the lab's cube for each site and writes `vegetation/` beside the inputs, copied into `data/dev_sites/{stub}/vegetation/`: `manifest.json` plus `vegetation.npz` with `class_index` (int8: 0 grass, 1 tree, −1 unknown) and the per-cell `low`, `median` and `high` (the 10th, 50th and 90th percentiles of NDVI over the year). The year is the site's own last year when the archive (from mid-2015) has it, else 2023. A cell is a tree where its low NDVI is at least 0.4 and its swing, high minus low, is at most 0.2: an evergreen canopy moves by a fifth or less over a year, while grass swings by a third to a half at a dry site and by a quarter at a temperate one whose pasture never browns off, so the swing is what carries between sites. The thresholds are in the manifest's `meta` with the imagery period.

| stub | imagery | NDVI low, median of cells | swing, median | tree share |
|---|---|---|---|---|
| esdale | 2025-07-02 to 2026-07-01 | 0.24 | 0.44 | 2 % |
| llara | 2023-07-02 to 2024-06-30 | 0.23 | 0.23 | 8 % |
| mri | 2025-06-04 to 2026-06-03 | 0.38 | 0.22 | 34 % |
| sasmas_stanley | 2023 | 0.25 | 0.17 | 1 % |
| tarrawarra | 2023 | 0.53 | 0.28 | 18 % |
| nerrigundah | 2023 | 0.43 | 0.27 | 7 % |

The tree share is sensitive to the swing cut where pasture stays green: at 0.25 instead of 0.2, tarrawarra reads 35 % and nerrigundah 33 %. The maps have not been checked against ground truth; the run page colours the terrain by class so they can be judged by eye.

## Source files used

- `all_sites_observations.parquet`: 590,330 rows; columns site, station, lon, lat, time, depth_top_m, depth_bottom_m, vwc, n. Covers esdale, llara, mri, phenode, sasmas, tarrawarra.
- `Tarrawarra/observations/tarrawarra_points_bbox.json` and `Tarrawarra/documentation/coordinate_conversion.md`.
- `Nerrigundah_data/raw/data/DEM/ACCURATE/nerrig-amg.xyz`, `TRANSFORM/trans-par.dat`, `CON-TDR/cTDR-*.dat`, `readme.txt`.
- `SASMAS/observations/sasmas_coordinates.csv`, `MRI_data/mri_logger_coordinate_crosswalk.csv`, `Llara_data/sm_probe_locs.csv`.
