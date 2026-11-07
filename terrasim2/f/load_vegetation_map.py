import json
from pathlib import Path

import numpy as np

from terrasim2.f.classify_vegetation import VEGETATION_CLASSES
from terrasim2.k.vegetation_map import VegetationMap


def load_vegetation_map(folder: Path) -> VegetationMap:
    """Read a folder written by ``write_vegetation_map`` back into a VegetationMap.

    Needs only NumPy and the standard library. Refuses a manifest whose
    version is not ``VegetationMap.FORMAT_VERSION`` or whose classes are
    not the ones this code knows.

    Parameters
    ----------
    folder : Path
        Contains manifest.json and the array file it names.

    Returns
    -------
    VegetationMap
    """
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text())
    version = manifest.get("version")
    if version != VegetationMap.FORMAT_VERSION:
        raise ValueError(f"vegetation map at {folder} is format version {version}; this reader needs {VegetationMap.FORMAT_VERSION}")
    if tuple(manifest["classes"]) != VEGETATION_CLASSES:
        raise ValueError(f"vegetation map at {folder} uses classes {manifest['classes']}, not the ones this code knows")
    with np.load(folder / manifest["file"]) as arrays:
        class_index = arrays["class_index"]
        features = {name: arrays[name] for name in manifest["features"]}
    return VegetationMap(class_index, features, meta=manifest.get("meta", {}))


DEV_SITES = Path(__file__).resolve().parents[2] / "data" / "dev_sites"


def t1():
    """Round trip: what write_vegetation_map wrote comes back equal; a wrong version or other classes are refused."""
    import tempfile

    from terrasim2.f.write_vegetation_map import write_vegetation_map
    from terrasim2.k.vegetation_map import _example

    original = _example()
    folder = write_vegetation_map(original, Path(tempfile.mkdtemp()) / "vegetation")
    back = load_vegetation_map(folder)
    assert np.array_equal(back.class_index, original.class_index) and back.meta == original.meta
    for name in original.features:
        assert np.array_equal(back.features[name], original.features[name], equal_nan=True), name
    manifest = json.loads((folder / "manifest.json").read_text())
    for change in ({"version": VegetationMap.FORMAT_VERSION + 1}, {"classes": ["grass", "shrub", "tree"]}):
        (folder / "manifest.json").write_text(json.dumps({**manifest, **change}))
        try:
            load_vegetation_map(folder)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {change}")


def t2():
    """Every committed vegetation map sits on its site's grid and has a tree share between none and most."""
    from terrasim2.f.load_model_inputs import load_model_inputs

    folders = sorted(DEV_SITES.glob("*/vegetation"))
    assert len(folders) >= 5, [p.parent.name for p in folders]
    for folder in folders:
        v = load_vegetation_map(folder)
        inputs = load_model_inputs(folder.parent / "model_inputs")
        assert v.shape == inputs.shape, f"{folder}: the map must sit on the site's grid"
        assert v.meta["stub"] == folder.parent.name
        assert 0.0 <= v.compute_fraction("tree") <= 0.8, f"{folder}: tree share {v.compute_fraction('tree')}"
        assert (v.class_index >= 0).mean() > 0.9, f"{folder}: most cells should be classified"


def t():
    t1()
    t2()
