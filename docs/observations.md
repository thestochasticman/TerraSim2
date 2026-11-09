# Observations

<!-- nav -->
← [Vegetation](vegetation.md) · [Index](README.md) · [Evaluation](evaluation.md) →
<!-- /nav -->

Field observations are held the same way as inputs: prepared once by the ingest, written to a versioned folder beside the site, and read by the model's own loader. A run is then paired with them cell by cell and day by day, and scored.

## The object

`SiteObservations` (`terrasim2/k/site_observations.py`) is a set of point measurements of volumetric water content on a grid's cells: for each point its `dates` (datetime64[D]), `row`, `col`, `station` (an index into `stations`), `depth_top` and `depth_bottom` (m), `vwc` (m³/m³) and `n` (readings averaged into it), with `meta` provenance. `survey_dates` lists the distinct dates; `select_day(date)` and `select_layer(top, bottom)` return index arrays.

On disk: `data/dev_sites/{stub}/observations/manifest.json` (`version`, `rows`, `cols`, `n_points`, `stations`, `start`, `end`, `n_dates`, `file`, `columns`, `written_at`, `meta`) and `observations.npz`. `write_site_observations` and `load_site_observations` define the layout (`SiteObservations.FORMAT_VERSION` = 1).

## Preparation

The lab's compiled file (`~/Downloads/Dense_sites/all_sites_observations.parquet`, described in `data/dense_sites.md`) holds every site's readings in one table. `troi_ingest.f.ingest_observations(stub)` reads the rows for the site (`SITE_SOURCES` maps stubs to the file's site names), locates each point on the site's window (`locate_points_on_window`), drops and counts points outside it, and averages a station's readings per day and depth interval. `python -m troi_ingest.f.ingest_site_observations [stubs]` writes every site that has observations and checks the shape against the committed inputs. Nerrigundah has no observations in the compiled file.

| Site | What was measured | Stations | Dates | Depths |
|---|---|---|---|---|
| Tarrawarra | TDR campaigns on a 10 × 20 m grid, 1995–96 | 3,610 points over 13 surveys | 19 survey days | 0–0.3 m |
| MRI (Mulloon) | Logger profiles, 2020–26 | 18 | daily | 0.05–1.55 m in 0.1 m steps |
| Esdale | Hand campaign on 9 dates plus 7 loggers, 2025–26 | 86 | 9 campaign dates plus daily loggers | 0–7.6 cm (campaign), 0–0.1 m (loggers) |
| Llara (Narrabri) | Logger profiles in two clusters, 2021–24 | 32 | daily | 0.05–0.35 m and deeper |
| SASMAS Stanley | Station profiles, 2003–06 | 7, two reporting 0–0.3 m | daily | 0–0.3 m and deeper |

## Pairing

`pair_run_with_observations(result, observations, hydraulics, days_available)` reads the run at each observation's day and cell as a water content over the root depth, θwp + stored / depth (`compute_water_content`), in blocks of days so a store on disk is decompressed once; points beyond the days written are NaN. The caller decides how an observation's depth interval relates to the model's store: the service pairs every reading at the run's root depth and says so in its caption; the evaluation reads each site's layers against the store explicitly ([evaluation.md](evaluation.md)).

## Scores

`score_pairs(observed, modelled)` returns n, the two means, bias, RMSE, unbiased RMSE, r, Nash–Sutcliffe efficiency and Kling–Gupta efficiency, dropping non-finite pairs; these are the scores TerraSim v1 used. `score_pairs_by_key` returns the same per group of a key, keys sorted: per survey date gives the level and the spatial pattern on each day; per station gives each probe's timing.

The three questions are kept separate because a model can have the catchment mean right and its arrangement wrong, or the reverse: the whole-run scores answer the level and timing, the mean of the per-date r answers the spatial pattern, and the mean of the per-station r answers the timing at a point.

## In the service and the viewer

`GET /runs/{id}/comparison` returns the scores overall, per survey date (with the run's day index) and per station, for the days written, or 404 for a site without observations; `GET /runs/{id}/pairs` returns every observation with the run's value at it as six float32 columns. The viewer puts the day's points on the terrain as markers coloured by the measured content or by modelled minus observed, shows a table per survey that seeks the scrubber, and plots modelled against observed with the shown day in full ([visualiser.md](visualiser.md)).

<!-- nav -->
← [Vegetation](vegetation.md) · [Index](README.md) · [Evaluation](evaluation.md) →
<!-- /nav -->
