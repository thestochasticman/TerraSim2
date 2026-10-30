import json
from pathlib import Path

import numpy as np


def read_terrain(inputs_folder: Path) -> dict:
    """The terrain of a prepared inputs folder in the visualiser's JSON shape.

    Parameters
    ----------
    inputs_folder : Path
        A ``model_inputs`` folder.

    Returns
    -------
    dict
        ``rows``, ``cols``, ``cell_size`` (m), ``elevation`` (nested lists,
        m) and ``capacity`` (nested lists, mm). The first four are the
        format the visualiser's ``parseTerrainGrid`` already accepts.
    """
    inputs_folder = Path(inputs_folder)
    manifest = json.loads((inputs_folder / "manifest.json").read_text())
    elevation = np.load(inputs_folder / manifest["variables"]["elevation"]["file"])
    capacity = np.load(inputs_folder / manifest["variables"]["capacity"]["file"])
    return {
        "rows": manifest["rows"],
        "cols": manifest["cols"],
        "cell_size": manifest["cell_size"],
        "elevation": elevation.tolist(),
        "capacity": capacity.tolist(),
    }


def t():
    """Shape and cell size match the manifest and the arrays are plain nested lists that serialise."""
    from app.api.f.find_inputs import find_inputs

    terrain = read_terrain(find_inputs("tarrawarra"))
    assert terrain["cell_size"] == 10.0
    assert len(terrain["elevation"]) == terrain["rows"] and len(terrain["elevation"][0]) == terrain["cols"]
    assert len(terrain["capacity"]) == terrain["rows"]
    assert isinstance(terrain["elevation"][0][0], float)
    json.dumps(terrain)
