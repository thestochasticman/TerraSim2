from terrasim2.k.campbell_params import CampbellParams
from terrasim2.k.soil_texture import SoilTexture

# Table 5.3 of Bittelli, Campbell and Tomei (2015), after Rawls et al. (1992):
# (b, psi_e, theta_s) per textural class.
_TABLE_5_3: dict[SoilTexture, tuple[float, float, float]] = {
    SoilTexture.SAND: (1.69, -0.73, 0.37),
    SoilTexture.LOAMY_SAND: (2.11, -0.87, 0.38),
    SoilTexture.SANDY_LOAM: (3.11, -1.47, 0.41),
    SoilTexture.SILT_LOAM: (4.74, -2.08, 0.43),
    SoilTexture.LOAM: (4.55, -1.12, 0.43),
    SoilTexture.SILT: (4.23, -2.6, 0.44),
    SoilTexture.SANDY_CLAY_LOAM: (4.00, -2.81, 0.41),
    SoilTexture.SILTY_CLAY_LOAM: (6.62, -3.26, 0.46),
    SoilTexture.CLAY_LOAM: (5.15, -2.59, 0.45),
    SoilTexture.SANDY_CLAY: (5.95, -2.92, 0.44),
    SoilTexture.SILTY_CLAY: (7.87, -3.42, 0.51),
    SoilTexture.CLAY: (7.63, -3.73, 0.50),
}


def lookup_campbell_params(texture: SoilTexture | str) -> CampbellParams:
    """Campbell curve parameters for a textural class, from table 5.3.

    The values are class averages over about 5000 samples (Rawls et al.,
    1992). Variation within a class is large; use them when nothing better
    is known about the soil.

    Parameters
    ----------
    texture : SoilTexture or str
        One of the twelve classes, or its table spelling such as "silt loam".

    Returns
    -------
    CampbellParams
        theta_s in m3 m-3, psi_e in J kg-1, b dimensionless.
    """
    b, psi_e, theta_s = _TABLE_5_3[SoilTexture(texture)]
    return CampbellParams(theta_s=theta_s, psi_e=psi_e, b=b)


def t1():
    """Spot checks against the printed table, by member and by name."""
    sand = lookup_campbell_params(SoilTexture.SAND)
    assert (sand.b, sand.psi_e, sand.theta_s) == (1.69, -0.73, 0.37)
    clay = lookup_campbell_params("clay")
    assert (clay.b, clay.psi_e, clay.theta_s) == (7.63, -3.73, 0.50)
    loam = lookup_campbell_params("loam")
    assert (loam.b, loam.psi_e, loam.theta_s) == (4.55, -1.12, 0.43)


def t2():
    """Every class has an entry that passes CampbellParams' checks, and no two are identical."""
    params = [lookup_campbell_params(tex) for tex in SoilTexture]
    assert len(params) == 12 and len(set(params)) == 12


def t3():
    """The coarse-to-fine pattern the book describes: sand has the smallest b and the least negative
    air entry; the clays have the largest b and the most negative air entry."""
    sand, clay = lookup_campbell_params("sand"), lookup_campbell_params("clay")
    bs = [lookup_campbell_params(tex).b for tex in SoilTexture]
    psis = [lookup_campbell_params(tex).psi_e for tex in SoilTexture]
    assert sand.b == min(bs) and sand.psi_e == max(psis)
    assert clay.b > 7 and clay.psi_e == min(psis)
    assert sand.theta_s < clay.theta_s


def t4():
    """An unknown texture is refused."""
    try:
        lookup_campbell_params("peat")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for an unknown texture")


def t():
    t1()
    t2()
    t3()
    t4()
