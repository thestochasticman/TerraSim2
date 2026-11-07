import json
from pathlib import Path

import numpy as np

from terrasim2.f.load_model_inputs import load_model_inputs
from terrasim2.f.load_vegetation_map import load_vegetation_map
from terrasim2.k.terrain_derivatives import TerrainDerivatives


def read_terrain(inputs_folder: Path, root_depth: float | np.ndarray | None = None, vegetation_folder: Path | None = None) -> dict:
    """The terrain of a prepared inputs folder in the visualiser's JSON shape.

    Parameters
    ----------
    inputs_folder : Path
        A ``model_inputs`` folder.
    root_depth : float or ndarray, optional, m
        When given and the inputs carry soil layers, the capacity is the
        soil's available water down to this depth, one value or a field
        of the grid's shape, as a run with this root depth would use;
        otherwise the stored capacity.
    vegetation_folder : Path, optional
        A ``vegetation`` folder on the same grid; its classes are served.

    Returns
    -------
    dict
        ``rows``, ``cols``, ``cell_size`` (m), ``elevation`` (nested lists,
        m), ``capacity`` (nested lists, mm; NaN as null), ``free_capacity``
        (nested lists, mm, the pore space above field capacity at that root
        depth, or null when the inputs carry no soil curve),
        ``upslope_cells`` (nested lists, dimensionless: how many cells drain
        through each, from the pit-filled elevation) and ``vegetation``
        (nested lists of the class index per cell, -1 unknown, with
        ``vegetation_classes`` naming the indices; null without a map).
    """
    inputs = load_model_inputs(inputs_folder)
    vegetation = None
    classes = None
    if vegetation_folder is not None:
        v = load_vegetation_map(vegetation_folder)
        if v.shape != inputs.shape:
            raise ValueError(f"vegetation map {v.shape} does not sit on the inputs' grid {inputs.shape}")
        vegetation = v.class_index.tolist()
        classes = list(v.classes)
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
        "vegetation": vegetation,
        "vegetation_classes": classes,
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
    assert terrain["vegetation"] is None and terrain["vegetation_classes"] is None

    from app.api.f.find_vegetation import find_vegetation

    folder = find_vegetation("tarrawarra")
    classes = np.array(read_terrain(find_inputs("tarrawarra"), vegetation_folder=folder)["vegetation"])
    assert classes.shape == shallow.shape and set(np.unique(classes)) <= {-1, 0, 1}
    field = np.where(classes == 1, 1.0, 0.3)
    treed = np.array(read_terrain(find_inputs("tarrawarra"), root_depth=field, vegetation_folder=folder)["capacity"])
    assert np.allclose(treed[classes != 1], shallow[classes != 1], equal_nan=True) and np.allclose(treed[classes == 1], deep[classes == 1], equal_nan=True)
    json.dumps(read_terrain(find_inputs("tarrawarra"), vegetation_folder=folder))
