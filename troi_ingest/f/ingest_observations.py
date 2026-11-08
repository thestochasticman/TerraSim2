from pathlib import Path

import numpy as np
import pandas as pd

from terrasim2.k.site_observations import SiteObservations
from troi_ingest.f.compute_window import compute_window
from troi_ingest.f.locate_points_on_window import locate_points_on_window
from troi_ingest.f.read_dense_observations import DENSE_OBSERVATIONS, read_dense_observations
from troi_ingest.f.read_dense_sites import read_dense_sites

# Which of the observation file's sites feed each stub in data/dense_sites.csv.
# Esdale's hand campaign and its Phenode loggers are two sites in the file and one in the table;
# SASMAS is a whole network, of which only the Stanley cluster lies in the bbox; Nerrigundah is not in the file.
SITE_SOURCES = {
    "esdale": ("esdale", "phenode"),
    "llara": ("llara",),
    "mri": ("mri",),
    "sasmas_stanley": ("sasmas",),
    "tarrawarra": ("tarrawarra",),
    "nerrigundah": (),
}


def ingest_observations(stub: str, path: Path = DENSE_OBSERVATIONS) -> SiteObservations:
    """A site's observations from the lab's compiled file, laid on the site's grid.

    The site's rows are read, each point is located on the Sentinel-2
    window of the site's bbox, and points outside it, outside the site's
    dates, or without a valid content are dropped and counted in ``meta``.
    Readings of one station at one depth on one day are averaged into one
    observation, weighted by how many readings each already stood for.

    Parameters
    ----------
    stub : str
        A ``stub`` from ``data/dense_sites.csv`` with an entry in ``SITE_SOURCES``.
    path : Path
        The observation file; see ``read_dense_observations``.

    Returns
    -------
    SiteObservations
        On the window of the site's bbox, sorted by date, station and depth.
    """
    sites = {s["stub"]: s for s in read_dense_sites()}
    if stub not in sites:
        raise KeyError(f"no site {stub!r} in dense_sites.csv; have {sorted(sites)}")
    sources = SITE_SOURCES.get(stub, ())
    if not sources:
        raise ValueError(f"{stub} has no observations in the compiled file")
    site = sites[stub]
    df = read_dense_observations(sources, path)
    n_read = len(df)
    row, col, inside = locate_points_on_window(df["lon"].values, df["lat"].values, site["bbox"])
    df = df.assign(row=row, col=col, date=df["time"].dt.floor("D").values.astype("datetime64[D]"))
    valid = np.isfinite(df["vwc"].values) & (df["vwc"].values >= 0) & (df["vwc"].values <= 1) & (df["n"].values > 0)
    in_dates = (df["date"].values >= np.datetime64(site["start"])) & (df["date"].values <= np.datetime64(site["end"]))
    kept = df[inside & valid & in_dates]

    weighted = kept.assign(weighted=kept["vwc"] * kept["n"])
    grouped = weighted.groupby(["date", "station", "depth_top_m", "depth_bottom_m"], as_index=False).agg(row=("row", "first"), col=("col", "first"), weighted=("weighted", "sum"), n=("n", "sum"))
    grouped = grouped.sort_values(["date", "station", "depth_top_m"]).reset_index(drop=True)
    stations = sorted(grouped["station"].unique())
    station_index = pd.Categorical(grouped["station"], categories=stations).codes
    row0, row1, col0, col1 = compute_window(site["bbox"])
    meta = {
        "stub": stub,
        "source": str(path),
        "sources": list(sources),
        "n_rows_read": int(n_read),
        "n_outside_window": int((~inside).sum()),
        "n_outside_dates": int((inside & ~in_dates).sum()),
        "n_invalid": int((inside & in_dates & ~valid).sum()),
        "n_readings": int(grouped["n"].sum()),
    }
    return SiteObservations(
        shape=(row1 - row0, col1 - col0),
        dates=grouped["date"].values,
        row=grouped["row"].values,
        col=grouped["col"].values,
        station=station_index,
        stations=stations,
        depth_top=grouped["depth_top_m"].values,
        depth_bottom=grouped["depth_bottom_m"].values,
        vwc=(grouped["weighted"] / grouped["n"]).values,
        n=grouped["n"].values,
        meta=meta,
    )


def t1():
    """A synthetic file for tarrawarra: points outside the bbox, outside the dates and with a bad content are dropped
    and counted; two readings of one station on one day become one weighted observation."""
    import tempfile

    folder = Path(tempfile.mkdtemp())
    inside_lon, inside_lat = 145.44, -37.655
    df = pd.DataFrame(
        {
            "site": ["tarrawarra"] * 6 + ["sasmas"],
            "station": ["p1", "p1", "p2", "p3", "p4", "p2", "x"],
            "lon": [inside_lon, inside_lon, inside_lon + 0.001, 145.0, inside_lon, inside_lon + 0.001, inside_lon],
            "lat": [inside_lat] * 2 + [inside_lat - 0.001, -37.0, inside_lat, inside_lat - 0.001, inside_lat],
            "time": pd.to_datetime(["1995-09-25 09:00", "1995-09-25 15:00", "1995-09-25", "1995-09-25", "1990-01-01", "1996-02-13", "1995-09-25"], format="mixed"),
            "depth_top_m": [0.0] * 7,
            "depth_bottom_m": [0.3] * 7,
            "vwc": [0.3, 0.4, 0.2, 0.25, 0.3, 1.5, 0.3],
            "n": [1, 3, 1, 1, 1, 1, 1],
        }
    )
    df.to_parquet(folder / "obs.parquet")
    obs = ingest_observations("tarrawarra", folder / "obs.parquet")
    assert obs.shape == tuple(np.subtract(compute_window([145.435, -37.659, 145.445, -37.652])[1::2], compute_window([145.435, -37.659, 145.445, -37.652])[0::2]))
    assert obs.n_points == 2 and obs.stations == ["p1", "p2"]
    assert abs(obs.vwc[0] - (0.3 * 1 + 0.4 * 3) / 4) < 1e-12 and obs.n[0] == 4, "p1's two readings averaged by weight"
    assert obs.vwc[1] == 0.2 and obs.n[1] == 1
    assert obs.meta["n_rows_read"] == 6 and obs.meta["n_outside_window"] == 1 and obs.meta["n_outside_dates"] == 1 and obs.meta["n_invalid"] == 1
    assert obs.meta["sources"] == ["tarrawarra"] and obs.meta["n_readings"] == 5
    try:
        ingest_observations("nerrigundah", folder / "obs.parquet")
    except ValueError as err:
        assert "no observations" in str(err)
    else:
        raise AssertionError("expected ValueError for a site without a source")


def t2():
    """The lab's file, when present: tarrawarra keeps every point, sasmas_stanley keeps only the Stanley cluster."""
    from unittest import SkipTest

    if not DENSE_OBSERVATIONS.exists():
        raise SkipTest(f"no observation file at {DENSE_OBSERVATIONS}")
    t = ingest_observations("tarrawarra")
    assert t.meta["n_outside_window"] == 0 and 8000 < t.n_points < 9000 and t.n_stations > 3000
    s = ingest_observations("sasmas_stanley")
    assert s.n_stations == 7 and all(name.startswith("SASMAS_S") for name in s.stations), s.stations
    assert s.meta["n_outside_window"] > s.n_points


def t():
    t1()
    t2()
