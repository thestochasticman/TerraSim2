import json
from pathlib import Path

from terrasim2.f.load_model_inputs import load_model_inputs
from terrasim2.k.terrain_derivatives import TerrainDerivatives


def read_terrain(inputs_folder: Path, root_depth: float | None = None) -> dict:
    """The terrain of a prepared inputs folder in the visualiser's JSON shape.

    Parameters
    ----------
    inputs_folder : Path
        A ``model_inputs`` folder.
    root_depth : float, optional, m
        When given and the inputs carry soil layers, the capacity is the
        soil's available water down to this depth, as a run with this
        root depth would use; otherwise the stored capacity.

    Returns
    -------
    dict
        ``rows``, ``cols``, ``cell_size`` (m), ``elevation`` (nested lists,
        m), ``capacity`` (nested lists, mm; NaN as null), ``free_capacity``
        (nested lists, mm, the pore space above field capacity at that root
        depth, or null when the inputs carry no soil curve) and
        ``upslope_cells`` (nested lists, dimensionless: how many cells drain
        through each, from the pit-filled elevation).
    """
    inputs = load_model_inputs(inputs_folder)
    capacity = inputs.grid.capacity
    free_capacity = None
    depth = root_depth if root_depth is not None else inputs.root_depth
    if inputs.soil is not None and depth is not None:
        hydraulics = inputs.soil.compute_hydraulics(depth)
        capacity = hydraulics.capacity
        if hydraulics.has_conductivity:
            free_capacity = hydraulics.free_capacity.tolist()
    derivatives = TerrainDerivatives(inputs.grid)
    return {
        "rows": inputs.shape[0],
        "cols": inputs.shape[1],
        "cell_size": inputs.grid.cell_size,
        "elevation": inputs.grid.elevation.tolist(),
        "capacity": capacity.tolist(),
        "free_capacity": free_capacity,
        "upslope_cells": derivatives.upslope_cells.tolist(),
    }


def t():
    """Shape and cell size match the manifest, the arrays are plain nested lists that serialise, and a
    deeper root depth gives a larger capacity."""
    import numpy as np

    from app.api.f.find_inputs import find_inputs

    terrain = read_terrain(find_inputs("tarrawarra"))
    assert terrain["cell_size"] == 10.0
    assert len(terrain["elevation"]) == terrain["rows"] and len(terrain["elevation"][0]) == terrain["cols"]
    assert len(terrain["capacity"]) == terrain["rows"]
    assert isinstance(terrain["elevation"][0][0], float)
    json.dumps(terrain)
    shallow = np.array(read_terrain(find_inputs("tarrawarra"), root_depth=0.3)["capacity"])
    deep = np.array(read_terrain(find_inputs("tarrawarra"), root_depth=1.0)["capacity"])
    assert np.allclose(shallow, np.array(terrain["capacity"])), "the stored capacity is the 0.3 m one"
    assert deep.mean() > 2 * shallow.mean()
    free = np.array(terrain["free_capacity"])
    assert free.shape == shallow.shape and free.min() > 0 and np.array(read_terrain(find_inputs("tarrawarra"), root_depth=1.0)["free_capacity"]).mean() > 2 * free.mean()
    upslope = np.array(terrain["upslope_cells"])
    assert upslope.shape == shallow.shape and upslope.min() == 1 and upslope.max() > 0.1 * upslope.size
    assert isinstance(terrain["upslope_cells"][0][0], int)
