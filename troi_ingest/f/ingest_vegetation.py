from dataclasses import asdict

import numpy as np
from troi import Config, config as troi_config

from terrasim2.f.classify_vegetation import classify_vegetation
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.vegetation_map import VegetationMap
from terrasim2.k.vegetation_thresholds import VegetationThresholds
from troi_ingest.f.choose_reference_period import choose_reference_period
from troi_ingest.f.compute_window import compute_window
from troi_ingest.f.load_ndvi_features import load_ndvi_features
from troi_ingest.f.make_site_troi import make_site_troi


def ingest_vegetation(stub: str, thresholds: VegetationThresholds = VegetationThresholds(), config: Config = troi_config) -> VegetationMap:
    """A site's vegetation map from a year of Sentinel-2 NDVI, on the site's grid.

    The year is ``choose_reference_period`` of the site's dates; the
    statistics are ``load_ndvi_features``; the classes are
    ``classify_vegetation`` with the thresholds given. Provenance goes in
    the map's ``meta``.

    Parameters
    ----------
    stub : str
        A ``stub`` from ``data/dense_sites.csv``.
    thresholds : VegetationThresholds
    config : Config
        Where the Sentinel-2 cube lives.

    Returns
    -------
    VegetationMap
    """
    troi = make_site_troi(stub, config=config)
    start, end = choose_reference_period(troi.start, troi.end)
    row0, row1, col0, col1 = compute_window(troi.bbox)
    grid = TerrainGrid(elevation=np.zeros((row1 - row0, col1 - col0)), cell_size=10.0)
    features = load_ndvi_features(troi, grid, start, end)
    class_index = classify_vegetation(features["low"], features["high"], thresholds)
    n_clear = features.pop("n_clear")
    meta = {
        "stub": stub,
        "bbox": list(troi.bbox),
        "imagery": {"start": str(start), "end": str(end), "own_dates": (start, end) != choose_reference_period(start, start)},
        "clear_looks": {"median": float(np.median(n_clear)), "min": int(n_clear.min()), "max": int(n_clear.max())},
        "thresholds": asdict(thresholds),
        "sources": {"ndvi": "Sentinel-2 ARD (DEA) via pysentinel2, cloud-masked on read; per cell the 10th, 50th and 90th percentiles of NDVI over the year"},
        "rule": "tree where the 10th percentile of NDVI is at least tree_low_min and the 90th minus the 10th is at most tree_amplitude_max; else grass; unknown where fewer than 8 clear looks",
    }
    return VegetationMap(class_index, features, meta=meta)


def t():
    """Tarrawarra from the cube: a map on the site's grid, nearly all cells classified, few trees on a grazed catchment,
    provenance recorded."""
    from unittest import SkipTest

    try:
        v = ingest_vegetation("tarrawarra")
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"Sentinel-2 cube unavailable: {err}") from err
    row0, row1, col0, col1 = compute_window(make_site_troi("tarrawarra").bbox)
    assert v.shape == (row1 - row0, col1 - col0)
    assert (v.class_index >= 0).mean() > 0.95
    assert v.compute_fraction("tree") < 0.3, "tarrawarra is pasture with a few trees"
    assert v.meta["stub"] == "tarrawarra" and v.meta["imagery"]["start"] == "2023-01-01" and v.meta["thresholds"]["tree_low_min"] == 0.4
