from terrasim2.k.soil_texture import SoilTexture
from terrasim2.k.van_genuchten_params import VanGenuchtenParams

# Table 5.4 of Bittelli, Campbell and Tomei (2015): (alpha, n, psi_e, theta_r, theta_s)
# per textural class. psi_e belongs to the Ippisch variant of the curve and is
# kept as printed; the plain restricted curve does not use it.
_TABLE_5_4: dict[SoilTexture, tuple[float, float, float, float, float]] = {
    SoilTexture.SAND: (0.68, 1.7, -0.7, 0.02, 0.38),
    SoilTexture.LOAMY_SAND: (0.49, 1.5, -1.1, 0.03, 0.39),
    SoilTexture.SANDY_LOAM: (0.39, 1.4, -1.5, 0.05, 0.4),
    SoilTexture.SILT_LOAM: (0.14, 1.2, -2.6, 0.05, 0.44),
    SoilTexture.LOAM: (0.18, 1.21, -2.3, 0.05, 0.42),
    SoilTexture.SILT: (0.08, 1.24, -2.7, 0.04, 0.44),
    SoilTexture.SANDY_CLAY_LOAM: (0.23, 1.22, -2.1, 0.05, 0.41),
    SoilTexture.SILTY_CLAY_LOAM: (0.14, 1.2, -3.1, 0.05, 0.46),
    SoilTexture.CLAY_LOAM: (0.19, 1.18, -2.7, 0.06, 0.45),
    SoilTexture.SANDY_CLAY: (0.22, 1.18, -2.5, 0.07, 0.44),
    SoilTexture.SILTY_CLAY: (0.18, 1.16, -3.3, 0.06, 0.5),
    SoilTexture.CLAY: (0.17, 1.16, -3.3, 0.07, 0.5),
}


def lookup_van_genuchten_params(texture: SoilTexture | str) -> VanGenuchtenParams:
    """Van Genuchten curve parameters for a textural class, from table 5.4.

    The book built the table from Rosetta (Schaap et al., 2001) and Rawls
    et al. (1992), tested on soils of Emilia-Romagna. Class averages; use
    them when nothing better is known about the soil.

    Parameters
    ----------
    texture : SoilTexture or str
        One of the twelve classes, or its table spelling such as "silt loam".

    Returns
    -------
    VanGenuchtenParams
        theta_s and theta_r in m3 m-3, alpha in kg J-1, n dimensionless.
    """
    alpha, n, _psi_e, theta_r, theta_s = _TABLE_5_4[SoilTexture(texture)]
    return VanGenuchtenParams(theta_s=theta_s, theta_r=theta_r, alpha=alpha, n=n)


def t1():
    """Spot checks against the printed table, by member and by name."""
    sand = lookup_van_genuchten_params(SoilTexture.SAND)
    assert (sand.alpha, sand.n, sand.theta_r, sand.theta_s) == (0.68, 1.7, 0.02, 0.38)
    clay = lookup_van_genuchten_params("clay")
    assert (clay.alpha, clay.n, clay.theta_r, clay.theta_s) == (0.17, 1.16, 0.07, 0.5)


def t2():
    """Every class has an entry that passes the parameter checks, and no two are identical."""
    params = [lookup_van_genuchten_params(tex) for tex in SoilTexture]
    assert len(params) == 12 and len(set(params)) == 12


def t3():
    """Coarse to fine: sand has the largest alpha and n (drains soonest and steepest), clay among the smallest."""
    alphas = {tex: lookup_van_genuchten_params(tex).alpha for tex in SoilTexture}
    ns = {tex: lookup_van_genuchten_params(tex).n for tex in SoilTexture}
    assert alphas[SoilTexture.SAND] == max(alphas.values()) and ns[SoilTexture.SAND] == max(ns.values())
    assert ns[SoilTexture.CLAY] == min(ns.values())
    assert lookup_van_genuchten_params("sand").theta_s < lookup_van_genuchten_params("clay").theta_s


def t4():
    """An unknown texture is refused."""
    try:
        lookup_van_genuchten_params("peat")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for an unknown texture")


def t():
    t1()
    t2()
    t3()
    t4()
