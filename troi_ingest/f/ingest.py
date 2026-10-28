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


def ingest(troi: Troi) -> ModelInputs:
    """Build TerraSim2 model inputs for a Troi on the Sentinel-2 grid, in memory.

    Elevation from the Copernicus DEM store, rain and reference
    evapotranspiration from the SILO store, all located by the Troi's
    config. Capacity is the grid default; moisture is zero.

    Parameters
    ----------
    troi : Troi
        Region (``bbox``, degrees), dates (``start``/``end``) and store
        location plus credentials (``config``).

    Returns
    -------
    ModelInputs
        With ``meta`` recording stub, bbox, dates, the Sentinel-2 window,
        the SILO points and the sources.
    """
    elevation = load_elevation(troi)
    grid = TerrainGrid(elevation=elevation, cell_size=s2.RES)
    cell_map, rain = load_rain(troi, grid)
    _, pet = load_pet(troi, grid)
    _, points = compute_silo_tiles(troi.bbox)
    meta = {
        "stub": troi.stub,
        "bbox": list(troi.bbox),
        "start": str(troi.start),
        "end": str(troi.end),
        "crs": s2.CRS,
        "window": list(compute_window(troi.bbox)),
        "tiles": [{"tile": k, "lat": lat, "lon": lon} for k, (lat, lon) in enumerate(points)],
        "sources": {
            "elevation": "Copernicus GLO-30 DEM via pycopdem, bilinear onto the Sentinel-2 grid",
            "rain": "SILO daily_rain via pysilo, nearest 0.05 degree point",
            "pet": "SILO et_short_crop (FAO56 short crop) via pysilo, nearest 0.05 degree point",
        },
    }
    return ModelInputs(grid, cell_map, rain, pet, meta=meta)


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

    result = run_model(step_bucket_model, inputs, BucketModelParams())
    assert result.n_days == inputs.n_days and result.shape == inputs.shape
    assert np.all(result.moisture_history >= 0) and np.all(result.moisture_history <= inputs.grid.capacity + 1e-9)


def t():
    t1()
