from dataclasses import dataclass


@dataclass(frozen=True)
class RunStoreParams:
    """How a run's histories are chunked and written to a zarr store.

    Attributes
    ----------
    chunk_days : int, dimensionless
        Days per chunk along the time axis. Longer chunks compress better
        and make one cell's time series cheaper to read.
    chunk_rows, chunk_cols : int, dimensionless
        Chunk size over the grid. Clipped to the grid if larger.
    write_every_days : int, dimensionless
        Days buffered in memory before a block is written. Memory held is
        this many days of moisture and fluxes. A multiple of ``chunk_days``
        avoids rewriting partly filled chunks.
    record_fluxes : bool
        Whether to store the per-day flux arrays at all. Off saves most of
        the disk when only moisture is wanted.
    """

    chunk_days: int = 32
    chunk_rows: int = 256
    chunk_cols: int = 256
    write_every_days: int = 32
    record_fluxes: bool = True

    def __post_init__(self):
        for name in ("chunk_days", "chunk_rows", "chunk_cols", "write_every_days"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1, got {getattr(self, name)}")


def t():
    """Defaults are positive, custom values stick, and non-positive sizes are rejected."""
    p = RunStoreParams()
    assert p.chunk_days == 32 and p.write_every_days == 32 and p.record_fluxes
    q = RunStoreParams(chunk_days=8, write_every_days=16, record_fluxes=False)
    assert q.chunk_days == 8 and q.write_every_days == 16 and not q.record_fluxes
    for bad in (dict(chunk_days=0), dict(chunk_rows=-1), dict(write_every_days=0)):
        try:
            RunStoreParams(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
