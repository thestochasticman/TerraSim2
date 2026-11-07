from dataclasses import dataclass


@dataclass(frozen=True)
class SubsurfaceBucketParams:
    """Tunable parameters of the subsurface bucket step.

    Attributes
    ----------
    stress_exponent : float, dimensionless
        Evaporation is reference evapotranspiration times
        ``(plant store fullness) ** stress_exponent``. Positive.
    leak_fraction : float, dimensionless
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
        a real hillslope. Scales the downslope drainage only; 1 is the
        matrix value, tens are usual in the field. Positive.
    """

    stress_exponent: float = 1.0
    leak_fraction: float = 0.0
    rain_hours: float = 24.0
    lateral_multiplier: float = 1.0

    def __post_init__(self):
        if not self.stress_exponent > 0:
            raise ValueError(f"stress_exponent must be positive, got {self.stress_exponent}")
        if not 0 <= self.leak_fraction <= 1:
            raise ValueError(f"leak_fraction must be within [0, 1], got {self.leak_fraction}")
        if not self.rain_hours > 0:
            raise ValueError(f"rain_hours must be positive, got {self.rain_hours}")
        if not self.lateral_multiplier > 0:
            raise ValueError(f"lateral_multiplier must be positive, got {self.lateral_multiplier}")


def t():
    """Defaults are an impermeable base, all-day rain and the matrix conductivity; each bound is enforced; the object is frozen."""
    p = SubsurfaceBucketParams()
    assert (p.stress_exponent, p.leak_fraction, p.rain_hours, p.lateral_multiplier) == (1.0, 0.0, 24.0, 1.0)
    assert SubsurfaceBucketParams(leak_fraction=1.0, rain_hours=6.0).rain_hours == 6.0
    assert SubsurfaceBucketParams(lateral_multiplier=30.0).lateral_multiplier == 30.0
    for bad in (dict(stress_exponent=0.0), dict(leak_fraction=-0.1), dict(leak_fraction=1.5), dict(rain_hours=0.0), dict(lateral_multiplier=0.0)):
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
