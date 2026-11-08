from typing import Literal

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    """What the visualiser sends to start a run: everything that decides the run's identity.

    Attributes
    ----------
    stub : str
        A site stub whose prepared inputs exist, for example ``"tarrawarra"``.
    step : str
        Which process runs: ``"bucket"`` for closed per-cell buckets, or
        ``"routed"`` for buckets whose overflow runs downhill.
    stress_exponent : float, dimensionless
        ``BucketModelParams.stress_exponent``. Positive.
    initial_fullness : float, dimensionless
        Moisture at day zero as a fraction of capacity, in [0, 1].
    root_depth : float, m
        How deep the roots reach: each cell's capacity is its soil's
        available water down to this depth. Positive. Ignored by inputs
        that carry no soil layers.
    write_every_days : int, dimensionless
        Days the run buffers before writing a block. 1 shows progress day by day.
    chunk_days : int, dimensionless
        ``RunStoreParams.chunk_days``.
    record_fluxes : bool
        Whether the run stores fluxes.
    """

    stub: str = Field(min_length=1)
    step: Literal["bucket", "routed"] = "bucket"
    stress_exponent: float = Field(default=1.0, gt=0)
    initial_fullness: float = Field(default=0.5, ge=0, le=1)
    root_depth: float = Field(default=0.3, gt=0)
    write_every_days: int = Field(default=1, ge=1)
    chunk_days: int = Field(default=32, ge=1)
    record_fluxes: bool = True


def t():
    """Defaults apply, fields validate, and the model round-trips through JSON."""
    r = RunRequest(stub="tarrawarra")
    assert r.stress_exponent == 1.0 and r.initial_fullness == 0.5 and r.write_every_days == 1 and r.root_depth == 0.3 and r.step == "bucket"
    assert RunRequest(stub="x", step="routed").step == "routed"
    assert RunRequest.model_validate_json(r.model_dump_json()) == r
    for bad in (dict(stub=""), dict(stub="x", stress_exponent=0), dict(stub="x", initial_fullness=1.5), dict(stub="x", write_every_days=0), dict(stub="x", root_depth=0), dict(stub="x", step="darcy")):
        try:
            RunRequest(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
