from dataclasses import dataclass


@dataclass(frozen=True)
class SoilConventions:
    """Where on a retention curve the model reads field capacity and wilting point.

    The book's convention, -33 and -1500 J/kg, put the SLGA-derived field
    capacity 0.09 to 0.10 m3/m3 below the drained upper limit measured at
    205 surveyed APSoil profiles in south-eastern Australia, at every depth
    and in every texture class, and the wilting point 0.05 below the
    measured lower limit (2026-11-07; data under the lab's calibration
    outputs). The defaults here reproduce those measurements: field
    capacity at -10 J/kg, the drained upper limit as Australian practice
    takes it, and the wilting point at -500 J/kg, which corrects the
    texture-estimated curve's too-steep dry end rather than the physics
    of wilting. Plant-available water in the top 0.3 m then comes within
    1 mm of APSoil's mean of 54, where the book's convention gives 42.

    Attributes
    ----------
    field_capacity_suction : float, J kg-1
        The matric potential read as field capacity. Negative.
    wilting_point_suction : float, J kg-1
        The matric potential read as wilting point. More negative than
        the field capacity's.
    """

    field_capacity_suction: float = -10.0
    wilting_point_suction: float = -500.0

    def __post_init__(self):
        if not self.field_capacity_suction < 0:
            raise ValueError(f"field_capacity_suction must be negative, got {self.field_capacity_suction}")
        if not self.wilting_point_suction < self.field_capacity_suction:
            raise ValueError(f"wilting_point_suction {self.wilting_point_suction} must be more negative than field capacity {self.field_capacity_suction}")


def t():
    """The calibrated defaults, the book's values on request, the ordering enforced, and the object frozen."""
    c = SoilConventions()
    assert (c.field_capacity_suction, c.wilting_point_suction) == (-10.0, -500.0)
    book = SoilConventions(-33.0, -1500.0)
    assert book.wilting_point_suction == -1500.0 and book != c
    for bad in (dict(field_capacity_suction=0.0), dict(field_capacity_suction=-1500.0, wilting_point_suction=-33.0), dict(wilting_point_suction=-10.0)):
        try:
            SoilConventions(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
    try:
        c.field_capacity_suction = -33.0  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("expected the conventions to be frozen")
