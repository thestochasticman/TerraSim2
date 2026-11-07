import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from terrasim2.k.vegetation_map import VegetationMap


def write_vegetation_map(vegetation: VegetationMap, folder: Path) -> Path:
    """Write a VegetationMap to a folder in the versioned on-disk layout.

    The layout needs only NumPy and the standard library to read back:

        manifest.json    version, rows, cols, classes, features (names),
                         fraction per class, written_at, meta
        vegetation.npz   compressed arrays: class_index (int8) and one
                         float32 array per feature, each (rows, cols)

    Existing files in the folder are overwritten.

    Parameters
    ----------
    vegetation : VegetationMap
    folder : Path
        Created if missing.

    Returns
    -------
    Path
        ``folder``.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(folder / "vegetation.npz", class_index=vegetation.class_index, **vegetation.features)
    manifest = {
        "version": VegetationMap.FORMAT_VERSION,
        "rows": vegetation.shape[0],
        "cols": vegetation.shape[1],
        "classes": list(vegetation.classes),
        "features": list(vegetation.features),
        "fraction": {name: vegetation.compute_fraction(name) for name in vegetation.classes},
        "n_unknown": int((vegetation.class_index < 0).sum()),
        "file": "vegetation.npz",
        "units": {"class_index": "index into classes, -1 unknown", "features": "NDVI, dimensionless"},
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "meta": vegetation.meta,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return folder


def t():
    """Writes the manifest and the array file with the declared dtypes, the class shares and the unknown count."""
    import tempfile

    from terrasim2.k.vegetation_map import _example

    folder = write_vegetation_map(_example(), Path(tempfile.mkdtemp()) / "vegetation")
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["version"] == VegetationMap.FORMAT_VERSION and (manifest["rows"], manifest["cols"]) == (2, 3)
    assert manifest["classes"] == ["grass", "tree"] and manifest["features"] == ["low", "median", "high"]
    assert abs(manifest["fraction"]["tree"] - 0.6) < 1e-12 and manifest["n_unknown"] == 1 and manifest["meta"] == {"stub": "unit"}
    with np.load(folder / manifest["file"]) as arrays:
        assert arrays["class_index"].dtype == np.int8 and arrays["class_index"].tolist() == [[0, 1, -1], [1, 1, 0]]
        assert arrays["low"].dtype == np.float32 and np.isnan(arrays["low"][0, 2]) and abs(arrays["high"][1, 2] - 0.6) < 1e-6
