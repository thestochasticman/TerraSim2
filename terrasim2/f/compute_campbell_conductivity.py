import numpy as np


def compute_campbell_conductivity(theta: np.ndarray | float, theta_s: np.ndarray | float, b: np.ndarray | float, k_sat: np.ndarray | float) -> np.ndarray:
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
    theta_s : ndarray or float, m3 m-3
        Saturated water content, positive; floats or arrays per cell.
    b : ndarray or float, dimensionless
        Campbell's shape parameter, positive.
    k_sat : ndarray or float, kg s m-3
        Saturated conductivity, from ``estimate_saturated_conductivity``
        or a table.

    Returns
    -------
    ndarray, kg s m-3
        Between 0 and ``k_sat``.
    """
    theta, theta_s, b = (np.asarray(v, dtype=np.float64) for v in (theta, theta_s, b))
    if np.any(theta < 0):
        raise ValueError("theta must be non-negative")
    if np.any(theta_s <= 0) or np.any(b <= 0):
        raise ValueError("theta_s and b must be positive")
    saturation = np.minimum(theta / theta_s, 1.0)
    return np.asarray(k_sat, dtype=np.float64) * saturation ** (2.0 * b + 3.0)


def t1():
    """Saturated gives K_s, and the hand-computed drops: 0.8 ** 9 and 0.5 ** 9 with b of 3."""
    assert compute_campbell_conductivity(0.4, 0.4, 3.0, 2.0) == 2.0
    assert compute_campbell_conductivity(0.6, 0.4, 3.0, 2.0) == 2.0
    assert abs(float(compute_campbell_conductivity(0.32, 0.4, 3.0, 2.0)) - 2.0 * 0.8**9) < 1e-12
    assert abs(float(compute_campbell_conductivity(0.2, 0.4, 3.0, 2.0)) - 2.0 * 0.5**9) < 1e-12
    assert compute_campbell_conductivity(0.0, 0.4, 3.0, 2.0) == 0.0


def t2():
    """Arrays per cell, monotone in water content, and bad inputs are refused."""
    out = compute_campbell_conductivity(np.array([0.2, 0.25]), np.array([0.4, 0.5]), np.array([2.0, 7.0]), np.array([1.0, 0.1]))
    assert out.shape == (2,) and out[0] == 0.5**7 and abs(out[1] - 0.1 * 0.5**17) < 1e-15
    k = compute_campbell_conductivity(np.linspace(0, 0.4, 50), 0.4, 3.0, 1.0)
    assert np.all(np.diff(k) >= 0)
    for bad in (dict(theta=-0.1, theta_s=0.4, b=3.0, k_sat=1.0), dict(theta=0.1, theta_s=0.0, b=3.0, k_sat=1.0)):
        try:
            compute_campbell_conductivity(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
