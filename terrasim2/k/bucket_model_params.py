from dataclasses import dataclass


@dataclass(frozen=True)
class BucketModelParams:
    """Tunable parameters of the bucket model step.

    Attributes
    ----------
    stress_exponent : float, dimensionless
        Evaporation is reference evapotranspiration times
        ``(moisture / capacity) ** stress_exponent``. 1 is linear stress;
        larger values hold evaporation back harder as the bucket dries.
        Must be positive.
    """

    stress_exponent: float = 1.0

    def __post_init__(self):
        if not self.stress_exponent > 0:
            raise ValueError(f"stress_exponent must be positive, got {self.stress_exponent}")


def t1():
    """Defaults to linear stress; accepts other positive exponents."""
    assert BucketModelParams().stress_exponent == 1.0
    assert BucketModelParams(stress_exponent=2.5).stress_exponent == 2.5


def t2():
    """Non-positive exponents are rejected, and the object is immutable."""
    for bad in (0.0, -1.0):
        try:
            BucketModelParams(stress_exponent=bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
    p = BucketModelParams()
    try:
        p.stress_exponent = 2.0  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("expected params to be frozen")


def t():
    t1()
    t2()
