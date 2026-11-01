from dataclasses import dataclass


@dataclass(frozen=True)
class CampbellParams:
    """Parameters of Campbell's (1974) soil water retention curve.

    The curve is eq. 5.27 of Bittelli, Campbell and Tomei, *Soil Physics
    with Python* (2015): water content is ``theta_s`` at potentials wetter
    than air entry, and falls as a power of the potential below it.

    Attributes
    ----------
    theta_s : float, m3 m-3
        Saturated volumetric water content, in (0, 1].
    psi_e : float, J kg-1
        Air-entry potential: the matric potential at which the largest
        pores start to drain. Negative.
    b : float, dimensionless
        Shape parameter tied to the pore size distribution. Larger b means
        water content falls more slowly as the soil dries. Positive.
    """

    theta_s: float
    psi_e: float
    b: float

    def __post_init__(self):
        if not 0 < self.theta_s <= 1:
            raise ValueError(f"theta_s must be in (0, 1], got {self.theta_s}")
        if not self.psi_e < 0:
            raise ValueError(f"psi_e must be negative, got {self.psi_e}")
        if not self.b > 0:
            raise ValueError(f"b must be positive, got {self.b}")


def t1():
    """Valid parameters are stored as given and the object is immutable."""
    p = CampbellParams(theta_s=0.46, psi_e=-4.2, b=3.58)
    assert (p.theta_s, p.psi_e, p.b) == (0.46, -4.2, 3.58)
    try:
        p.b = 2.0  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("expected params to be frozen")


def t2():
    """Each bound is enforced: theta_s in (0, 1], psi_e negative, b positive."""
    bad = [
        dict(theta_s=0.0, psi_e=-1.0, b=2.0),
        dict(theta_s=1.5, psi_e=-1.0, b=2.0),
        dict(theta_s=0.4, psi_e=0.0, b=2.0),
        dict(theta_s=0.4, psi_e=1.0, b=2.0),
        dict(theta_s=0.4, psi_e=-1.0, b=0.0),
    ]
    for kwargs in bad:
        try:
            CampbellParams(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")


def t():
    t1()
    t2()
