from collections.abc import Callable

import numpy as np


def compute_available_fraction(
    compute_water_content: Callable[[np.ndarray | float, object], np.ndarray],
    params: object,
    psi_fc: float = -33.0,
    psi_pwp: float = -1500.0,
) -> np.ndarray:
    """Plant-available water as a fraction of soil volume.

    Water content at field capacity minus water content at permanent
    wilting point, each read off the soil's retention curve. Multiply by
    a depth of soil to get a depth of water.

    Parameters
    ----------
    compute_water_content : callable
        A retention curve, ``(psi, params) -> theta``.
    params : object
        The parameters that curve takes; may hold arrays, one curve per cell.
    psi_fc : float, J kg-1
        Matric potential taken as field capacity. Default -33.
    psi_pwp : float, J kg-1
        Matric potential taken as permanent wilting point. Default -1500.
        Must be drier (more negative) than psi_fc.

    Returns
    -------
    ndarray, m3 m-3
        Same shape as the parameters broadcast to; a 0-d array for scalars.
    """
    if not psi_pwp < psi_fc:
        raise ValueError(f"wilting point {psi_pwp} must be more negative than field capacity {psi_fc}")
    return np.asarray(compute_water_content(psi_fc, params) - compute_water_content(psi_pwp, params))


def t1():
    """Exercise 5.6's soil: 0.1823 between field capacity and wilting point."""
    from terrasim2.f.compute_van_genuchten_water_content import compute_van_genuchten_water_content
    from terrasim2.k.van_genuchten_params import VanGenuchtenParams

    p = VanGenuchtenParams(theta_s=0.46, theta_r=0.01, alpha=0.15, n=1.35)
    out = compute_available_fraction(compute_van_genuchten_water_content, p)
    assert out.shape == () and abs(float(out) - 0.1823) < 5e-4


def t2():
    """Array-valued Campbell parameters give one fraction per cell, and a hand case checks out."""
    from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
    from terrasim2.k.campbell_params import CampbellParams

    p = CampbellParams(theta_s=np.array([0.4, 0.5]), psi_e=np.array([-1.0, -1.0]), b=np.array([1.0, 1.0]))
    out = compute_available_fraction(compute_campbell_water_content, p)
    assert out.shape == (2,)
    assert np.allclose(out, [0.4 / 33 - 0.4 / 1500, 0.5 / 33 - 0.5 / 1500])


def t3():
    """A wilting point wetter than field capacity is refused."""
    from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
    from terrasim2.k.campbell_params import CampbellParams

    try:
        compute_available_fraction(compute_campbell_water_content, CampbellParams(0.4, -1.0, 2.0), psi_fc=-1500.0, psi_pwp=-33.0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
    t3()
