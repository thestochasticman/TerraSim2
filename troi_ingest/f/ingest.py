from unittest import SkipTest

from pysentinel2 import grid as s2
from troi import Troi

from terrasim2.k.model_inputs import ModelInputs
from terrasim2.k.terrain_grid import TerrainGrid
from troi_ingest.f.compute_silo_tiles import compute_silo_tiles
from troi_ingest.f.compute_window import compute_window
from troi_ingest.f.load_elevation import load_elevation
from troi_ingest.f.load_pet import load_pet
from troi_ingest.f.load_rain import load_rain
from troi_ingest.f.load_soil_layers import load_soil_layers

# The root depth the stored capacity is computed for: the top 30 cm, the layer most soil moisture probes see.
ROOT_DEPTH = 0.3


def ingest(troi: Troi) -> ModelInputs:
    """Build TerraSim2 model inputs for a Troi on the Sentinel-2 grid, in memory.

    Elevation from the Copernicus DEM store, rain and reference
    evapotranspiration from the SILO store, soil layers from the SLGA
    store, all located by the Troi's config. Capacity is the soil's
    available water down to ``ROOT_DEPTH``; moisture is zero.

    Parameters
    ----------
    troi : Troi
        Region (``bbox``, degrees), dates (``start``/``end``) and store
        location plus credentials (``config``).

    Returns
    -------
    ModelInputs
        With ``meta`` recording stub, bbox, dates, the Sentinel-2 window,
        the SILO points, the root depth (m) and the sources.
    """
    elevation = load_elevation(troi)
    grid = TerrainGrid(elevation=elevation, cell_size=s2.RES)
    cell_map, rain = load_rain(troi, grid)
    _, pet = load_pet(troi, grid)
    soil = load_soil_layers(troi, grid)
    grid.capacity = soil.compute_capacity(ROOT_DEPTH)
    _, points = compute_silo_tiles(troi.bbox)
    meta = {
        "stub": troi.stub,
        "bbox": list(troi.bbox),
        "start": str(troi.start),
        "end": str(troi.end),
        "crs": s2.CRS,
        "window": list(compute_window(troi.bbox)),
        "tiles": [{"tile": k, "lat": lat, "lon": lon} for k, (lat, lon) in enumerate(points)],
        "root_depth": ROOT_DEPTH,
        "sources": {
            "elevation": "Copernicus GLO-30 DEM via pycopdem, bilinear onto the Sentinel-2 grid",
            "rain": "SILO daily_rain via pysilo, nearest 0.05 degree point",
            "pet": "SILO et_short_crop (FAO56 short crop) via pysilo, nearest 0.05 degree point",
            "soil": "SLGA v2 clay, sand, silt and bulk density at six depths via pyslga, nearest 90 m pixel; "
            "Campbell curve from the geometric mean diameter (Bittelli et al. 2015 eqs. 2.36, 5.36, 5.37), "
            f"theta_s = 1 - bulk density / 2650; available water between {soil.conventions.field_capacity_suction:g} and {soil.conventions.wilting_point_suction:g} J/kg "
            "(SoilConventions, calibrated against APSoil's measured limits)",
            "capacity": "soil available water summed over layers down to root_depth",
        },
    }
    return ModelInputs(grid, cell_map, rain, pet, meta=meta, soil=soil, root_depth=ROOT_DEPTH, latitude=round((troi.bbox[1] + troi.bbox[3]) / 2, 6))


def t1():
    """The inputs agree with the Troi, carry provenance, and the bucket model runs on them."""
    import numpy as np

    from terrasim2.f.run_model import run_model
    from terrasim2.f.step_bucket_model import step_bucket_model
    from terrasim2.k.bucket_model_params import BucketModelParams
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    try:
        inputs = ingest(troi)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"a data store is unavailable: {err}") from err
    row0, row1, col0, col1 = compute_window(troi.bbox)
    assert inputs.shape == (row1 - row0, col1 - col0)
    assert 100 < inputs.grid.elevation.min() < inputs.grid.elevation.max() < 1500
    assert inputs.dates[0] == np.datetime64(troi.start) and inputs.dates[-1] == np.datetime64(troi.end)
    assert inputs.meta["stub"] == troi.stub and len(inputs.meta["tiles"]) == inputs.n_tiles
    assert inputs.soil is not None and inputs.meta["root_depth"] == ROOT_DEPTH == inputs.root_depth
    assert troi.bbox[1] <= inputs.latitude <= troi.bbox[3], "the latitude is the bbox's middle"
    assert np.allclose(inputs.grid.capacity, inputs.soil.compute_capacity(ROOT_DEPTH), equal_nan=True)
    assert np.isfinite(inputs.grid.capacity).mean() > 0.9 and 5 < np.nanmean(inputs.grid.capacity) < 80

    result = run_model(step_bucket_model, inputs, BucketModelParams())
    assert result.n_days == inputs.n_days and result.shape == inputs.shape
    known = np.isfinite(inputs.grid.capacity)
    assert np.all(result.moisture_history[:, known] >= 0) and np.all(result.moisture_history[:, known] <= inputs.grid.capacity[known] + 1e-9)


def t():
    t1()
