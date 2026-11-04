import numpy as np

from terrasim2.k.van_genuchten_params import VanGenuchtenParams


def compute_van_genuchten_water_content(psi: np.ndarray | float, params: VanGenuchtenParams) -> np.ndarray:
    """Volumetric water content at a matric potential, by van Genuchten's curve.

    Eq. 5.29 of Bittelli, Campbell and Tomei (2015) with ``m = 1 - 1/n``::

        S_e   = [1 + (alpha * |psi|) ** n] ** (-m)
        theta = theta_r + (theta_s - theta_r) * S_e

    Parameters
    ----------
    psi : ndarray or float, J kg-1
        Matric potential, zero at saturation and negative when drier.
        Any shape.
    params : VanGenuchtenParams
        The soil's curve.

    Returns
    -------
    ndarray, m3 m-3
        Water content, same shape as ``psi``. Between ``params.theta_r``
        and ``params.theta_s``; the curve is smooth and never quite reaches
        either end.
    """
    psi = np.asarray(psi, dtype=np.float64)
    # Any potential at or above zero is saturated, including positive
    # pressures below a water table. Taking |psi| alone would make a positive
    # pressure look like suction, so the suction is clipped at zero first.
    suction = np.maximum(-psi, 0.0)
    effective = (1.0 + (params.alpha * suction) ** params.n) ** (-params.m)
    return params.theta_r + (params.theta_s - params.theta_r) * effective


def t1():
    """At zero and positive potential the soil is saturated."""
    p = VanGenuchtenParams(theta_s=0.4, theta_r=0.05, alpha=0.5, n=1.5)
    out = compute_van_genuchten_water_content(np.array([0.0, 3.0, 100.0]), p)
    assert np.allclose(out, 0.4)
    assert compute_van_genuchten_water_content(0.0, p).shape == ()


def t2():
    """Hand-computed points with alpha 1 and n 2, so m is 1/2 and the curve is 1 / sqrt(1 + psi^2)."""
    p = VanGenuchtenParams(theta_s=0.4, theta_r=0.0, alpha=1.0, n=2.0)
    assert np.isclose(compute_van_genuchten_water_content(-1.0, p), 0.4 / np.sqrt(2.0))
    assert np.isclose(compute_van_genuchten_water_content(-np.sqrt(3.0), p), 0.2)
    q = VanGenuchtenParams(theta_s=0.5, theta_r=0.1, alpha=1.0, n=2.0)
    assert np.isclose(compute_van_genuchten_water_content(-np.sqrt(3.0), q), 0.1 + 0.4 * 0.5)


def t3():
    """Content falls strictly as the soil dries, stays within (theta_r, theta_s], and tends to theta_r:
    with this n the approach is slow, so at -1e8 J/kg the excess is still a few tenths of a percent of the range."""
    p = VanGenuchtenParams(theta_s=0.46, theta_r=0.01, alpha=0.15, n=1.35)
    psi = -np.logspace(-2, 8, 300)
    theta = compute_van_genuchten_water_content(psi, p)
    assert np.all(np.diff(theta) < 0)
    assert theta.max() <= p.theta_s and theta.min() > p.theta_r
    assert theta[-1] - p.theta_r < 0.01 * (p.theta_s - p.theta_r)
    assert theta.shape == psi.shape


def t4():
    """Exercise 5.6 of the book (alpha 0.15, n 1.35, theta_r 0.01, theta_s 0.46): our own evaluation at
    field capacity -33 J/kg and wilting point -1500 J/kg. The book prints no answer; these are ours."""
    p = VanGenuchtenParams(theta_s=0.46, theta_r=0.01, alpha=0.15, n=1.35)
    fc = float(compute_van_genuchten_water_content(-33.0, p))
    pwp = float(compute_van_genuchten_water_content(-1500.0, p))
    assert abs(fc - 0.2599) < 5e-4 and abs(pwp - 0.0776) < 5e-4
    assert abs((fc - pwp) - 0.1823) < 5e-4


def t5():
    """Field capacity at -33 J/kg orders the coarse textures as with Campbell's table: sand holds least."""
    from terrasim2.f.lookup_van_genuchten_params import lookup_van_genuchten_params
    from terrasim2.k.soil_texture import SoilTexture

    fc = {tex: float(compute_van_genuchten_water_content(-33.0, lookup_van_genuchten_params(tex))) for tex in SoilTexture}
    assert fc[SoilTexture.SAND] < fc[SoilTexture.LOAMY_SAND] < fc[SoilTexture.SANDY_LOAM]
    finer = [v for k, v in fc.items() if k not in (SoilTexture.SAND, SoilTexture.LOAMY_SAND, SoilTexture.SANDY_LOAM)]
    assert fc[SoilTexture.SANDY_LOAM] < min(finer)


def t():
    t1()
    t2()
    t3()
    t4()
    t5()
