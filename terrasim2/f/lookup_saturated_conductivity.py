from terrasim2.k.soil_texture import SoilTexture

# Table 6.1 of Bittelli, Campbell and Tomei (2015), the Rawls et al. (1992)
# column, in g s m-3. The table has no row for silt; its value here is eq.
# 6.34 evaluated with table 5.3's silt parameters and theta_s 0.5, the
# way the book computed its own eq. 6.34 column.
_TABLE_6_1: dict[SoilTexture, float] = {
    SoilTexture.SAND: 5.800,
    SoilTexture.LOAMY_SAND: 1.700,
    SoilTexture.SANDY_LOAM: 0.720,
    SoilTexture.SILT_LOAM: 0.190,
    SoilTexture.LOAM: 0.370,
    SoilTexture.SILT: 0.182,
    SoilTexture.SANDY_CLAY_LOAM: 0.120,
    SoilTexture.SILTY_CLAY_LOAM: 0.042,
    SoilTexture.CLAY_LOAM: 0.064,
    SoilTexture.SANDY_CLAY: 0.033,
    SoilTexture.SILTY_CLAY: 0.025,
    SoilTexture.CLAY: 0.017,
}


def lookup_saturated_conductivity(texture: SoilTexture | str) -> float:
    """Typical saturated hydraulic conductivity of a textural class, from table 6.1.

    Parameters
    ----------
    texture : SoilTexture or str
        One of the twelve classes, or its table spelling.

    Returns
    -------
    float, kg s m-3
        The table's g s m-3 value divided by 1000. Variation within a
        class is large; the book warns against leaning on these.
    """
    return _TABLE_6_1[SoilTexture(texture)] / 1000.0


def t1():
    """Spot checks against the printed table, in kg s m-3, and the sand to clay ratio of about 340."""
    assert lookup_saturated_conductivity("sand") == 0.0058
    assert lookup_saturated_conductivity(SoilTexture.CLAY) == 0.000017
    assert abs(lookup_saturated_conductivity("sand") / lookup_saturated_conductivity("clay") - 341) < 1


def t2():
    """Every class has a positive entry, and the silt fill-in matches eq. 6.34 with table 5.3's silt."""
    from terrasim2.f.estimate_saturated_conductivity import estimate_saturated_conductivity

    assert all(lookup_saturated_conductivity(tex) > 0 for tex in SoilTexture)
    assert abs(1000 * lookup_saturated_conductivity("silt") - 1000 * float(estimate_saturated_conductivity(0.5, -2.6, 4.23))) < 0.001


def t():
    t1()
    t2()
