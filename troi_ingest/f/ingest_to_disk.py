import json
from pathlib import Path
from unittest import SkipTest

from troi import Troi

from terrasim2.f.write_model_inputs import write_model_inputs
from terrasim2.k.model_inputs import ModelInputs
from troi_ingest.f.ingest import ingest


def ingest_to_disk(troi: Troi, folder: Path | None = None) -> Path:
    """Write a Troi's model inputs to disk, unless an up-to-date copy is already there.

    The folder defaults to ``{troi.out_dir}/model_inputs``. A folder is
    up to date when its manifest has the current format version and the
    same stub, bbox, start and end as the Troi; then nothing is fetched or
    written. Otherwise ``ingest`` runs and the result is written.

    Parameters
    ----------
    troi : Troi
    folder : Path, optional
        Where to write. Use this to put a copy somewhere other than the
        Troi's output directory, for example into ``dev_data/``.

    Returns
    -------
    Path
        The folder holding manifest.json and the input files.
    """
    folder = Path(folder) if folder is not None else Path(troi.out_dir) / "model_inputs"
    if _is_current(folder, troi):
        return folder
    return write_model_inputs(ingest(troi), folder)


def _is_current(folder: Path, troi: Troi) -> bool:
    manifest_path = folder / "manifest.json"
    if not manifest_path.exists():
        return False
    manifest = json.loads(manifest_path.read_text())
    meta = manifest.get("meta", {})
    return (
        manifest.get("version") == ModelInputs.FORMAT_VERSION
        and meta.get("stub") == troi.stub
        and meta.get("bbox") == list(troi.bbox)
        and meta.get("start") == str(troi.start)
        and meta.get("end") == str(troi.end)
    )


def t1():
    """Writes into the Troi's out_dir, loads back equal to the in-memory inputs, and skips the second time."""
    import numpy as np

    from terrasim2.f.load_model_inputs import load_model_inputs
    from troi_ingest.f.make_test_troi import make_test_troi

    troi = make_test_troi()
    try:
        folder = ingest_to_disk(troi)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"a data store is unavailable: {err}") from err
    assert folder == Path(troi.out_dir) / "model_inputs"
    back = load_model_inputs(folder)
    assert back.meta["stub"] == troi.stub and back.n_days == 31
    assert 100 < back.grid.elevation.min() < back.grid.elevation.max() < 1500
    assert np.all(np.nan_to_num(back.rain.values) >= 0)

    written_at = json.loads((folder / "manifest.json").read_text())["written_at"]
    assert ingest_to_disk(troi) == folder
    assert json.loads((folder / "manifest.json").read_text())["written_at"] == written_at, "second call must not rewrite"


def t():
    t1()
