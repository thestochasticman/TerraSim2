import tempfile
from datetime import date

from troi import Config, Troi, config as troi_config

TEST_BBOX = [148.36265, -33.52606, 148.38265, -33.50606]


def make_test_troi(stub: str = "troi_ingest_test") -> Troi:
    """A Troi for the lab's example region, safe to construct in tests.

    Its registry and outputs go to a fresh temporary directory, so test
    runs never touch the user's real Troi registry. Its ``tmp_dir`` and
    credentials are the user's real ones, so the data stores reuse their
    caches and can fetch what is missing.

    Parameters
    ----------
    stub : str
        Name recorded in the temporary registry.

    Returns
    -------
    Troi
        ``TEST_BBOX`` (degrees, EPSG:4326), January 2024.
    """
    out_dir = tempfile.mkdtemp(prefix="troi_ingest_t_")
    return Troi(
        bbox=list(TEST_BBOX),
        start=date(2024, 1, 1),
        end=date(2024, 1, 31),
        stub=stub,
        config=Config(
            out_dir=out_dir,
            tmp_dir=troi_config.tmp_dir,
            email=troi_config.email,
            tern_api_key=troi_config.tern_api_key,
        ),
    )


def t():
    """It constructs."""
    assert make_test_troi().bbox == TEST_BBOX
