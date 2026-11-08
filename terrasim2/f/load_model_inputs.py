import csv
import json
from pathlib import Path

import numpy as np

from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.model_inputs import ModelInputs
from terrasim2.k.soil_conventions import SoilConventions
from terrasim2.k.soil_layers import SoilLayers
from terrasim2.k.terrain_grid import TerrainGrid
from terrasim2.k.tile_series import TileSeries


def load_model_inputs(folder: Path, root_depth: float | np.ndarray | None = None) -> ModelInputs:
    """Read a folder written by ``write_model_inputs`` back into a ModelInputs.

    Needs only NumPy and the standard library. Refuses a manifest whose
    version is not ``ModelInputs.FORMAT_VERSION``. Initial moisture is zero;
    set ``inputs.grid.moisture`` before running if you want otherwise.

    Parameters
    ----------
    folder : Path
        Contains manifest.json and the files it names.
    root_depth : float or ndarray, optional, m
        When given and the inputs carry soil layers, the grid's capacity is
        recomputed for this root depth instead of taken from capacity.npy,
        which holds the producer's choice; the result records it. One
        value, or a field of the grid's shape where roots vary by cell.
        Without it, the manifest's root depth is recorded. Refused for
        inputs without soil.

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
    soil = _read_soil(folder, manifest.get("soil"), grid)
    if root_depth is not None:
        if soil is None:
            raise ValueError(f"model inputs at {folder} carry no soil layers, so a root depth cannot be applied")
        grid.capacity = soil.compute_capacity(root_depth)
    else:
        root_depth = manifest.get("root_depth")
    return ModelInputs(grid, cell_map, rain, pet, meta=manifest.get("meta", {}), soil=soil, root_depth=root_depth, latitude=manifest.get("latitude"))


def _read_soil(folder: Path, entry: dict | None, grid: TerrainGrid) -> SoilLayers | None:
    if entry is None:
        return None
    names = entry["files"]
    soil_map = CellToTileMap(grid, np.load(folder / names["tile_index"]), n_tiles=entry["n_tiles"])
    campbell = np.load(folder / names["campbell"]) if "campbell" in names else None
    conventions = SoilConventions(**entry["conventions"])
    return SoilLayers(soil_map, entry["layer_bounds"], np.load(folder / names["fraction"]), np.load(folder / names["texture"]), campbell, conventions)


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
    assert back.soil is None and back.root_depth is None and back.latitude is None
    try:
        load_model_inputs(folder, root_depth=0.5)
    except ValueError as err:
        assert "no soil layers" in str(err)
    else:
        raise AssertionError("expected ValueError for a root depth without soil")


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


def t5():
    """Soil layers round-trip, and a root depth at load recomputes the capacity from them."""
    import tempfile

    from terrasim2.f.write_model_inputs import _inputs, write_model_inputs

    original = _inputs(with_soil=True)
    folder = write_model_inputs(original, Path(tempfile.mkdtemp()) / "model_inputs")
    back = load_model_inputs(folder)
    assert back.soil is not None and back.soil.n_layers == 3 and back.soil.n_tiles == 2
    assert np.array_equal(back.soil.cell_map.tile_index, original.soil.cell_map.tile_index)
    assert np.array_equal(back.soil.layer_bounds, original.soil.layer_bounds)
    assert np.allclose(back.soil.available_fraction, original.soil.available_fraction, equal_nan=True)
    assert np.array_equal(back.soil.texture_index, original.soil.texture_index)
    assert np.allclose(back.soil.campbell, original.soil.campbell, equal_nan=True)
    assert back.soil.conventions == original.soil.conventions == SoilConventions()
    assert np.all(back.grid.capacity == 80.0), "without a root depth the stored capacity stands"
    assert back.root_depth == 0.3 and back.latitude == -37.5, "the manifest's root depth and latitude are recorded"
    shallow = load_model_inputs(folder, root_depth=0.3)
    assert np.allclose(shallow.grid.capacity, [[0.035 * 300] * 3, [0.116 * 300] * 3])
    assert load_model_inputs(folder, root_depth=1.0).root_depth == 1.0
    assert np.isnan(load_model_inputs(folder, root_depth=1.0).grid.capacity[0, 0])
    field = np.array([[0.3, 0.3, 0.1], [0.3, 1.0, 0.3]])
    varied = load_model_inputs(folder, root_depth=field)
    assert np.array_equal(varied.root_depth, field)
    assert np.allclose(varied.grid.capacity, [[0.035 * 300, 0.035 * 300, 0.035 * 100], [0.116 * 300, 0.116 * 1000, 0.116 * 300]]), "capacity follows the depth of each cell"


DEV_SITES = Path(__file__).resolve().parents[2] / "data" / "dev_sites"


def t3():
    """The committed example inputs load and the bucket model runs on them."""
    from terrasim2.f.run_model import run_model
    from terrasim2.f.step_bucket_model import step_bucket_model
    from terrasim2.k.bucket_model_params import BucketModelParams

    inputs = load_model_inputs(DEV_SITES / "example" / "model_inputs")
    assert inputs.n_days >= 28 and inputs.n_tiles >= 1
    assert 100 < inputs.grid.elevation.min() < inputs.grid.elevation.max() < 1500
    result = run_model(step_bucket_model, inputs, BucketModelParams())
    assert result.n_days == inputs.n_days and result.shape == inputs.shape


def t4():
    """Every committed site folder loads with soil layers, names itself correctly, covers its dates without
    gaps, and its stored capacity is the soil's capacity at the recorded root depth."""
    folders = sorted(p for p in DEV_SITES.glob("*/model_inputs") if p.parent.name != "example")
    assert len(folders) == 6, [p.parent.name for p in folders]
    for folder in folders:
        inputs = load_model_inputs(folder)
        assert inputs.meta["stub"] == folder.parent.name, folder
        assert inputs.meta["start"] == str(inputs.dates[0]) and inputs.meta["end"] == str(inputs.dates[-1])
        assert np.all(np.diff(inputs.dates) == np.timedelta64(1, "D")), f"{folder}: dates must be consecutive days"
        assert np.isfinite(inputs.grid.elevation).all(), f"{folder}: DEM has gaps"
        assert inputs.rain.values.shape == (inputs.n_days, inputs.n_tiles)
        assert inputs.soil is not None and inputs.soil.n_layers == 6, f"{folder}: expected six SLGA layers"
        assert inputs.soil.campbell is not None and inputs.root_depth == inputs.meta["root_depth"]
        assert inputs.latitude is not None and -40 < inputs.latitude < -28, f"{folder}: the sites lie in south-eastern Australia"
        assert inputs.soil.conventions == SoilConventions(), f"{folder}: the committed inputs are prepared at the calibrated conventions"
        hydraulics = inputs.soil.compute_hydraulics(inputs.root_depth)
        assert hydraulics.has_conductivity and np.isfinite(hydraulics.k_sat).all(), f"{folder}: conductivity should be known everywhere"
        recomputed = inputs.soil.compute_capacity(inputs.meta["root_depth"])
        assert np.allclose(recomputed, inputs.grid.capacity, equal_nan=True), f"{folder}: capacity.npy disagrees with the soil layers"
        assert np.nanmin(inputs.grid.capacity) > 0, f"{folder}: capacity must be positive where known"


def t():
    t1()
    t2()
    t5()
    t3()
    t4()
