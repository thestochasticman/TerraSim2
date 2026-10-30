from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEV_DATA = REPO / "dev_data"


def find_inputs(stub: str, roots: tuple[Path, ...] = (DEV_DATA,)) -> Path:
    """The prepared model inputs folder for a site stub.

    Looks in each root for ``{root}/{stub}/model_inputs/manifest.json`` and
    returns the first match. By default only the committed ``dev_data`` is
    searched; the service puts the Troi output directory in front of it.

    Parameters
    ----------
    stub : str
    roots : tuple of Path
        Searched in order.

    Returns
    -------
    Path
        The ``model_inputs`` folder.

    Raises
    ------
    FileNotFoundError
        If no root holds inputs for the stub.
    """
    for root in roots:
        folder = Path(root) / stub / "model_inputs"
        if (folder / "manifest.json").exists():
            return folder
    raise FileNotFoundError(f"no prepared inputs for {stub!r} under {[str(r) for r in roots]}")


def t():
    """Finds a committed site, prefers an earlier root, and names the stub when nothing matches."""
    import tempfile

    assert find_inputs("tarrawarra") == DEV_DATA / "tarrawarra" / "model_inputs"
    other = Path(tempfile.mkdtemp())
    (other / "tarrawarra" / "model_inputs").mkdir(parents=True)
    (other / "tarrawarra" / "model_inputs" / "manifest.json").write_text("{}")
    assert find_inputs("tarrawarra", roots=(other, DEV_DATA)) == other / "tarrawarra" / "model_inputs"
    assert find_inputs("esdale", roots=(other, DEV_DATA)) == DEV_DATA / "esdale" / "model_inputs"
    try:
        find_inputs("nowhere")
    except FileNotFoundError as err:
        assert "nowhere" in str(err)
    else:
        raise AssertionError("expected FileNotFoundError")
