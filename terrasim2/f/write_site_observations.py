import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from terrasim2.k.site_observations import SiteObservations


def write_site_observations(observations: SiteObservations, folder: Path) -> Path:
    """Write a SiteObservations to a folder in the versioned on-disk layout.

    The layout needs only NumPy and the standard library to read back:

        manifest.json       version, rows, cols, n_points, stations, dates
                            (first and last), columns with units, written_at, meta
        observations.npz    compressed arrays, one per column: dates
                            (datetime64[D]), row, col, station (int32),
                            depth_top, depth_bottom (float64, m),
                            vwc (float64, m3 m-3), n (int32)

    Existing files in the folder are overwritten.

    Parameters
    ----------
    observations : SiteObservations
    folder : Path
        Created if missing.

    Returns
    -------
    Path
        ``folder``.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        folder / "observations.npz",
        dates=observations.dates,
        row=observations.row.astype(np.int32),
        col=observations.col.astype(np.int32),
        station=observations.station.astype(np.int32),
        depth_top=observations.depth_top,
        depth_bottom=observations.depth_bottom,
        vwc=observations.vwc,
        n=observations.n.astype(np.int32),
    )
    manifest = {
        "version": SiteObservations.FORMAT_VERSION,
        "rows": observations.shape[0],
        "cols": observations.shape[1],
        "n_points": observations.n_points,
        "stations": observations.stations,
        "start": str(observations.survey_dates[0]),
        "end": str(observations.survey_dates[-1]),
        "n_dates": int(observations.survey_dates.size),
        "file": "observations.npz",
        "columns": {
            "dates": {"units": "datetime64[D]"},
            "row": {"units": "dimensionless"},
            "col": {"units": "dimensionless"},
            "station": {"units": "index into stations"},
            "depth_top": {"units": "m"},
            "depth_bottom": {"units": "m"},
            "vwc": {"units": "m3 m-3"},
            "n": {"units": "readings averaged"},
        },
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "meta": observations.meta,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return folder


def t():
    """Writes the manifest and one compressed array file with the declared dtypes and the exact values."""
    import tempfile

    from terrasim2.k.site_observations import _example

    folder = write_site_observations(_example(), Path(tempfile.mkdtemp()) / "observations")
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["version"] == SiteObservations.FORMAT_VERSION
    assert (manifest["rows"], manifest["cols"], manifest["n_points"], manifest["n_dates"]) == (3, 4, 3, 2)
    assert manifest["stations"] == ["a", "b"] and manifest["start"] == "2024-01-02" and manifest["end"] == "2024-01-05"
    assert manifest["meta"] == {"stub": "unit"} and manifest["columns"]["vwc"]["units"] == "m3 m-3"
    with np.load(folder / manifest["file"]) as arrays:
        assert set(arrays.files) == set(manifest["columns"])
        assert arrays["dates"].dtype == np.dtype("datetime64[D]") and str(arrays["dates"][2]) == "2024-01-05"
        assert arrays["row"].dtype == np.int32 and arrays["row"].tolist() == [0, 2, 0]
        assert arrays["vwc"].dtype == np.float64 and arrays["vwc"].tolist() == [0.25, 0.31, 0.2]
        assert arrays["n"].tolist() == [1, 3, 1] and arrays["depth_bottom"].tolist() == [0.3, 0.3, 0.3]
