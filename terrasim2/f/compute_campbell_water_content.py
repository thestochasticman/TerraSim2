import numpy as np

from terrasim2.k.campbell_params import CampbellParams


def compute_campbell_water_content(psi: np.ndarray | float, params: CampbellParams) -> np.ndarray:
    """Volumetric water content at a matric potential, by Campbell's curve.

    Eq. 5.27 of Bittelli, Campbell and Tomei (2015)::

        theta = theta_s                          if psi >= psi_e
        theta = theta_s * (psi / psi_e) ** (-1/b) if psi <  psi_e

    Potentials at or above air entry, including zero and positive pressure
    below a water table, give the saturated content.

    Parameters
    ----------
    psi : ndarray or float, J kg-1
        Matric potential, zero at saturation and negative when drier.
        Any shape.
    params : CampbellParams
        The soil's curve.

    Returns
    -------
    ndarray, m3 m-3
        Water content, same shape as ``psi``. Always between 0 and
        ``params.theta_s``.
    """
    psi = np.asarray(psi, dtype=np.float64)
    # Any potential at or above air entry is saturated, including positive
    # pressures below a water table. This matches the book's own code and
    # keeps the column integral simple.
    ratio = np.maximum(psi / params.psi_e, 1.0)
    return params.theta_s * ratio ** (-1.0 / params.b)


def t1():
    """At and above air entry the soil is saturated."""
    p = CampbellParams(theta_s=0.4, psi_e=-2.0, b=3.0)
    out = compute_campbell_water_content(np.array([-2.0, -1.0, 0.0, 5.0]), p)
    assert np.allclose(out, 0.4)
    assert compute_campbell_water_content(-2.0, p).shape == ()


def t2():
    """Hand-computed points below air entry: with b = 1 content falls as 1/ratio, with b = 2 as 1/sqrt."""
    assert np.isclose(compute_campbell_water_content(-4.0, CampbellParams(0.4, -1.0, 1.0)), 0.1)
    assert np.isclose(compute_campbell_water_content(-4.0, CampbellParams(0.4, -1.0, 2.0)), 0.2)
    assert np.isclose(compute_campbell_water_content(-100.0, CampbellParams(0.5, -1.0, 2.0)), 0.05)


def t3():
    """Content never rises as the soil dries, strictly falls below air entry, and stays within [0, theta_s]."""
    p = CampbellParams(theta_s=0.46, psi_e=-4.2, b=3.58)
    psi = -np.logspace(-2, 6, 200)
    theta = compute_campbell_water_content(psi, p)
    assert np.all(np.diff(theta) <= 0)
    below = psi < p.psi_e
    assert np.all(np.diff(theta[below]) < 0)
    assert theta.max() <= p.theta_s and theta.min() > 0
    assert theta.shape == psi.shape


def t4():
    """Reproduces the book's column example (section 5.3.4): a 2 m profile in hydrostatic equilibrium
    with theta_s 0.46, air entry -4.2 J/kg and b 3.58 holds about 0.75 m3 of water per m2."""
    p = CampbellParams(theta_s=0.46, psi_e=-4.2, b=3.58)
    z = np.linspace(0.0, 2.0, 20001)
    theta = compute_campbell_water_content(-9.81 * z, p)
    assert abs(np.trapezoid(theta, z) - 0.75) < 0.01


def t5():
    """Field capacity at -33 J/kg orders the coarse textures as expected: sand holds least."""
    from terrasim2.f.lookup_campbell_params import lookup_campbell_params
    from terrasim2.k.soil_texture import SoilTexture

    fc = {tex: float(compute_campbell_water_content(-33.0, lookup_campbell_params(tex))) for tex in SoilTexture}
    assert fc[SoilTexture.SAND] < fc[SoilTexture.LOAMY_SAND] < fc[SoilTexture.SANDY_LOAM]
    finer = [v for k, v in fc.items() if k not in (SoilTexture.SAND, SoilTexture.LOAMY_SAND, SoilTexture.SANDY_LOAM)]
    assert fc[SoilTexture.SANDY_LOAM] < min(finer)


def t():
    t1()
    t2()
    t3()
    t4()
    t5()
