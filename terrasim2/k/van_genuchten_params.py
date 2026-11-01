from dataclasses import dataclass


@dataclass(frozen=True)
class VanGenuchtenParams:
    """Parameters of the van Genuchten (1980) soil water retention curve.

    The curve is eq. 5.29 of Bittelli, Campbell and Tomei, *Soil Physics
    with Python* (2015), with the usual restriction ``m = 1 - 1/n`` so the
    curve has four parameters rather than five.

    Attributes
    ----------
    theta_s : float, m3 m-3
        Saturated volumetric water content, in (0, 1].
    theta_r : float, m3 m-3
        Residual water content the curve approaches as the soil dries.
        At least 0 and below theta_s.
    alpha : float, kg J-1
        Inverse of a characteristic potential; roughly where the curve
        bends away from saturation. Positive.
    n : float, dimensionless
        Shape parameter; larger n gives a steeper fall. Must exceed 1 so
        that ``m = 1 - 1/n`` is positive.
    """

    theta_s: float
    theta_r: float
    alpha: float
    n: float

    def __post_init__(self):
        if not 0 < self.theta_s <= 1:
            raise ValueError(f"theta_s must be in (0, 1], got {self.theta_s}")
        if not 0 <= self.theta_r < self.theta_s:
            raise ValueError(f"theta_r must be in [0, theta_s), got {self.theta_r} with theta_s {self.theta_s}")
        if not self.alpha > 0:
            raise ValueError(f"alpha must be positive, got {self.alpha}")
        if not self.n > 1:
            raise ValueError(f"n must exceed 1, got {self.n}")

    @property
    def m(self) -> float:
        """The restricted shape exponent ``1 - 1/n``, dimensionless."""
        return 1.0 - 1.0 / self.n


def t1():
    """Valid parameters are stored as given, m follows from n, and the object is immutable."""
    p = VanGenuchtenParams(theta_s=0.46, theta_r=0.01, alpha=0.15, n=1.35)
    assert (p.theta_s, p.theta_r, p.alpha, p.n) == (0.46, 0.01, 0.15, 1.35)
    assert abs(p.m - (1 - 1 / 1.35)) < 1e-12
    assert VanGenuchtenParams(0.4, 0.0, 1.0, 2.0).m == 0.5
    try:
        p.n = 2.0  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("expected params to be frozen")


def t2():
    """Each bound is enforced: theta_s in (0, 1], 0 <= theta_r < theta_s, alpha > 0, n > 1."""
    bad = [
        dict(theta_s=0.0, theta_r=0.0, alpha=0.1, n=1.5),
        dict(theta_s=1.2, theta_r=0.0, alpha=0.1, n=1.5),
        dict(theta_s=0.4, theta_r=-0.1, alpha=0.1, n=1.5),
        dict(theta_s=0.4, theta_r=0.4, alpha=0.1, n=1.5),
        dict(theta_s=0.4, theta_r=0.0, alpha=0.0, n=1.5),
        dict(theta_s=0.4, theta_r=0.0, alpha=0.1, n=1.0),
    ]
    for kwargs in bad:
        try:
            VanGenuchtenParams(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")


def t():
    t1()
    t2()
