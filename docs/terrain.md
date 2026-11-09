# Terrain

<!-- nav -->
← [Soil](soil.md) · [Index](README.md) · [Process steps](process-steps.md) →
<!-- /nav -->

Everything that follows from the shape of the terrain lives in one object, `TerrainDerivatives` (`terrasim2/k/terrain_derivatives.py`), built once per run from the grid and the site's latitude. Each quantity is a cached property computed on first use, so a step that ignores terrain pays nothing for it.

| Property | Shape | What it is | Function |
|---|---|---|---|
| `filled` | (rows, cols), m | The elevation with depressions raised to their spill level plus a faint slope, so every cell drains to an edge | `fill_pits` (priority flood) |
| `downstream` | (rows, cols), flat index or −1 | The one of eight neighbours each cell drains to by steepest descent; −1 at outlets | `compute_flow_direction` |
| `slope` | (rows, cols), m/m | The drop to that neighbour over the distance | `compute_flow_direction` |
| `order` | (cells,) flat indices | Cells upstream before downstream, so a cascade can be run in one pass; refuses non-descending directions | `compute_flow_order` |
| `upslope_cells` | (rows, cols), count | The number of cells draining through each cell, itself included | `compute_upslope_cells` |
| `surface_slope`, `aspect` | (rows, cols), rad | The ground's own tilt and the direction it faces (downslope, clockwise from north), by central differences on the unfilled surface | `compute_slope_aspect` |
| `solar_ratio` | (rows, cols), – | Direct clear-sky beam irradiance on the tilted ground over a year relative to flat ground at the same latitude; 1 on flat ground | `compute_solar_ratio` |

## What each is for

- `filled`, `downstream`, `slope` and `order` are what the routed and subsurface steps cascade along: surface excess and drainage move from each cell to its downstream cell in flow order within the day, and only outlets shed runoff ([process-steps.md](process-steps.md)).
- `upslope_cells` is the drainage view in the viewer (log scale) and the usual terrain index for where water accumulates.
- `solar_ratio` is what the aspect lever scales evaporative demand by. It integrates the direct beam over a year of sun paths at the site's latitude on each cell's slope and aspect; it is clear-sky and direct-beam only, which is one reason the fitted exponent at Tarrawarra exceeds one. The latitude comes from the inputs' manifest (the bounding box's middle).

## Resolution

The elevation is the Copernicus GLO-30 model resampled onto the 10 m lattice, so slope, aspect and irradiance carry a 30 m texture and the pit-filled flow network is correspondingly coarse. The 10 m cell size is the Sentinel-2 lattice's, chosen so that vegetation and the model share a grid; the terrain derivatives inherit the DEM's information content, not the grid's.

<!-- nav -->
← [Soil](soil.md) · [Index](README.md) · [Process steps](process-steps.md) →
<!-- /nav -->
