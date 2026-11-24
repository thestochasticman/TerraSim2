# Soil

<!-- nav -->
← [Model inputs](model-inputs.md) · [Index](README.md) · [Terrain](terrain.md) →
<!-- /nav -->

The model's soil properties come from SLGA texture and bulk density, converted to a Campbell retention curve by the regressions in *Soil Physics with Python*. No soil property is measured at a site.

## From SLGA to a curve per layer

SLGA v2 gives clay, sand and silt percentages and bulk density at six depth intervals (0–5, 5–15, 15–30, 30–60, 60–100 and 100–200 cm) on 90 m pixels. `troi_ingest.f.load_soil_layers` reads them and passes each layer through `prepare_soil_layer` (`terrasim2/f/`):

1. Geometric mean particle diameter from the three fractions (`compute_geometric_mean_diameter`, eq. 2.36).
2. Saturated content θs = 1 − bulk density / 2650 kg m⁻³.
3. Air-entry potential ψe and exponent b from the diameter (`estimate_campbell_params`, eqs. 5.36 and 5.37).
4. USDA texture class (`classify_soil_texture`). It is stored for display and is not used in the calculation.
5. Plant-available fraction θ(ψfc) − θ(ψwp), read off the curve θ = θs (ψe/ψ)^(1/b) (eq. 5.27) at the suctions in `SoilConventions`.

The result is a `SoilLayers` object. A cell takes the values of the SLGA pixel nearest its centre, so all cells on one pixel share their soil.

## Capacity and hydraulics over the root depth

`SoilLayers.compute_capacity(root_depth)` gives capacity in mm per cell. It takes each layer's plant-available fraction times the thickness of that layer above the root depth, and sums over the layers (`compute_layer_thickness_in_depth`, `compute_capacity_map`). The root depth may be one value or a `(rows, cols)` field.

`SoilLayers.compute_hydraulics(root_depth)` returns a `SoilHydraulics` with these arrays per cell:

| Attribute | Unit | Computed as |
|---|---|---|
| `capacity` | mm | the layered sum above |
| `theta_s`, `b` | m³/m³, dimensionless | the layers' θs, ψe and b averaged, weighted by each layer's thickness within the root depth |
| `k_sat` | kg s m⁻³ | eq. 6.34 from the averaged θs, ψe and b (`estimate_saturated_conductivity`) |
| `theta_fc`, `theta_wp` | m³/m³ | the averaged curve at the convention suctions |
| `free_capacity` | mm | (θs − θfc) × root depth |

Two consequences of this construction:

- `capacity` is a sum over layer curves, but `theta_fc`, `theta_wp` and `free_capacity` come from one averaged curve. In general, `capacity` is not equal to (θfc − θwp) × root depth for the same cell.
- A cell is NaN in `theta_s`, `b`, `k_sat`, `theta_fc` and `theta_wp` if any layer within its roots has no SLGA value.

Unsaturated conductivity is K = Ks (θ/θs)^(2b+3) (eq. 6.35, `compute_campbell_conductivity`). `require_conductivity()` raises an error when the inputs carry no curve. The subsurface step and `compute_water_content` call it.

## Conventions: −10 and −500 J/kg

`SoilConventions` (`terrasim2/k/soil_conventions.py`) sets the suctions at which field capacity and wilting point are read. The defaults are −10 and −500 J/kg (equal to kPa for water). The textbook uses −33 and −1500 J/kg.

The defaults were set by comparison with CSIRO APSoil v3.37 at 205 profiles (1,183 depth intervals with measured drained upper limit and lower limit). The comparison is not fitted to the validation sites. With the soil route above:

| Read at | Field capacity minus measured drained upper limit | r |
|---|---|---|
| −33 J/kg | bias −0.090 m³/m³, RMSE 0.108 | 0.81 |
| −10 J/kg | bias −0.020 m³/m³, RMSE 0.064 | 0.81 |

| Read at | Wilting point minus measured lower limit | r |
|---|---|---|
| −1500 J/kg | bias −0.061 m³/m³, RMSE 0.080 | 0.74 |
| −500 J/kg | bias −0.031 m³/m³, RMSE 0.061 | 0.74 |

For the 203 profiles measured through the top 0.3 m, the mean plant-available water is 54.1 mm measured, 54.6 mm at −10/−500 and 41.7 mm at −33/−1500.

The −10 J/kg value matches the drained-upper-limit convention used in Australian practice. The −500 J/kg value compensates for the estimated curve's dry end and has no physical meaning as a wilting suction. The correlation is the same under both conventions, because the choice shifts the level and leaves the ranking unchanged. The data and scripts are in `~/Documents/Troi-Outputs/calibration/apsoil/`, outside the repository, and the write-up is a comment on pull request #25.

The manifest's `soil.conventions` records which suctions the stored fraction was read at, and `SoilLayers` reads its hydraulics at the same suctions. `SoilConventions(field_capacity_suction=-33.0, wilting_point_suction=-1500.0)` restores the textbook values.

## Reference tables

`lookup_campbell_params` and `lookup_van_genuchten_params` (book tables 5.3 and 5.4), `lookup_typical_fractions` (table 2.4) and `lookup_saturated_conductivity` (table 6.1, with silt filled in by eq. 6.34) give class-average values. The run path does not use them. The viewer's retention and texture pages use them, with the textbook's −33/−1500 J/kg. The viewer's soil-column page uses the model's conventions. `SoilTexture` is a `StrEnum` of the twelve USDA classes, coarsest first.
