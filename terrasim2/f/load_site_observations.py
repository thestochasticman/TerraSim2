import json
from pathlib import Path

import numpy as np

from terrasim2.k.site_observations import SiteObservations


def load_site_observations(folder: Path) -> SiteObservations:
    """Read a folder written by ``write_site_observations`` back into a SiteObservations.

    Needs only NumPy and the standard library. Refuses a manifest whose
    version is not ``SiteObservations.FORMAT_VERSION``.

    Parameters
    ----------
    folder : Path
        Contains manifest.json and the array file it names.

    Returns
    -------
    SiteObservations
    """
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text())
    version = manifest.get("version")
    if version != SiteObservations.FORMAT_VERSION:
        raise ValueError(f"site observations at {folder} are format version {version}; this reader needs {SiteObservations.FORMAT_VERSION}")
    with np.load(folder / manifest["file"]) as arrays:
        columns = {name: arrays[name] for name in arrays.files}
    return SiteObservations(
        shape=(manifest["rows"], manifest["cols"]),
        dates=columns["dates"],
        row=columns["row"],
        col=columns["col"],
        station=columns["station"],
        stations=manifest["stations"],
        depth_top=columns["depth_top"],
        depth_bottom=columns["depth_bottom"],
        vwc=columns["vwc"],
        n=columns["n"],
        meta=manifest.get("meta", {}),
    )


DEV_SITES = Path(__file__).resolve().parents[2] / "data" / "dev_sites"


def t1():
    """Round trip: what write_site_observations wrote comes back equal, and a wrong version is refused."""
    import tempfile

    from terrasim2.f.write_site_observations import write_site_observations
    from terrasim2.k.site_observations import _example

    original = _example()
    folder = write_site_observations(original, Path(tempfile.mkdtemp()) / "observations")
    back = load_site_observations(folder)
    assert back.shape == original.shape and back.stations == original.stations and back.meta == original.meta
    for name in ("dates", "row", "col", "station", "depth_top", "depth_bottom", "vwc", "n"):
        assert np.array_equal(getattr(back, name), getattr(original, name)), name
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["version"] = SiteObservations.FORMAT_VERSION + 1
    (folder / "manifest.json").write_text(json.dumps(manifest))
    try:
        load_site_observations(folder)
    except ValueError as err:
        assert "format version" in str(err)
    else:
        raise AssertionError("expected ValueError for version mismatch")


def t2():
    """Every committed observation folder loads, sits on its site's grid, and tarrawarra holds its 13 surveys at 0 to 0.3 m."""
    from terrasim2.f.load_model_inputs import load_model_inputs

    folders = sorted(DEV_SITES.glob("*/observations"))
    assert len(folders) >= 5, [p.parent.name for p in folders]
    for folder in folders:
        obs = load_site_observations(folder)
        inputs = load_model_inputs(folder.parent / "model_inputs")
        assert obs.shape == inputs.shape, f"{folder}: observations must sit on the site's grid"
        assert obs.meta["stub"] == folder.parent.name
        assert obs.survey_dates[0] >= inputs.dates[0] and obs.survey_dates[-1] <= inputs.dates[-1], f"{folder}: observations must fall within the inputs' dates"
    tarrawarra = load_site_observations(DEV_SITES / "tarrawarra" / "observations")
    assert tarrawarra.n_points > 8000 and tarrawarra.n_stations > 3000
    assert np.all(tarrawarra.depth_top == 0.0) and np.all(tarrawarra.depth_bottom == 0.3)
    assert 0.1 < tarrawarra.vwc.min() and tarrawarra.vwc.max() < 0.7
    assert str(tarrawarra.survey_dates[0]) == "1995-09-25" and str(tarrawarra.survey_dates[-1]) == "1996-11-29"


def t():
    t1()
    t2()
