import numpy as np

from terrasim2.k.campbell_params import CampbellParams


def estimate_campbell_params(geometric_mean_diameter: np.ndarray | float, theta_s: np.ndarray | float) -> CampbellParams:
    """Campbell curve parameters from particle size, by the book's regressions.

    Eqs. 5.36 and 5.37 of Bittelli, Campbell and Tomei (2015), fitted to
    the Rawls et al. (1992) data::

        psi_e = 0.61 ln(d_g) - 3.9
        b     = 8.25 - 1.26 ln(d_g)

    with ``d_g`` in micrometres. Class averages in table 5.3 differ from
    these by up to about 1 J/kg in psi_e and 1 in b, so expect the same
    spread here. The saturated content is not a function of particle size
    and is passed in, typically the porosity ``1 - bulk_density / 2650``.

    Parameters
    ----------
    geometric_mean_diameter : ndarray or float, micrometres
        From ``compute_geometric_mean_diameter``. Positive; any shape.
    theta_s : ndarray or float, m3 m-3
        Saturated water content, in (0, 1]; broadcastable to the diameter.

    Returns
    -------
    CampbellParams
        With array-valued ``psi_e`` and ``b`` of the diameter's shape when
        the diameter is an array.
    """
    d_g = np.asarray(geometric_mean_diameter, dtype=np.float64)
    if np.any(d_g <= 0):
        raise ValueError("geometric mean diameter must be positive")
    ln_d = np.log(d_g)
    psi_e = 0.61 * ln_d - 3.9
    b = 8.25 - 1.26 * ln_d
    if np.any(b <= 0) or np.any(psi_e >= 0):
        raise ValueError("diameter outside the range where the regressions give a valid curve")
    return CampbellParams(theta_s=theta_s, psi_e=psi_e, b=b)


def t1():
    """The ends of the texture range land near table 5.3: sand from 211.75 um gives psi_e about -0.6 and b
    about 1.5 (table -0.73, 1.69); clay from 1.55 um gives about -3.6 and 7.7 (table -3.73, 7.63)."""
    sand = estimate_campbell_params(211.75, 0.37)
    assert abs(float(sand.psi_e) - (-0.63)) < 0.01 and abs(float(sand.b) - 1.50) < 0.01
    clay = estimate_campbell_params(1.55, 0.50)
    assert abs(float(clay.psi_e) - (-3.63)) < 0.01 and abs(float(clay.b) - 7.70) < 0.01
    assert abs(float(sand.psi_e) - (-0.73)) < 0.2 and abs(float(clay.b) - 7.63) < 0.2


def t2():
    """Finer soils get a more negative air entry and a larger b, and arrays come back per cell."""
    d_g = np.array([[300.0, 30.0], [3.0, 1.0]])
    p = estimate_campbell_params(d_g, 0.45)
    assert p.psi_e.shape == (2, 2) and p.b.shape == (2, 2)
    flat_psi, flat_b = p.psi_e.ravel(), p.b.ravel()
    assert np.all(np.diff(flat_psi) < 0) and np.all(np.diff(flat_b) > 0)
    assert p.theta_s == 0.45


def t3():
    """The curve built from the estimate evaluates per cell: with arrays of parameters and one potential."""
    from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content

    p = estimate_campbell_params(np.array([211.75, 1.55]), np.array([0.37, 0.50]))
    theta = compute_campbell_water_content(-33.0, p)
    assert theta.shape == (2,) and theta[0] < 0.1 < theta[1]


def t4():
    """Non-positive diameters, and diameters so coarse that b would turn negative, are refused."""
    for bad in (0.0, -1.0, 1e6):
        try:
            estimate_campbell_params(bad, 0.4)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def t():
    t1()
    t2()
    t3()
    t4()
