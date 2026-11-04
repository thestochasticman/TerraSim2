from terrasim2.k.soil_texture import SoilTexture

# Table 2.4 of Bittelli, Campbell and Tomei (2015): typical (sand, silt, clay)
# mass fractions of each textural class, after Shiozawa and Campbell (1991).
_TABLE_2_4: dict[SoilTexture, tuple[float, float, float]] = {
    SoilTexture.SAND: (0.92, 0.05, 0.03),
    SoilTexture.LOAMY_SAND: (0.81, 0.12, 0.07),
    SoilTexture.SANDY_LOAM: (0.65, 0.25, 0.10),
    SoilTexture.SILT_LOAM: (0.20, 0.65, 0.15),
    SoilTexture.LOAM: (0.42, 0.40, 0.18),
    SoilTexture.SILT: (0.06, 0.87, 0.07),
    SoilTexture.SANDY_CLAY_LOAM: (0.60, 0.13, 0.27),
    SoilTexture.SILTY_CLAY_LOAM: (0.08, 0.58, 0.34),
    SoilTexture.CLAY_LOAM: (0.32, 0.34, 0.34),
    SoilTexture.SANDY_CLAY: (0.53, 0.07, 0.40),
    SoilTexture.SILTY_CLAY: (0.10, 0.45, 0.45),
    SoilTexture.CLAY: (0.20, 0.20, 0.60),
}


def lookup_typical_fractions(texture: SoilTexture | str) -> tuple[float, float, float]:
    """A typical sand, silt and clay composition of a textural class, from table 2.4.

    Parameters
    ----------
    texture : SoilTexture or str
        One of the twelve classes, or its table spelling.

    Returns
    -------
    tuple of float, dimensionless
        (sand, silt, clay) mass fractions, summing to one.
    """
    return _TABLE_2_4[SoilTexture(texture)]


def t1():
    """Spot checks against the printed table, and every row sums to one."""
    assert lookup_typical_fractions("sand") == (0.92, 0.05, 0.03)
    assert lookup_typical_fractions(SoilTexture.CLAY) == (0.20, 0.20, 0.60)
    for tex in SoilTexture:
        assert abs(sum(lookup_typical_fractions(tex)) - 1) < 1e-9, tex


def t2():
    """Each typical composition classifies as its own class."""
    from terrasim2.f.classify_soil_texture import classify_soil_texture

    for i, tex in enumerate(SoilTexture):
        assert int(classify_soil_texture(*lookup_typical_fractions(tex))) == i, tex


def t():
    t1()
    t2()
