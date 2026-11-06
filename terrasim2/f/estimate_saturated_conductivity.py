import numpy as np


def estimate_saturated_conductivity(theta_s: np.ndarray | float, psi_e: np.ndarray | float, b: np.ndarray | float) -> np.ndarray:
    """Saturated hydraulic conductivity from Campbell's curve, by the book's regression.

    Eq. 6.34 of Bittelli, Campbell and Tomei (2015), after Rawls et al.
    (1992): the largest pores, those that drain between saturation and
    -33 J/kg, carry the flow::

        K_s = 0.07 * [theta_s * (1 - (psi_e / -33) ** (1 / b))] ** 4

    The book fits this to table 6.1 with about half the error of the
    air-entry regression, eq. 6.32.

    Parameters
    ----------
    theta_s : ndarray or float, m3 m-3
        Saturated water content, in (0, 1].
    psi_e : ndarray or float, J kg-1
        Air-entry potential, negative and wetter than -33.
    b : ndarray or float, dimensionless
        Campbell's shape parameter, positive.

    Returns
    -------
    ndarray, kg s m-3
        Same shape as the inputs broadcast. Multiply by 1000 for g s m-3,
        the unit table 6.1 prints.
    """
    theta_s, psi_e, b = (np.asarray(v, dtype=np.float64) for v in (theta_s, psi_e, b))
    if np.any(psi_e >= 0) or np.any(psi_e <= -33):
        raise ValueError("psi_e must be negative and wetter than -33 J/kg")
    if np.any(b <= 0) or np.any((theta_s <= 0) | (theta_s > 1)):
        raise ValueError("b must be positive and theta_s within (0, 1]")
    return 0.07 * (theta_s * (1.0 - (psi_e / -33.0) ** (1.0 / b))) ** 4


def t1():
    """Reproduces table 6.1's eq. 6.34 column within 5 percent; the book computed it with theta_s 0.5 for
    every class and, from the residuals, unrounded air entries, so exact agreement is not expected."""
    cases = {"sand": (-0.7, 1.7, 2.814), "loamy sand": (-0.9, 2.1, 1.994), "loam": (-1.1, 4.5, 0.333), "silt loam": (-2.1, 4.7, 0.167), "clay loam": (-2.6, 5.2, 0.101), "clay": (-3.7, 7.6, 0.017)}
    for name, (psi_e, b, expected) in cases.items():
        got = 1000 * float(estimate_saturated_conductivity(0.5, psi_e, b))
        assert abs(got / expected - 1) < 0.05, (name, got, expected)
    assert abs(1000 * float(estimate_saturated_conductivity(0.5, -0.7, 1.7)) - 2.824) < 0.001, "the hand-computed sand value"


def t2():
    """Coarser soils conduct more, denser soils less, and arrays come back per cell."""
    out = estimate_saturated_conductivity(np.array([0.5, 0.5, 0.4]), np.array([-0.7, -3.7, -0.7]), np.array([1.7, 7.6, 1.7]))
    assert out.shape == (3,) and out[0] > 100 * out[1] and out[2] < out[0]


def t3():
    """An air entry at or beyond -33, or beyond zero, is refused."""
    for bad in (-33.0, -40.0, 0.0, 1.0):
        try:
            estimate_saturated_conductivity(0.5, bad, 3.0)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for psi_e {bad}")


def t():
    t1()
    t2()
    t3()
