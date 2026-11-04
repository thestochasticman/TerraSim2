from unittest import SkipTest

import numpy as np
from pyslga.store import Store
from troi import Troi

from terrasim2.f.prepare_soil_layer import prepare_soil_layer
from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.soil_layers import SoilLayers
from terrasim2.k.terrain_grid import TerrainGrid
from troi_ingest.f.compute_slga_tiles import compute_slga_tiles

# SLGA's six standard depth intervals: their bounds in metres and pyslga's names for them.
LAYER_BOUNDS = np.array([0.0, 0.05, 0.15, 0.30, 0.60, 1.0, 2.0])
DEPTHS = ("0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm")
ATTRIBUTES = ("Clay", "Sand", "Silt", "Bulk_Density")


def load_soil_layers(troi: Troi, grid: TerrainGrid) -> SoilLayers:
    """The layered soil of a Troi's window, from the Soil and Landscape Grid of Australia.

    Clay, sand, silt and bulk density at six depths are read from the lab's
    SLGA store (downloading missing chunks on first use), one value per
    90 m pixel. Each terrain cell snaps to its nearest pixel. Per pixel and
    layer, ``prepare_soil_layer`` turns the properties into the available
    water fraction and the textural class.

    Parameters
    ----------
    troi : Troi
        Uses ``bbox`` (degrees) and ``config`` (store location and TERN key).
        Dates are ignored; soil does not change.
    grid : TerrainGrid
        The terrain the soil map is laid out on. Must have the window's shape.

    Returns
    -------
    SoilLayers
        On ``grid``, one tile per distinct SLGA pixel, ``LAYER_BOUNDS`` as
        the layers.
    """
    ds = Store(config=troi.config).get_ds(troi.bbox, attributes=ATTRIBUTES, depths=DEPTHS)
    tile_index, pixels = compute_slga_tiles(troi.bbox, ds["lat"].values, ds["lon"].values)
    if tile_index.shape != grid.shape:
        raise ValueError(f"grid shape {grid.shape} does not match the Troi's window {tile_index.shape}")
    lat_i, lon_i = pixels[:, 0], pixels[:, 1]

    fraction = np.empty((len(DEPTHS), len(pixels)))
    texture = np.empty((len(DEPTHS), len(pixels)), dtype=np.int8)
    for k, depth in enumerate(DEPTHS):
        pick = lambda attribute: ds[f"{attribute}_{depth}"].values[lat_i, lon_i].astype(np.float64)  # noqa: E731
        sand, silt, clay = pick("Sand") / 100, pick("Silt") / 100, pick("Clay") / 100
        bulk_density = pick("Bulk_Density") * 1000
        fraction[k], texture[k] = prepare_soil_layer(sand, silt, clay, bulk_density)
    return SoilLayers(CellToTileMap(grid, tile_index, n_tiles=len(pixels)), LAYER_BOUNDS, fraction, texture)


def _load_or_skip(troi: Troi, grid: TerrainGrid) -> SoilLayers:
    try:
        return load_soil_layers(troi, grid)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"SLGA store unavailable: {err}") from err
    except ValueError as err:
        if "tern_api_key" in str(err):
            raise SkipTest(f"TERN key not configured: {err}") from err
        raise


def _grid_for(troi: Troi) -> TerrainGrid:
    from troi_ingest.f.compute_window import compute_window

    row0, row1, col0, col1 = compute_window(troi.bbox)
    return TerrainGrid(elevation=np.zeros((row1 - row0, col1 - col0)), cell_size=10.0)


def t1():
    """The example region: six layers on a few hundred pixels, fractions in the range soils give, every
    class valid, and a capacity map that is finite and positive at 0.3 m."""
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    soil = _load_or_skip(troi, _grid_for(troi))
    assert soil.n_layers == 6 and 100 < soil.n_tiles < 2000, soil.n_tiles
    assert np.array_equal(soil.layer_bounds, LAYER_BOUNDS)
    known = np.isfinite(soil.available_fraction)
    assert known.mean() > 0.9, "the example region is land with full SLGA coverage"
    assert 0.02 < np.nanmin(soil.available_fraction) and np.nanmax(soil.available_fraction) < 0.30
    assert soil.texture_index.min() >= 0 and soil.texture_index.max() < 12
    capacity = soil.compute_capacity(0.3)
    assert capacity.shape == soil.shape and np.isfinite(capacity).mean() > 0.9
    assert 5 < np.nanmean(capacity) < 80, np.nanmean(capacity)


def t2():
    """A grid of the wrong shape is rejected."""
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    try:
        _load_or_skip(troi, TerrainGrid(elevation=np.zeros((2, 2)), cell_size=10.0))
    except ValueError as err:
        assert "does not match" in str(err)
    else:
        raise AssertionError("expected ValueError for grid shape mismatch")


def t():
    t1()
    t2()
