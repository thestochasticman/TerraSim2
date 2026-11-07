from pathlib import Path

import pandas as pd

# The lab's compiled observation file for the dense sites; see data/dense_sites.md.
DENSE_OBSERVATIONS = Path.home() / "Downloads" / "Dense_sites" / "all_sites_observations.parquet"
COLUMNS = ("site", "station", "lon", "lat", "time", "depth_top_m", "depth_bottom_m", "vwc", "n")


def read_dense_observations(sites: tuple[str, ...], path: Path = DENSE_OBSERVATIONS) -> pd.DataFrame:
    """The rows of the compiled observation file for some of its sites.

    Parameters
    ----------
    sites : tuple of str
        Values of the file's ``site`` column to keep, for example
        ``("esdale", "phenode")``.
    path : Path
        A parquet file with the columns ``site, station, lon, lat
        (degrees), time, depth_top_m, depth_bottom_m (m), vwc (m3 m-3),
        n (readings averaged)``.

    Returns
    -------
    DataFrame
        Those columns, the matching rows in file order, ``time`` as
        datetime64.

    Raises
    ------
    FileNotFoundError
        If the file is not there.
    ValueError
        If a column is missing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"no observation file at {path}")
    df = pd.read_parquet(path)
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} lacks the columns {missing}")
    out = df.loc[df["site"].isin(sites), list(COLUMNS)].reset_index(drop=True)
    out["time"] = pd.to_datetime(out["time"])
    return out


def _write_example(path: Path) -> Path:
    df = pd.DataFrame(
        {
            "site": ["a", "a", "b"],
            "station": ["s1", "s1", "s2"],
            "lon": [145.44, 145.44, 145.0],
            "lat": [-37.655, -37.655, -37.0],
            "time": pd.to_datetime(["1995-09-25", "1995-09-26", "1995-09-25"]),
            "depth_top_m": [0.0, 0.0, 0.0],
            "depth_bottom_m": [0.3, 0.3, 0.3],
            "vwc": [0.3, 0.31, 0.2],
            "n": [1, 1, 2],
        }
    )
    df.to_parquet(path)
    return path


def t1():
    """Keeps only the asked sites with the declared columns; a missing file or column is refused."""
    import tempfile

    folder = Path(tempfile.mkdtemp())
    path = _write_example(folder / "obs.parquet")
    a = read_dense_observations(("a",), path)
    assert len(a) == 2 and list(a.columns) == list(COLUMNS) and a["time"].dtype.kind == "M"
    assert len(read_dense_observations(("a", "b"), path)) == 3 and read_dense_observations(("c",), path).empty
    try:
        read_dense_observations(("a",), folder / "nowhere.parquet")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected FileNotFoundError")
    pd.DataFrame({"site": ["a"], "vwc": [0.2]}).to_parquet(folder / "short.parquet")
    try:
        read_dense_observations(("a",), folder / "short.parquet")
    except ValueError as err:
        assert "lacks" in str(err)
    else:
        raise AssertionError("expected ValueError for missing columns")


def t2():
    """The lab's file, when present, holds tarrawarra's 13 campaigns at 0 to 0.3 m."""
    from unittest import SkipTest

    if not DENSE_OBSERVATIONS.exists():
        raise SkipTest(f"no observation file at {DENSE_OBSERVATIONS}")
    t = read_dense_observations(("tarrawarra",))
    assert 8000 < len(t) < 9000 and t["depth_bottom_m"].eq(0.3).all()
    assert str(t["time"].min().date()) == "1995-09-25" and str(t["time"].max().date()) == "1996-11-29"


def t():
    t1()
    t2()
