from typing import Literal

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    """What the visualiser sends to start a run: everything that decides the run's identity.

    Attributes
    ----------
    stub : str
        A site stub whose prepared inputs exist, for example ``"tarrawarra"``.
    step : str
        Which process runs: ``"bucket"`` for closed per-cell buckets,
        ``"routed"`` for buckets whose overflow runs downhill, or
        ``"subsurface"`` for buckets with a free store that drains
        downslope through the soil.
    percolation_fraction : float, dimensionless
        ``SubsurfaceBucketParams.percolation_fraction``, in [0, 1]. Subsurface step only.
    rain_hours : float, hours
        ``SubsurfaceBucketParams.rain_hours``, positive. Subsurface step only.
    lateral_multiplier : float, dimensionless
        ``SubsurfaceBucketParams.lateral_multiplier``, positive. Subsurface step only.
    aspect_strength : float, dimensionless
        ``SubsurfaceBucketParams.aspect_strength``, non-negative. Subsurface step only.
    cover_strength : float, dimensionless
        How much each cell's evaporative demand follows its persistent
        cover: with a vegetation map for the site, the reference
        evapotranspiration is multiplied by the cell's crop coefficient
        relative to the site's mean, to this power, so the site's mean
        demand stays at the reference and only the pattern moves. 0
        ignores cover. Non-negative; every step.
    tree_root_depth : float, m, optional
        The root depth of tree cells when the site has a vegetation map;
        ``root_depth`` then applies to grass and unknown cells. Positive.
        Without a map, or when absent, ``root_depth`` applies everywhere.
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
    step: Literal["bucket", "routed", "subsurface"] = "bucket"
    stress_exponent: float = Field(default=1.0, gt=0)
    initial_fullness: float = Field(default=0.5, ge=0, le=1)
    root_depth: float = Field(default=0.3, gt=0)
    percolation_fraction: float = Field(default=0.0, ge=0, le=1)
    rain_hours: float = Field(default=24.0, gt=0)
    lateral_multiplier: float = Field(default=1.0, gt=0)
    aspect_strength: float = Field(default=0.0, ge=0)
    cover_strength: float = Field(default=0.0, ge=0)
    tree_root_depth: float | None = Field(default=None, gt=0)
    write_every_days: int = Field(default=1, ge=1)
    chunk_days: int = Field(default=32, ge=1)
    record_fluxes: bool = True


def t():
    """Defaults apply, fields validate, and the model round-trips through JSON."""
    r = RunRequest(stub="tarrawarra")
    assert r.stress_exponent == 1.0 and r.initial_fullness == 0.5 and r.write_every_days == 1 and r.root_depth == 0.3 and r.step == "bucket"
    assert RunRequest(stub="x", step="routed").step == "routed" and r.percolation_fraction == 0.0 and r.rain_hours == 24.0
    assert RunRequest(stub="x", step="subsurface", percolation_fraction=0.5, rain_hours=6).rain_hours == 6
    assert r.lateral_multiplier == 1.0 and RunRequest(stub="x", lateral_multiplier=30).lateral_multiplier == 30
    assert r.tree_root_depth is None and RunRequest(stub="x", tree_root_depth=1.5).tree_root_depth == 1.5
    assert r.aspect_strength == 0.0 and RunRequest(stub="x", aspect_strength=1).aspect_strength == 1
    assert r.cover_strength == 0.0 and RunRequest(stub="x", cover_strength=0.5).cover_strength == 0.5
    assert RunRequest.model_validate_json(r.model_dump_json()) == r
    for bad in (dict(stub=""), dict(stub="x", stress_exponent=0), dict(stub="x", initial_fullness=1.5), dict(stub="x", write_every_days=0), dict(stub="x", root_depth=0), dict(stub="x", step="darcy"), dict(stub="x", percolation_fraction=2), dict(stub="x", rain_hours=0), dict(stub="x", lateral_multiplier=0), dict(stub="x", tree_root_depth=0), dict(stub="x", aspect_strength=-1), dict(stub="x", cover_strength=-0.1)):
        try:
            RunRequest(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
