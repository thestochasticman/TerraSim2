import json
from pathlib import Path


def read_inputs_key(inputs_folder: Path) -> str:
    """A short string that changes whenever a site's prepared inputs change.

    Built from the manifest's format version and ``written_at``, so a run
    made on older inputs is never mistaken for one on the current ones.

    Parameters
    ----------
    inputs_folder : Path
        A ``model_inputs`` folder.

    Returns
    -------
    str
        For example ``"v2@2026-11-01T06:12:40+00:00"``.
    """
    manifest = json.loads((Path(inputs_folder) / "manifest.json").read_text())
    return f"v{manifest['version']}@{manifest['written_at']}"


def t():
    """The key names the version and write time, and differs between two folders written at different times."""
    import tempfile

    from app.api.f.find_inputs import find_inputs

    key = read_inputs_key(find_inputs("example"))
    assert key.startswith("v3@20"), key
    folder = Path(tempfile.mkdtemp()) / "model_inputs"
    folder.mkdir()
    (folder / "manifest.json").write_text(json.dumps({"version": 2, "written_at": "2000-01-01T00:00:00+00:00"}))
    assert read_inputs_key(folder) == "v2@2000-01-01T00:00:00+00:00" != key
