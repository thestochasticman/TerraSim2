import csv
import json
from pathlib import Path

import numpy as np

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.model_inputs import ModelInputs
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries


def load_model_inputs(folder: Path) -> ModelInputs:
    """Read a folder written by ``write_model_inputs`` back into a ModelInputs.

    Needs only NumPy and the standard library. Refuses a manifest whose
    version is not ``ModelInputs.FORMAT_VERSION``. Initial moisture is zero;
    set ``inputs.grid.moisture`` before running if you want otherwise.

    Parameters
    ----------
    folder : Path
        Contains manifest.json and the files it names.

    Returns
    -------
    ModelInputs
    """
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text())
    version = manifest.get("version")
    if version != ModelInputs.FORMAT_VERSION:
        raise ValueError(f"model inputs at {folder} are format version {version}; this reader needs {ModelInputs.FORMAT_VERSION}")

    files = manifest["variables"]
    elevation = np.load(folder / files["elevation"]["file"])
    capacity = np.load(folder / files["capacity"]["file"])
    tile_index = np.load(folder / "tile_index.npy")
    shape = (manifest["rows"], manifest["cols"])
    if elevation.shape != shape or tile_index.shape != shape:
        raise ValueError(f"arrays do not match the manifest shape {shape}")

    grid = TerrainGrid(elevation=elevation, cell_size=manifest["cell_size"], capacity=capacity)
    cell_map = CellToTileMap(grid, tile_index, n_tiles=manifest["n_tiles"])
    rain = _read_series(folder / files["rain"]["file"], "rain", files["rain"]["units"])
    pet = _read_series(folder / files["pet"]["file"], "pet", files["pet"]["units"])
    return ModelInputs(grid, cell_map, rain, pet, meta=manifest.get("meta", {}))


def _read_series(path: Path, name: str, units: str) -> TileSeries:
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    if header[0] != "date" or any(not h.startswith("tile_") for h in header[1:]):
        raise ValueError(f"{path} does not look like a tile series: header {header}")
    dates = [r[0] for r in body]
    values = np.array([[float(v) for v in r[1:]] for r in body], dtype=np.float64)
    return TileSeries(name, units, dates, values)


def t1():
    """Round trip: what write_model_inputs wrote comes back equal."""
    import tempfile

    from terrasim2.f.write_model_inputs import _inputs, write_model_inputs

    original = _inputs()
    folder = write_model_inputs(original, Path(tempfile.mkdtemp()) / "model_inputs")
    back = load_model_inputs(folder)
    assert back.shape == original.shape and back.n_tiles == original.n_tiles
    assert np.array_equal(back.grid.elevation, original.grid.elevation)
    assert np.array_equal(back.grid.capacity, original.grid.capacity)
    assert np.all(back.grid.moisture == 0.0)
    assert np.array_equal(back.cell_map.tile_index, original.cell_map.tile_index)
    assert np.array_equal(back.rain.dates, original.rain.dates)
    assert np.array_equal(back.rain.values, original.rain.values)
    assert np.array_equal(back.pet.values, original.pet.values)
    assert back.rain.units == "mm" and back.pet.name == "pet"
    assert back.meta == original.meta


def t2():
    """A wrong format version is refused."""
    import tempfile

    from terrasim2.f.write_model_inputs import _inputs, write_model_inputs

    folder = write_model_inputs(_inputs(), Path(tempfile.mkdtemp()) / "model_inputs")
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["version"] = ModelInputs.FORMAT_VERSION + 1
    (folder / "manifest.json").write_text(json.dumps(manifest))
    try:
        load_model_inputs(folder)
    except ValueError as err:
        assert "format version" in str(err)
    else:
        raise AssertionError("expected ValueError for version mismatch")


DEV_DATA = Path(__file__).resolve().parents[2] / "dev_data"


def t3():
    """The committed example inputs load and the bucket model runs on them."""
    from terrasim2.f.run_model import run_model
    from terrasim2.f.step_bucket_model import step_bucket_model
    from terrasim2.k.bucket_model_params import BucketModelParams

    inputs = load_model_inputs(DEV_DATA / "example" / "model_inputs")
    assert inputs.n_days >= 28 and inputs.n_tiles >= 1
    assert 100 < inputs.grid.elevation.min() < inputs.grid.elevation.max() < 1500
    result = run_model(step_bucket_model, inputs, BucketModelParams())
    assert result.n_days == inputs.n_days and result.shape == inputs.shape


def t4():
    """Every committed site folder loads, names itself correctly, and covers its dates without gaps."""
    folders = sorted(p for p in DEV_DATA.glob("*/model_inputs") if p.parent.name != "example")
    assert len(folders) == 6, [p.parent.name for p in folders]
    for folder in folders:
        inputs = load_model_inputs(folder)
        assert inputs.meta["stub"] == folder.parent.name, folder
        assert inputs.meta["start"] == str(inputs.dates[0]) and inputs.meta["end"] == str(inputs.dates[-1])
        assert np.all(np.diff(inputs.dates) == np.timedelta64(1, "D")), f"{folder}: dates must be consecutive days"
        assert np.isfinite(inputs.grid.elevation).all(), f"{folder}: DEM has gaps"
        assert inputs.rain.values.shape == (inputs.n_days, inputs.n_tiles)


def t():
    t1()
    t2()
    t3()
    t4()
