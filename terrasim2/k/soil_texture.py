from enum import StrEnum


class SoilTexture(StrEnum):
    """The twelve USDA soil textural classes, coarsest first.

    These are the rows of the parameter tables 5.3 and 5.4 in Bittelli,
    Campbell and Tomei, *Soil Physics with Python* (2015). The value of
    each member is its lower-case name with spaces, as the tables print it.
    """

    SAND = "sand"
    LOAMY_SAND = "loamy sand"
    SANDY_LOAM = "sandy loam"
    SILT_LOAM = "silt loam"
    LOAM = "loam"
    SILT = "silt"
    SANDY_CLAY_LOAM = "sandy clay loam"
    SILTY_CLAY_LOAM = "silty clay loam"
    CLAY_LOAM = "clay loam"
    SANDY_CLAY = "sandy clay"
    SILTY_CLAY = "silty clay"
    CLAY = "clay"


def t():
    """Twelve classes, usable as plain strings, and the table's spelling round-trips."""
    assert len(SoilTexture) == 12
    assert SoilTexture.SANDY_CLAY_LOAM == "sandy clay loam"
    assert SoilTexture("silt loam") is SoilTexture.SILT_LOAM
    assert list(SoilTexture)[0] is SoilTexture.SAND and list(SoilTexture)[-1] is SoilTexture.CLAY
    try:
        SoilTexture("peat")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for an unknown texture")
