# Terrain

<!-- nav -->
← [Soil](soil.md) · [Index](README.md) · [Process steps](process-steps.md) →
<!-- /nav -->

`TerrainDerivatives` (`terrasim2/k/terrain_derivatives.py`) computes quantities from the elevation grid and the site's latitude. `run_model` builds one per run. Each property is computed on first access and cached.

| Property | Shape, unit | Content | Function |
|---|---|---|---|
| `filled` | (rows, cols), m | Elevation with depressions raised to their spill level plus a small gradient, so every cell drains to the grid edge | `fill_pits` (priority flood) |
| `downstream` | (rows, cols), flat index | The one neighbour of eight with the steepest descent (D8); −1 at outlets | `compute_flow_direction` |
| `slope` | (rows, cols), m/m | Drop to that neighbour divided by the centre-to-centre distance; 0 at outlets | `compute_flow_direction` |
| `order` | (cells,), flat index | Every cell after all cells that drain into it | `compute_flow_order` |
| `upslope_cells` | (rows, cols), count | Cells draining through each cell, itself included | `compute_upslope_cells` |
| `flow_levels` | `(cells, bounds)`, flat indices | Cells grouped by the length of the longest flow path ending in each; every cell draining into a cell is in an earlier group | `compute_flow_levels` |
| `surface_slope`, `aspect` | (rows, cols), rad | Tilt of the unfilled surface by central differences, and the downslope direction clockwise from north | `compute_slope_aspect` |
| `solar_ratio` | (rows, cols), dimensionless | Direct clear-sky irradiance on the tilted surface summed over a year, divided by the same sum for a horizontal surface | `compute_solar_ratio` |

## Use in the model

- The routed and subsurface steps pass water from each cell to `downstream[cell]`, processing the groups of `flow_levels` in turn (`cascade_downhill`). One neighbour receives all of a cell's flow, so flow does not divide.
- The subsurface step's lateral flow uses `slope` (the D8 slope), not `surface_slope`.
- `solar_ratio` scales evaporative demand when `aspect_strength` is above 0 ([process-steps.md](process-steps.md)). It counts the direct beam only, with no diffuse light, no cloud and no shading by surrounding terrain. The sun's position is sampled at the middle of each hour of days 1 to 365, at the latitude in the manifest.
- `upslope_cells` is used by the viewer's drainage colouring only.

## Resolution

Elevation is the Copernicus GLO-30 DEM bilinearly resampled to the 10 m lattice. Slope, aspect, solar ratio and the flow network have the resolution of the 30 m source, not of the 10 m grid. Pit filling removes real closed depressions along with artefacts.

At Tarrawarra (72 × 97 cells) the window spans 70 to 112 m elevation, `fill_pits` raises 79 cells, there are 4 outlets, the largest `upslope_cells` value is 3,278, the mean surface slope is 4.5° (maximum 21°), and the solar ratio ranges from 0.71 to 1.13.
