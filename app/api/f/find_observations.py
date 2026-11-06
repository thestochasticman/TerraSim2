from pathlib import Path

from app.api.f.find_inputs import DEV_SITES


def find_observations(stub: str, roots: tuple[Path, ...] = (DEV_SITES,)) -> Path:
    """The prepared observations folder for a site stub.

    Looks in each root for ``{root}/{stub}/observations/manifest.json`` and
    returns the first match, the same search as ``find_inputs``.

    Parameters
    ----------
    stub : str
    roots : tuple of Path
        Searched in order.

    Returns
    -------
    Path
        The ``observations`` folder.

    Raises
    ------
    FileNotFoundError
        If no root holds observations for the stub.
    """
    for root in roots:
        folder = Path(root) / stub / "observations"
        if (folder / "manifest.json").exists():
            return folder
    raise FileNotFoundError(f"no prepared observations for {stub!r} under {[str(r) for r in roots]}")


def t():
    """Finds a committed site, prefers an earlier root, and names the stub when nothing matches."""
    import tempfile

    assert find_observations("tarrawarra") == DEV_SITES / "tarrawarra" / "observations"
    other = Path(tempfile.mkdtemp())
    (other / "tarrawarra" / "observations").mkdir(parents=True)
    (other / "tarrawarra" / "observations" / "manifest.json").write_text("{}")
    assert find_observations("tarrawarra", roots=(other, DEV_SITES)) == other / "tarrawarra" / "observations"
    assert find_observations("llara", roots=(other, DEV_SITES)) == DEV_SITES / "llara" / "observations"
    for stub in ("example", "nerrigundah", "nowhere"):
        try:
            find_observations(stub)
        except FileNotFoundError as err:
            assert stub in str(err)
        else:
            raise AssertionError(f"expected FileNotFoundError for {stub}")
