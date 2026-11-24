# Observations

<!-- nav -->
← [Vegetation](vegetation.md) · [Index](README.md) · [Evaluation](evaluation.md) →
<!-- /nav -->

Field measurements of volumetric water content are prepared once by `troi_ingest`, stored beside each site's inputs, and paired with a run cell by cell and day by day.

## The object

`SiteObservations` (`terrasim2/k/site_observations.py`) holds one record per point:

- `dates` (datetime64[D]), `row`, `col`;
- `station`, an index into `stations`;
- `depth_top` and `depth_bottom` (m);
- `vwc` (m³/m³);
- `n`, the number of readings averaged into the record.

It also carries `meta`. `survey_dates` lists the distinct dates, and `select_day(date)` and `select_layer(top, bottom)` return index arrays.

On disk: `data/dev_sites/{stub}/observations/manifest.json` and `observations.npz`, written and read by `write_site_observations` and `load_site_observations` (`SiteObservations.FORMAT_VERSION` = 1).

## Preparation

The source is the lab's compiled file `~/Downloads/Dense_sites/all_sites_observations.parquet`, which is outside the repository and described in `data/dense_sites.md`. `troi_ingest.f.ingest_observations(stub)`:

1. selects the site's rows (`SITE_SOURCES` maps stubs to the file's site names);
2. places each point on the site's 10 m window (`locate_points_on_window`);
3. drops, and counts in `meta`, points outside the window, outside the site's dates, or with a content that is non-finite or outside [0, 1];
4. averages each station's readings per day and depth interval, weighted by the number of readings in each.

`python -m troi_ingest.f.ingest_site_observations [stubs]` writes all sites. No other correction or quality control is applied. Sensor calibration is as delivered in the compiled file.

| Site | Instrument | Records | Stations | Days with data | Period | Depth intervals (m) |
|---|---|---|---|---|---|---|
| Tarrawarra | TDR survey on a 10 × 20 m grid | 8,644 | 3,610 points | 19 (13 surveys) | 1995-09-25 to 1996-11-29 | 0–0.3 |
| Esdale | Hand campaign on 9 dates, plus 7 loggers | 2,767 | 86 | 360 | 2025-04-30 to 2026-07-01 | 0–0.076 (campaign), 0–0.1 (loggers) |
| MRI (Mulloon) | Logger profiles | 179,287 | 18 | 1,930 | 2020-09-25 to 2026-06-03 | 0.1 m intervals from 0.05 to 1.55 |
| Llara | Logger profiles, two clusters | 366,240 | 32 | 955 | 2021-10-19 to 2024-06-30 | 0.1 m intervals from 0.05 |
| SASMAS Stanley | Station profiles | 8,936 | 7 | 1,452 | 2003-01-10 to 2006-12-31 | 0–0.3, 0–0.6, 0–0.9 |

Nerrigundah has no records in the compiled file.

## Pairing

`pair_run_with_observations(result, observations, hydraulics, days_available)` returns, for each record, the run's θ = θwp + moisture / root depth at its cell and date. It reads the store in blocks of days. Records outside the run's dates or beyond `days_available` get NaN.

The function ignores each record's depth interval. Matching a depth interval to the model's single root-zone store is left to the caller:

- The service pairs every record, at whatever depth it was measured.
- The evaluation selects and averages layers per site ([evaluation.md](evaluation.md)).

## Scores

`score_pairs(observed, modelled)` drops non-finite pairs and returns n, both means, bias (modelled − observed), RMSE, unbiased RMSE, Pearson r, Nash–Sutcliffe efficiency (NSE) and Kling–Gupta efficiency (KGE). `score_pairs_by_key` returns the same per value of a key (date or station), keys sorted.

The evaluation reports three summaries:

- the whole-run scores;
- the mean of the per-date r over dates with at least 20 records, which measures the spatial pattern within a day;
- the mean of the per-station r over stations with at least 30 records, which measures timing at a point.

## In the service and viewer

`GET /runs/{id}/comparison` returns the scores overall, per date and per station for the days written, or 404 for a site without observations. `GET /runs/{id}/pairs` returns six float32 columns: `t`, `row`, `col`, `station`, `observed`, `modelled` ([service.md](service.md), [visualiser.md](visualiser.md)).
