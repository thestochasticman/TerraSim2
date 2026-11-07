from pathlib import Path

from app.api.f.find_inputs import DEV_SITES


def find_vegetation(stub: str, roots: tuple[Path, ...] = (DEV_SITES,)) -> Path | None:
    """The prepared vegetation map folder for a site stub, if any root holds one.

    Looks in each root for ``{root}/{stub}/vegetation/manifest.json``, the
    same search as ``find_inputs``, but a site without a map is an
    ordinary case rather than an error: a run then takes one root depth
    everywhere.

    Parameters
    ----------
    stub : str
    roots : tuple of Path
        Searched in order.

    Returns
    -------
    Path or None
        The ``vegetation`` folder, or None when no root holds one.
    """
    for root in roots:
        folder = Path(root) / stub / "vegetation"
        if (folder / "manifest.json").exists():
            return folder
    return None


def t():
    """Finds a committed site, prefers an earlier root, and gives None when nothing matches."""
    import tempfile

    assert find_vegetation("tarrawarra") == DEV_SITES / "tarrawarra" / "vegetation"
    other = Path(tempfile.mkdtemp())
    (other / "tarrawarra" / "vegetation").mkdir(parents=True)
    (other / "tarrawarra" / "vegetation" / "manifest.json").write_text("{}")
    assert find_vegetation("tarrawarra", roots=(other, DEV_SITES)) == other / "tarrawarra" / "vegetation"
    assert find_vegetation("example") is None and find_vegetation("nowhere") is None
