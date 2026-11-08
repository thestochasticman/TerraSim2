import json
import sys
from pathlib import Path

from troi import Config, config as troi_config

from terrasim2.f.write_vegetation_map import write_vegetation_map
from terrasim2.k.vegetation_thresholds import VegetationThresholds
from troi_ingest.f.ingest_vegetation import ingest_vegetation
from troi_ingest.f.read_dense_sites import read_dense_sites

DEV_SITES = Path(__file__).resolve().parents[2] / "data" / "dev_sites"


def ingest_site_vegetation(stubs: list[str] | None = None, thresholds: VegetationThresholds = VegetationThresholds(), config: Config = troi_config) -> dict[str, Path]:
    """Prepare vegetation maps on disk for validation sites.

    Each site's map goes to ``{config.out_dir}/{stub}/vegetation`` in the
    layout ``write_vegetation_map`` defines, next to its model inputs and
    observations. When the committed inputs for a site exist, their shape
    must agree with the map's grid.

    Usage from the shell:
        python -m troi_ingest.f.ingest_site_vegetation                  # every site
        python -m troi_ingest.f.ingest_site_vegetation tarrawarra llara # just these

    Parameters
    ----------
    stubs : list of str, optional
        Site stubs from ``data/dense_sites.csv``. All sites when omitted.
    thresholds : VegetationThresholds
    config : Config
        Where outputs and the Sentinel-2 cube live.

    Returns
    -------
    dict of str to Path
        Stub to the folder holding that site's vegetation map.
    """
    if stubs is None:
        stubs = [s["stub"] for s in read_dense_sites()]
    folders = {}
    for stub in stubs:
        print(f"ingesting vegetation for {stub} ...", flush=True)
        vegetation = ingest_vegetation(stub, thresholds, config)
        manifest = DEV_SITES / stub / "model_inputs" / "manifest.json"
        if manifest.exists():
            m = json.loads(manifest.read_text())
            if (m["rows"], m["cols"]) != vegetation.shape:
                raise ValueError(f"{stub}: map on {vegetation.shape} does not match the committed inputs' {(m['rows'], m['cols'])}")
        folders[stub] = write_vegetation_map(vegetation, Path(config.out_dir) / stub / "vegetation")
        print(f"  -> {folders[stub]}: {vegetation.compute_fraction('tree'):.0%} tree, {int((vegetation.class_index < 0).sum())} unknown cells", flush=True)
    return folders


def t():
    """One site from the cube into a throwaway output directory, loading back equal."""
    import tempfile
    from unittest import SkipTest

    from terrasim2.f.load_vegetation_map import load_vegetation_map

    tmp = tempfile.mkdtemp(prefix="ingest_site_vegetation_t_")
    config = Config(out_dir=tmp, tmp_dir=troi_config.tmp_dir)
    try:
        folders = ingest_site_vegetation(["tarrawarra"], config=config)
    except (OSError, ConnectionError, TimeoutError) as err:
        raise SkipTest(f"Sentinel-2 cube unavailable: {err}") from err
    assert folders["tarrawarra"] == Path(tmp) / "tarrawarra" / "vegetation"
    back = load_vegetation_map(folders["tarrawarra"])
    assert back.meta["stub"] == "tarrawarra" and (back.class_index >= 0).mean() > 0.95


if __name__ == "__main__":
    ingest_site_vegetation(sys.argv[1:] or None)
