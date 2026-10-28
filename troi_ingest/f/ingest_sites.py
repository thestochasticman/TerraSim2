import sys
from pathlib import Path
from unittest import SkipTest

from troi import Config, config as troi_config

from troi_ingest.f.ingest_to_disk import ingest_to_disk
from troi_ingest.f.make_site_troi import make_site_troi
from troi_ingest.f.read_dense_sites import read_dense_sites


def ingest_sites(stubs: list[str] | None = None, config: Config = troi_config) -> dict[str, Path]:
    """Prepare model inputs on disk for validation sites.

    Each site becomes a Troi under ``config`` and goes through
    ``ingest_to_disk``, which fetches only what the stores do not already
    hold and skips sites whose inputs are already current.

    Usage from the shell:
        python -m troi_ingest.f.ingest_sites              # every site in dense_sites.csv
        python -m troi_ingest.f.ingest_sites esdale llara # just these

    Parameters
    ----------
    stubs : list of str, optional
        Site stubs from ``data/dense_sites.csv``. All sites when omitted.
    config : Config
        Where outputs and store caches live.

    Returns
    -------
    dict of str to Path
        Stub to the folder holding that site's model inputs.
    """
    if stubs is None:
        stubs = [s["stub"] for s in read_dense_sites()]
    folders = {}
    for stub in stubs:
        print(f"ingesting {stub} ...", flush=True)
        folders[stub] = ingest_to_disk(make_site_troi(stub, config=config))
        print(f"  -> {folders[stub]}", flush=True)
    return folders


def t1():
    """One real site end to end under a throwaway config: inputs land in that site's folder and load back."""
    import tempfile

    from terrasim2.f.load_model_inputs import load_model_inputs

    tmp = tempfile.mkdtemp(prefix="ingest_sites_t_")
    config = Config(out_dir=tmp, tmp_dir=troi_config.tmp_dir, email=troi_config.email, tern_api_key=troi_config.tern_api_key)
    try:
        folders = ingest_sites(["tarrawarra"], config=config)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"a data store is unavailable: {err}") from err
    folder = folders["tarrawarra"]
    assert folder == Path(tmp) / "tarrawarra" / "model_inputs"
    inputs = load_model_inputs(folder)
    assert inputs.meta["stub"] == "tarrawarra"
    assert inputs.dates[0].astype(str) == "1995-09-25" and inputs.dates[-1].astype(str) == "1996-11-29"
    assert 50 < inputs.grid.elevation.min() < inputs.grid.elevation.max() < 500, "Tarrawarra sits around 100 m"


def t():
    t1()


if __name__ == "__main__":
    ingest_sites(sys.argv[1:] or None)
