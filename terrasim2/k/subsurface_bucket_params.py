from dataclasses import dataclass


@dataclass(frozen=True)
class SubsurfaceBucketParams:
    """Tunable parameters of the subsurface bucket step.

    Attributes
    ----------
    stress_exponent : float, dimensionless
        Evaporation is reference evapotranspiration times
        ``(plant store fullness) ** stress_exponent``. Positive.
    percolation_fraction : float, dimensionless
        The share of a cell's conductivity that acts straight down out of
        the root zone: 0 for an impermeable base under the roots, 1 for
        free drainage. In [0, 1].
    rain_hours : float, hours
        How long the day's rain is taken to fall. The infiltration limit
        for the day is the saturated conductivity times gravity times this
        duration; 24 is the lenient limit, a few hours a storm. Positive.
    lateral_multiplier : float, dimensionless
        How many times the matrix conductivity the conductivity along the
        slope is: the anisotropy that macropores and layer boundaries give
        a real hillslope. Scales the downslope lateral flow only; 1 is the
        matrix value, tens are usual in the field. Positive.
    aspect_strength : float, dimensionless
        How much each cell's evaporative demand follows the sun its slope
        receives: demand is the reference evapotranspiration times the
        terrain's ``solar_ratio`` to this power. 0 ignores aspect; 1 scales
        demand by the full direct-beam ratio, which overstates it, since
        diffuse light and the rest of the energy balance do not tilt with
        the ground. Non-negative.
    """

    stress_exponent: float = 1.0
    percolation_fraction: float = 0.0
    rain_hours: float = 24.0
    lateral_multiplier: float = 1.0
    aspect_strength: float = 0.0

    def __post_init__(self):
        if not self.stress_exponent > 0:
            raise ValueError(f"stress_exponent must be positive, got {self.stress_exponent}")
        if not 0 <= self.percolation_fraction <= 1:
            raise ValueError(f"percolation_fraction must be within [0, 1], got {self.percolation_fraction}")
        if not self.rain_hours > 0:
            raise ValueError(f"rain_hours must be positive, got {self.rain_hours}")
        if not self.lateral_multiplier > 0:
            raise ValueError(f"lateral_multiplier must be positive, got {self.lateral_multiplier}")
        if not self.aspect_strength >= 0:
            raise ValueError(f"aspect_strength must be non-negative, got {self.aspect_strength}")


def t():
    """Defaults are an impermeable base, all-day rain, the matrix conductivity and no aspect; each bound is enforced; the object is frozen."""
    p = SubsurfaceBucketParams()
    assert (p.stress_exponent, p.percolation_fraction, p.rain_hours, p.lateral_multiplier, p.aspect_strength) == (1.0, 0.0, 24.0, 1.0, 0.0)
    assert SubsurfaceBucketParams(percolation_fraction=1.0, rain_hours=6.0).rain_hours == 6.0
    assert SubsurfaceBucketParams(lateral_multiplier=30.0).lateral_multiplier == 30.0
    assert SubsurfaceBucketParams(aspect_strength=1.0).aspect_strength == 1.0
    for bad in (dict(stress_exponent=0.0), dict(percolation_fraction=-0.1), dict(percolation_fraction=1.5), dict(rain_hours=0.0), dict(lateral_multiplier=0.0), dict(aspect_strength=-0.5)):
        try:
            SubsurfaceBucketParams(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
    try:
        p.rain_hours = 6.0  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("expected params to be frozen")
