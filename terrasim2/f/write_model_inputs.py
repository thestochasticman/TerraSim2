import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from terrasim2.k.model_inputs import ModelInputs


def write_model_inputs(inputs: ModelInputs, folder: Path) -> Path:
    """Write a ModelInputs to a folder in the versioned on-disk layout.

    The layout needs only NumPy and the standard library to read back:

        manifest.json       version, rows, cols, cell_size, n_tiles, dates,
                            variables with units, soil (when present), written_at, meta
        elevation.npy       float64 (rows, cols), m
        capacity.npy        float64 (rows, cols), mm, for the producer's root depth
        tile_index.npy      int32 (rows, cols)
        rain.csv            date, tile_0, tile_1, ...   mm
        pet.csv             date, tile_0, tile_1, ...   mm
        soil_tile_index.npy int32 (rows, cols), which soil tile each cell reads
        soil_fraction.npy   float64 (n_layers, n_soil_tiles), m3 m-3 available
        soil_texture.npy    int8 (n_layers, n_soil_tiles), index into the manifest's textures
        soil_campbell.npy   float64 (3, n_layers, n_soil_tiles): theta_s, psi_e (J kg-1), b

    The soil files exist only when the inputs carry soil layers, the curve
    file only when they carry a curve; the manifest's ``soil`` entry names
    them with the layer bounds in m, and ``root_depth`` (m) says what
    depth capacity.npy was computed for.
    Initial moisture is not written; a run sets it. Existing files in the
    folder are overwritten.

    Parameters
    ----------
    inputs : ModelInputs
    folder : Path
        Created if missing.

    Returns
    -------
    Path
        ``folder``.
    """
    folder = Path(folder)
    if isinstance(inputs.root_depth, np.ndarray):
        raise ValueError("model inputs on disk carry one root depth; a field of depths is set at run time from a vegetation map, not written")
    folder.mkdir(parents=True, exist_ok=True)

    np.save(folder / "elevation.npy", inputs.grid.elevation.astype(np.float64))
    np.save(folder / "capacity.npy", inputs.grid.capacity.astype(np.float64))
    np.save(folder / "tile_index.npy", inputs.cell_map.tile_index.astype(np.int32))
    _write_series(inputs.rain, folder / "rain.csv")
    _write_series(inputs.pet, folder / "pet.csv")
    soil = None
    if inputs.soil is not None:
        from terrasim2.k.soil_texture import SoilTexture

        np.save(folder / "soil_tile_index.npy", inputs.soil.cell_map.tile_index.astype(np.int32))
        np.save(folder / "soil_fraction.npy", inputs.soil.available_fraction.astype(np.float64))
        np.save(folder / "soil_texture.npy", inputs.soil.texture_index.astype(np.int8))
        files = {"tile_index": "soil_tile_index.npy", "fraction": "soil_fraction.npy", "texture": "soil_texture.npy"}
        if inputs.soil.campbell is not None:
            np.save(folder / "soil_campbell.npy", inputs.soil.campbell.astype(np.float64))
            files["campbell"] = "soil_campbell.npy"
        soil = {
            "layer_bounds": inputs.soil.layer_bounds.tolist(),
            "n_tiles": inputs.soil.n_tiles,
            "textures": [str(tex) for tex in SoilTexture],
            "files": files,
            "units": {"layer_bounds": "m", "fraction": "m3 m-3", "campbell": ["m3 m-3", "J kg-1", "dimensionless"]},
        }

    manifest = {
        "version": ModelInputs.FORMAT_VERSION,
        "rows": inputs.shape[0],
        "cols": inputs.shape[1],
        "cell_size": inputs.grid.cell_size,
        "n_tiles": inputs.n_tiles,
        "start": str(inputs.dates[0]),
        "end": str(inputs.dates[-1]),
        "n_days": inputs.n_days,
        "variables": {
            "elevation": {"file": "elevation.npy", "units": "m"},
            "capacity": {"file": "capacity.npy", "units": "mm"},
            "rain": {"file": "rain.csv", "units": inputs.rain.units},
            "pet": {"file": "pet.csv", "units": inputs.pet.units},
        },
        "soil": soil,
        "root_depth": inputs.root_depth,
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "meta": inputs.meta,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return folder


def _write_series(series, path: Path) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", *(f"tile_{k}" for k in range(series.n_tiles))])
        for date, row in zip(series.dates, series.values):
            writer.writerow([str(date), *(repr(float(v)) for v in row)])


def _inputs(with_soil: bool = False):
    from terrasim2.k.cell_to_tile_map import CellToTileMap
    from terrasim2.k.soil_layers import SoilLayers
    from terrasim2.k.terrain_grid import TerrainGrid
    from terrasim2.k.tile_series import TileSeries

    grid = TerrainGrid(elevation=[[1.5, 2.5, 3.5], [4.5, 5.5, 6.5]], cell_size=10.0, capacity=np.full((2, 3), 80.0))
    cell_map = CellToTileMap(grid, tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    dates = ["2024-01-01", "2024-01-02"]
    rain = TileSeries("rain", "mm", dates, [[5.0, 20.25], [0.0, 1.5]])
    pet = TileSeries("pet", "mm", dates, [[3.0, 3.0], [4.0, 4.1]])
    soil = None
    if with_soil:
        soil_map = CellToTileMap(grid, tile_index=[[0, 0, 0], [1, 1, 1]], n_tiles=2)
        campbell = np.array([[[0.37, 0.43]] * 3, [[-0.73, -1.12]] * 3, [[1.69, 4.55]] * 3])
        campbell[:, 2, 0] = np.nan
        soil = SoilLayers(soil_map, [0.0, 0.1, 0.3, 1.0], [[0.035, 0.116], [0.035, 0.116], [np.nan, 0.116]], [[0, 4], [0, 4], [-1, 4]], campbell)
    return ModelInputs(grid, cell_map, rain, pet, meta={"stub": "unit", "bbox": [1, 2, 3, 4]}, soil=soil, root_depth=0.3 if with_soil else None)


def t1():
    """Writes every file named in the manifest, with the declared shapes and the exact values."""
    import tempfile

    folder = write_model_inputs(_inputs(), Path(tempfile.mkdtemp()) / "model_inputs")
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["version"] == ModelInputs.FORMAT_VERSION
    assert (manifest["rows"], manifest["cols"], manifest["n_tiles"], manifest["n_days"]) == (2, 3, 2, 2)
    assert manifest["start"] == "2024-01-01" and manifest["end"] == "2024-01-02"
    assert manifest["meta"] == {"stub": "unit", "bbox": [1, 2, 3, 4]}
    for var in manifest["variables"].values():
        assert (folder / var["file"]).exists(), var
    assert np.load(folder / "elevation.npy").dtype == np.float64
    assert np.array_equal(np.load(folder / "elevation.npy"), [[1.5, 2.5, 3.5], [4.5, 5.5, 6.5]])
    assert np.load(folder / "tile_index.npy").dtype == np.int32
    rows = list(csv.reader(open(folder / "rain.csv")))
    assert rows[0] == ["date", "tile_0", "tile_1"]
    assert rows[1] == ["2024-01-01", "5.0", "20.25"]
    assert manifest["soil"] is None and manifest["root_depth"] is None and not (folder / "soil_fraction.npy").exists()


def t2():
    """With soil layers, the three soil files are written and the manifest names them with the bounds."""
    import tempfile

    folder = write_model_inputs(_inputs(with_soil=True), Path(tempfile.mkdtemp()) / "model_inputs")
    manifest = json.loads((folder / "manifest.json").read_text())
    soil = manifest["soil"]
    assert soil["layer_bounds"] == [0.0, 0.1, 0.3, 1.0] and soil["n_tiles"] == 2 and soil["textures"][0] == "sand"
    for name in soil["files"].values():
        assert (folder / name).exists(), name
    fraction = np.load(folder / "soil_fraction.npy")
    assert fraction.shape == (3, 2) and fraction.dtype == np.float64 and np.isnan(fraction[2, 0])
    texture = np.load(folder / "soil_texture.npy")
    assert texture.dtype == np.int8 and texture[2, 0] == -1 and texture[1, 1] == 4
    assert np.load(folder / "soil_tile_index.npy").dtype == np.int32
    curve = np.load(folder / "soil_campbell.npy")
    assert curve.shape == (3, 3, 2) and np.isnan(curve[:, 2, 0]).all() and curve[2, 0, 1] == 4.55
    assert soil["files"]["campbell"] == "soil_campbell.npy" and manifest["root_depth"] == 0.3


def t3():
    """Inputs whose root depth is a field are refused: the layout records one depth."""
    import tempfile

    inputs = _inputs(with_soil=True)
    inputs.root_depth = np.full(inputs.shape, 0.3)
    try:
        write_model_inputs(inputs, Path(tempfile.mkdtemp()) / "model_inputs")
    except ValueError as err:
        assert "field" in str(err)
    else:
        raise AssertionError("expected ValueError for a field of root depths")


def t():
    t1()
    t2()
    t3()
