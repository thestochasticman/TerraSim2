# Soil

<!-- nav -->
← [Model inputs](model-inputs.md) · [Index](README.md) · [Terrain](terrain.md) →
<!-- /nav -->

The soil enters the model as a retention curve per cell, from which capacity, conductivity and the two stores' limits follow. This page describes the route from the soil map to those numbers, and the one calibration that was made to it.

## From the map to a curve

The Soil and Landscape Grid of Australia v2 gives clay, sand and silt fractions and bulk density at six depth intervals (0–5, 5–15, 15–30, 30–60, 60–100, 100–200 cm) on 90 m pixels. `troi_ingest.f.load_soil_layers` reads them for a site and passes each layer through `prepare_soil_layer` (`terrasim2/f/`), which follows the textbook's continuous route:

1. the geometric mean particle diameter from the fractions (`compute_geometric_mean_diameter`, eq. 2.36);
2. saturated content θs = 1 − bulk density / 2650;
3. Campbell's air-entry potential ψe and exponent b from the diameter and θs by the book's regressions (`estimate_campbell_params`, eqs. 5.36 and 5.37);
4. the textural class by the USDA triangle rules (`classify_soil_texture`), kept for reference;
5. the plant-available fraction: θ at field capacity minus θ at wilting point, both read off the Campbell curve (`compute_campbell_water_content`, eq. 5.27) at the suctions in `SoilConventions`.

The result is a `SoilLayers` object: the second `CellToTileMap` onto the SLGA pixels, the layer bounds, and per layer and pixel the fraction, the texture index and (θs, ψe, b).

## Capacity and hydraulics over the root depth

`SoilLayers.compute_capacity(root_depth)` returns mm per cell: the available fraction times the thickness of each layer that lies above the root depth (`compute_layer_thickness_in_depth`), summed (`compute_capacity_map`). The root depth may be one number or a `(rows, cols)` field.

`SoilLayers.compute_hydraulics(root_depth)` returns a `SoilHydraulics` with arrays per cell:

| Attribute | Unit | How |
|---|---|---|
| `capacity` | mm | as above |
| `theta_s`, `b` | m³/m³, – | depth-weighted over the layers in the roots |
| `k_sat` | kg s m⁻³ | from θs, ψe and b by eq. 6.34 (`estimate_saturated_conductivity`) |
| `theta_fc`, `theta_wp` | m³/m³ | the curve at the convention suctions |
| `free_capacity` | mm | (θs − θfc) × root depth: the room between field capacity and saturation |

`require_conductivity()` raises when no curve is known (inputs without soil layers), which only the closed bucket tolerates. Conductivity at a content follows eq. 6.35, K = Ks (θ/θs)^(2b+3) (`compute_campbell_conductivity`).

## The conventions: −10 and −500 J/kg

`SoilConventions` (`terrasim2/k/soil_conventions.py`) holds the suctions field capacity and wilting point are read at. The defaults are −10 and −500 J/kg, not the textbook's −33 and −1500.

This was a calibration, not a choice. At 205 surveyed APSoil profiles (1,183 depth intervals, CSIRO APSoil v3.37), the SLGA-derived field capacity read at −33 J/kg sat 0.09 m³/m³ below the measured drained upper limit at every depth and in every texture class, with the ranking right (r 0.81). Reading the curve at −10 J/kg reproduces the measured limit (bias −0.02, r 0.81), and −500 J/kg corrects the estimated curve's too-steep dry end against the measured lower limit. In the top 0.3 m the corrected route gives 55 mm of plant-available water against 54 mm measured; the textbook conventions gave 42 mm. The moisture probes at Tarrawarra and MRI had independently indicated suctions of −5 and −7 J/kg. The write-up is a comment on PR #25; the data and scripts are under `~/Documents/Troi-Outputs/calibration/apsoil/`.

The textbook's values remain available: `SoilConventions(field_capacity_suction=-33.0, wilting_point_suction=-1500.0)`. The viewer's soils page (retention curves, texture triangle) keeps the book's values because it reproduces the book's tables; the soil column page uses the model's.

## The reference tables

For the viewer's soils page and for tests, the book's tables are available directly: `lookup_campbell_params` and `lookup_van_genuchten_params` (tables 5.3 and 5.4), `lookup_typical_fractions` (table 2.4), `lookup_saturated_conductivity` (table 6.1, silt filled by eq. 6.34), and `compute_available_water` per metre of each texture. `SoilTexture` is the `StrEnum` of the twelve USDA classes, coarsest first, spelled as the book's tables spell them.

<!-- nav -->
← [Model inputs](model-inputs.md) · [Index](README.md) · [Terrain](terrain.md) →
<!-- /nav -->
