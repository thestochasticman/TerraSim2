from pathlib import Path

import numpy as np

from app.api.f.find_inputs import DEV_SITES
from app.api.f.find_vegetation import find_vegetation
from app.api.k.run_request import RunRequest
from terrasim2.f.load_vegetation_map import load_vegetation_map


def compute_root_depth_field(request: RunRequest, inputs_roots: tuple[Path, ...] = (DEV_SITES,)) -> float | np.ndarray:
    """The root depth a request means: one value, or a depth per cell by what grows there.

    With ``tree_root_depth`` set and a vegetation map prepared for the
    site, tree cells take that depth and grass and unknown cells take
    ``root_depth``. Otherwise ``root_depth`` applies everywhere, and a
    request's tree depth without a map is simply not used.

    Parameters
    ----------
    request : RunRequest
    inputs_roots : tuple of Path
        Where ``find_vegetation`` looks.

    Returns
    -------
    float or ndarray, m
        A scalar, or a field of the site's shape.
    """
    if request.tree_root_depth is None:
        return request.root_depth
    folder = find_vegetation(request.stub, inputs_roots)
    if folder is None:
        return request.root_depth
    vegetation = load_vegetation_map(folder)
    return vegetation.compute_root_depth({"grass": request.root_depth, "tree": request.tree_root_depth}, unknown_depth=request.root_depth)


def t():
    """Without a tree depth, or without a map, the one depth stands; with both, trees take theirs and the rest the grass depth."""
    assert compute_root_depth_field(RunRequest(stub="tarrawarra")) == 0.3
    assert compute_root_depth_field(RunRequest(stub="example", tree_root_depth=1.5)) == 0.3, "the example region has no map"
    field = compute_root_depth_field(RunRequest(stub="tarrawarra", root_depth=0.4, tree_root_depth=1.5))
    vegetation = load_vegetation_map(find_vegetation("tarrawarra"))
    assert isinstance(field, np.ndarray) and field.shape == vegetation.shape
    assert set(np.unique(field)) <= {0.4, 1.5}
    assert np.all(field[vegetation.class_index == 1] == 1.5) and np.all(field[vegetation.class_index != 1] == 0.4)
