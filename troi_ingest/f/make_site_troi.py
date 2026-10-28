from troi import Config, Troi, config as troi_config

from troi_ingest.f.read_dense_sites import read_dense_sites


def make_site_troi(stub: str, config: Config = troi_config) -> Troi:
    """The Troi for one site in ``data/dense_sites.csv``.

    Constructing a Troi registers it under ``config``; the same stub with a
    different bbox or dates raises, which is troi's own guard against a site
    silently changing identity.

    Parameters
    ----------
    stub : str
        A ``stub`` value from the site table, for example ``"esdale"``.
    config : Config
        Where outputs and store caches live. Defaults to the machine's troi config.

    Returns
    -------
    Troi
    """
    sites = {s["stub"]: s for s in read_dense_sites()}
    if stub not in sites:
        raise KeyError(f"no site {stub!r} in dense_sites.csv; have {sorted(sites)}")
    s = sites[stub]
    return Troi(bbox=s["bbox"], start=s["start"], end=s["end"], stub=stub, config=config)


def t1():
    """Builds a Troi for a known site with the table's bbox and dates, under a throwaway config."""
    import tempfile
    from datetime import date

    tmp = tempfile.mkdtemp(prefix="site_troi_t_")
    troi = make_site_troi("tarrawarra", config=Config(out_dir=tmp, tmp_dir=troi_config.tmp_dir))
    assert troi.stub == "tarrawarra"
    assert troi.bbox == [145.435, -37.659, 145.445, -37.652]
    assert troi.start == date(1995, 9, 25) and troi.end == date(1996, 11, 29)
    assert troi.out_dir.startswith(tmp)


def t2():
    """An unknown stub is rejected naming the known ones."""
    try:
        make_site_troi("nowhere")
    except KeyError as err:
        assert "esdale" in str(err)
    else:
        raise AssertionError("expected KeyError")


def t():
    t1()
    t2()
