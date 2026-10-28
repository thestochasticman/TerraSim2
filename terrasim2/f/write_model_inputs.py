import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from terrasim2.k.model_inputs import ModelInputs


def write_model_inputs(inputs: ModelInputs, folder: Path) -> Path:
    """Write a ModelInputs to a folder in the versioned on-disk layout.

    The layout needs only NumPy and the standard library to read back:

        manifest.json   version, rows, cols, cell_size, n_tiles, dates,
                        variables with units, written_at, meta
        elevation.npy   float64 (rows, cols), m
        capacity.npy    float64 (rows, cols), mm
        tile_index.npy  int32 (rows, cols)
        rain.csv        date, tile_0, tile_1, ...   mm
        pet.csv         date, tile_0, tile_1, ...   mm

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
    folder.mkdir(parents=True, exist_ok=True)

    np.save(folder / "elevation.npy", inputs.grid.elevation.astype(np.float64))
    np.save(folder / "capacity.npy", inputs.grid.capacity.astype(np.float64))
    np.save(folder / "tile_index.npy", inputs.cell_map.tile_index.astype(np.int32))
    _write_series(inputs.rain, folder / "rain.csv")
    _write_series(inputs.pet, folder / "pet.csv")

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


def _inputs():
    from terrasim2.k.cell_to_tile_map import CellToTileMap
    from terrasim2.k.terrain_grid import TerrainGrid
    from terrasim2.k.tile_series import TileSeries

    grid = TerrainGrid(elevation=[[1.5, 2.5, 3.5], [4.5, 5.5, 6.5]], cell_size=10.0, capacity=np.full((2, 3), 80.0))
    cell_map = CellToTileMap(grid, tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    dates = ["2024-01-01", "2024-01-02"]
    rain = TileSeries("rain", "mm", dates, [[5.0, 20.25], [0.0, 1.5]])
    pet = TileSeries("pet", "mm", dates, [[3.0, 3.0], [4.0, 4.1]])
    return ModelInputs(grid, cell_map, rain, pet, meta={"stub": "unit", "bbox": [1, 2, 3, 4]})


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


def t():
    t1()
