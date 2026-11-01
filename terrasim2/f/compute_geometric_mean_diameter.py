import numpy as np

# Natural logarithms of the geometric mean diameters of the clay, silt and
# sand fractions, in micrometres: sqrt(0.01 * 2), sqrt(2 * 50) and
# sqrt(50 * 2000). Eqs. 2.33 to 2.36 of Bittelli, Campbell and Tomei (2015).
LN_CLAY = -1.96
LN_SILT = 2.3
LN_SAND = 5.76


def compute_geometric_mean_diameter(sand: np.ndarray | float, silt: np.ndarray | float, clay: np.ndarray | float) -> np.ndarray:
    """Geometric mean particle diameter of a soil from its three fractions.

    Eq. 2.36 of Bittelli, Campbell and Tomei (2015), after Shiozawa and
    Campbell (1991): each fraction's share of the log diameter, summed.

    Parameters
    ----------
    sand, silt, clay : ndarray or float, dimensionless
        Mass fractions in [0, 1], any common shape, summing to one.

    Returns
    -------
    ndarray, micrometres
        Same shape as the inputs.
    """
    sand, silt, clay = (np.asarray(v, dtype=np.float64) for v in (sand, silt, clay))
    for name, v in (("sand", sand), ("silt", silt), ("clay", clay)):
        if np.any((v < 0) | (v > 1)):
            raise ValueError(f"{name} fraction must be within [0, 1]")
    if np.any(np.abs(sand + silt + clay - 1) > 0.02):
        raise ValueError("fractions must sum to one")
    return np.exp(clay * LN_CLAY + silt * LN_SILT + sand * LN_SAND)


def t1():
    """Reproduces table 2.4: sand 211.75, loam 19.81 and clay 1.55 micrometres from their typical fractions."""
    assert abs(compute_geometric_mean_diameter(0.92, 0.05, 0.03) - 211.75) < 0.05
    assert abs(compute_geometric_mean_diameter(0.42, 0.40, 0.18) - 19.81) < 0.05
    assert abs(compute_geometric_mean_diameter(0.20, 0.20, 0.60) - 1.55) < 0.01


def t2():
    """Pure fractions give the class means of eqs. 2.33 to 2.35 (pure sand lands at 317 rather than 316.2
    because the book rounds ln 316.2 to 5.76), and arrays keep their shape."""
    out = compute_geometric_mean_diameter(np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0]))
    assert out.shape == (3,)
    assert abs(out[0] - 316.2) < 1.5 and abs(out[1] - 10) < 0.05 and abs(out[2] - 0.14) < 0.005


def t3():
    """Exercise 2.5, our own evaluation: silt loam with silt 60, sand 20, clay 20 percent has a mean near 8.5 micrometres."""
    assert abs(compute_geometric_mean_diameter(0.20, 0.60, 0.20) - 8.50) < 0.01


def t4():
    """Fractions outside [0, 1] or not summing to one are refused."""
    for bad in ((1.2, 0.0, 0.0), (0.5, 0.3, 0.3)):
        try:
            compute_geometric_mean_diameter(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def t():
    t1()
    t2()
    t3()
    t4()
