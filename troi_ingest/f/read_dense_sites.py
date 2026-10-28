import csv
from datetime import date
from pathlib import Path

DENSE_SITES_CSV = Path(__file__).resolve().parents[2] / "data" / "dense_sites.csv"


def read_dense_sites(path: Path = DENSE_SITES_CSV) -> list[dict]:
    """Read the validation site table into one dict per site.

    Parameters
    ----------
    path : Path
        ``data/dense_sites.csv`` by default.

    Returns
    -------
    list of dict
        Each with ``stub`` (str), ``site`` (str), ``bbox`` (list of four
        floats, west south east north, degrees), ``start`` and ``end``
        (date, inclusive), and ``notes`` (str). In file order.
    """
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    sites = []
    for r in rows:
        bbox = [float(r[k]) for k in ("west", "south", "east", "north")]
        if not (bbox[0] < bbox[2] and bbox[1] < bbox[3]):
            raise ValueError(f"site {r['stub']}: bbox must satisfy west < east and south < north, got {bbox}")
        start, end = date.fromisoformat(r["start"]), date.fromisoformat(r["end"])
        if start > end:
            raise ValueError(f"site {r['stub']}: start {start} is after end {end}")
        sites.append({"stub": r["stub"], "site": r["site"], "bbox": bbox, "start": start, "end": end, "notes": r.get("notes", "")})
    return sites


def t1():
    """The committed table has six distinct sites with valid bboxes and date ranges."""
    sites = read_dense_sites()
    stubs = [s["stub"] for s in sites]
    assert len(stubs) == 6 and len(set(stubs)) == 6, stubs
    assert "esdale" in stubs and "tarrawarra" in stubs
    for s in sites:
        w, so, e, n = s["bbox"]
        assert 140 < w < e < 155 and -40 < so < n < -28, s
        assert s["start"] <= s["end"]
        assert (e - w) < 0.1 and (n - so) < 0.1, "dense sites are a few km across"


def t2():
    """A malformed row is rejected with the stub named."""
    import tempfile

    bad = Path(tempfile.mkdtemp()) / "sites.csv"
    bad.write_text("stub,site,west,south,east,north,start,end,notes\nx,X,150.0,-33.0,149.0,-32.0,2024-01-01,2024-01-31,\n")
    try:
        read_dense_sites(bad)
    except ValueError as err:
        assert "site x" in str(err)
    else:
        raise AssertionError("expected ValueError for west > east")


def t():
    t1()
    t2()
