import numpy as np

from terrasim2.k.campbell_params import CampbellParams


def compute_campbell_conductivity(theta: np.ndarray | float, params: CampbellParams, k_sat: np.ndarray | float) -> np.ndarray:
    """Unsaturated hydraulic conductivity at a water content, by Campbell's curve.

    Eq. 6.35 of Bittelli, Campbell and Tomei (2015), written in water
    content through eq. 6.30::

        K = K_s * (theta / theta_s) ** (2 b + 3)

    and K_s at or above saturation. The exponent is large, so conductivity
    collapses as the soil dries: at 80 percent of saturation with b of 3 it
    is 13 percent of K_s, at half saturation under 0.2 percent.

    Parameters
    ----------
    theta : ndarray or float, m3 m-3
        Water content, non-negative. Any shape.
    params : CampbellParams
        Uses ``theta_s`` and ``b``; floats or arrays per cell.
    k_sat : ndarray or float, kg s m-3
        Saturated conductivity, from ``estimate_saturated_conductivity``
        or a table.

    Returns
    -------
    ndarray, kg s m-3
        Between 0 and ``k_sat``.
    """
    theta = np.asarray(theta, dtype=np.float64)
    if np.any(theta < 0):
        raise ValueError("theta must be non-negative")
    saturation = np.minimum(theta / params.theta_s, 1.0)
    return np.asarray(k_sat) * saturation ** (2.0 * params.b + 3.0)


def t1():
    """Saturated gives K_s, and the hand-computed drops: 0.8 ** 9 and 0.5 ** 9 with b of 3."""
    p = CampbellParams(theta_s=0.4, psi_e=-1.0, b=3.0)
    assert compute_campbell_conductivity(0.4, p, 2.0) == 2.0
    assert compute_campbell_conductivity(0.6, p, 2.0) == 2.0
    assert abs(float(compute_campbell_conductivity(0.32, p, 2.0)) - 2.0 * 0.8**9) < 1e-12
    assert abs(float(compute_campbell_conductivity(0.2, p, 2.0)) - 2.0 * 0.5**9) < 1e-12
    assert compute_campbell_conductivity(0.0, p, 2.0) == 0.0


def t2():
    """Arrays per cell, monotone in water content, and a negative content is refused."""
    p = CampbellParams(theta_s=np.array([0.4, 0.5]), psi_e=np.array([-1.0, -3.0]), b=np.array([2.0, 7.0]))
    out = compute_campbell_conductivity(np.array([0.2, 0.25]), p, np.array([1.0, 0.1]))
    assert out.shape == (2,) and out[0] == 0.5**7 and abs(out[1] - 0.1 * 0.5**17) < 1e-15
    theta = np.linspace(0, 0.4, 50)
    k = compute_campbell_conductivity(theta, CampbellParams(0.4, -1.0, 3.0), 1.0)
    assert np.all(np.diff(k) >= 0)
    try:
        compute_campbell_conductivity(-0.1, CampbellParams(0.4, -1.0, 3.0), 1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
