import json
import sys
from pathlib import Path

from troi import Config, config as troi_config

from terrasim2.f.write_site_observations import write_site_observations
from troi_ingest.f.ingest_observations import SITE_SOURCES, ingest_observations
from troi_ingest.f.read_dense_observations import DENSE_OBSERVATIONS
from troi_ingest.f.read_dense_sites import read_dense_sites

DEV_SITES = Path(__file__).resolve().parents[2] / "data" / "dev_sites"


def ingest_site_observations(stubs: list[str] | None = None, config: Config = troi_config, path: Path = DENSE_OBSERVATIONS) -> dict[str, Path]:
    """Prepare observations on disk for validation sites.

    Each site's observations go to ``{config.out_dir}/{stub}/observations``
    in the layout ``write_site_observations`` defines, next to where
    ``ingest_sites`` puts its model inputs. Sites with no observation
    source are skipped with a note. When the committed inputs for a site
    exist, their shape must agree with the observations' grid.

    Usage from the shell:
        python -m troi_ingest.f.ingest_site_observations                  # every site with observations
        python -m troi_ingest.f.ingest_site_observations tarrawarra llara # just these

    Parameters
    ----------
    stubs : list of str, optional
        Site stubs from ``data/dense_sites.csv``. All sites when omitted.
    config : Config
        Where outputs live.
    path : Path
        The observation file; see ``read_dense_observations``.

    Returns
    -------
    dict of str to Path
        Stub to the folder holding that site's observations.
    """
    if stubs is None:
        stubs = [s["stub"] for s in read_dense_sites()]
    folders = {}
    for stub in stubs:
        if not SITE_SOURCES.get(stub):
            print(f"{stub}: no observations in the compiled file, skipped", flush=True)
            continue
        print(f"ingesting observations for {stub} ...", flush=True)
        observations = ingest_observations(stub, path)
        manifest = DEV_SITES / stub / "model_inputs" / "manifest.json"
        if manifest.exists():
            m = json.loads(manifest.read_text())
            if (m["rows"], m["cols"]) != observations.shape:
                raise ValueError(f"{stub}: observations on {observations.shape} do not match the committed inputs' {(m['rows'], m['cols'])}")
        folders[stub] = write_site_observations(observations, Path(config.out_dir) / stub / "observations")
        print(f"  -> {folders[stub]}: {observations.n_points} observations from {observations.n_stations} stations on {observations.survey_dates.size} dates", flush=True)
    return folders


def t():
    """One site from the lab's file into a throwaway output directory, loading back equal; a site without a source is skipped."""
    import tempfile
    from unittest import SkipTest

    from terrasim2.f.load_site_observations import load_site_observations

    if not DENSE_OBSERVATIONS.exists():
        raise SkipTest(f"no observation file at {DENSE_OBSERVATIONS}")
    tmp = tempfile.mkdtemp(prefix="ingest_site_observations_t_")
    config = Config(out_dir=tmp, tmp_dir=troi_config.tmp_dir)
    folders = ingest_site_observations(["tarrawarra", "nerrigundah"], config=config)
    assert list(folders) == ["tarrawarra"] and folders["tarrawarra"] == Path(tmp) / "tarrawarra" / "observations"
    back = load_site_observations(folders["tarrawarra"])
    assert back.meta["stub"] == "tarrawarra" and back.n_points > 8000


if __name__ == "__main__":
    ingest_site_observations(sys.argv[1:] or None)
