import numpy as np

from terrasim2.f.compute_layer_thickness_in_depth import compute_layer_thickness_in_depth


def compute_capacity_map(available_fraction: np.ndarray, layer_bounds: np.ndarray, root_depth: np.ndarray | float) -> np.ndarray:
    """Plant-available water of a layered soil down to a root depth, per cell.

    Each layer's available fraction times the part of the layer the roots
    reach, summed over layers. Roots deeper than the last bound see only
    the soil that exists. A layer the roots do not reach contributes
    nothing, even where its fraction is NaN; a NaN within reach makes the
    cell NaN.

    Parameters
    ----------
    available_fraction : ndarray, m3 m-3
        Shape ``(L, rows, cols)``, or ``(L,)`` for one column: field
        capacity minus wilting point of each layer, from
        ``compute_available_fraction``. In [0, 1].
    layer_bounds : ndarray, m
        Shape ``(L + 1,)``, ascending from 0.
    root_depth : ndarray or float, m
        Positive; a scalar or a field of shape ``(rows, cols)``.

    Returns
    -------
    ndarray, mm
        Shape ``(rows, cols)``, or a 0-d array for a single column. NaN
        where a layer within reach has no data.
    """
    fraction = np.asarray(available_fraction, dtype=np.float64)
    bounds = np.asarray(layer_bounds, dtype=np.float64)
    if fraction.ndim not in (1, 3) or fraction.shape[0] != bounds.size - 1:
        raise ValueError(f"available_fraction must have one leading entry per layer ({bounds.size - 1}), got shape {fraction.shape}")
    if np.any(fraction < 0) or np.any(fraction > 1):
        raise ValueError("available_fraction must be within [0, 1]")
    root_depth = np.asarray(root_depth, dtype=np.float64)
    if np.any(root_depth <= 0):
        raise ValueError("root_depth must be positive")
    thickness = compute_layer_thickness_in_depth(bounds, root_depth)
    if fraction.ndim == 3 and thickness.ndim == 1:
        thickness = thickness.reshape(-1, 1, 1)
    contribution = np.where(thickness > 0, fraction * thickness, 0.0)
    return np.sum(contribution, axis=0) * 1000.0


BOUNDS = np.array([0.0, 0.05, 0.15, 0.30, 0.60, 1.0, 2.0])


def t1():
    """A uniform column is fraction times depth; sand over clay with shallow roots sees only the sand."""
    uniform = np.full(6, 0.15)
    assert np.isclose(compute_capacity_map(uniform, BOUNDS, 1.0), 150.0)
    assert np.isclose(compute_capacity_map(uniform, BOUNDS, 0.3), 45.0)
    sand_over_clay = np.array([0.035, 0.035, 0.035, 0.148, 0.148, 0.148])
    assert np.isclose(compute_capacity_map(sand_over_clay, BOUNDS, 0.3), 0.035 * 300)
    assert np.isclose(compute_capacity_map(sand_over_clay, BOUNDS, 0.6), 0.035 * 300 + 0.148 * 300)
    gappy = np.array([0.035, 0.035, 0.035, np.nan, 0.148, 0.148])
    assert np.isclose(compute_capacity_map(gappy, BOUNDS, 0.3), 0.035 * 300)
    assert np.isnan(compute_capacity_map(gappy, BOUNDS, 0.6))


def t2():
    """A grid of columns with one depth, and with a depth per cell; roots past the bottom are cut at 2 m."""
    fraction = np.zeros((6, 2, 2))
    fraction[:, 0, 0] = 0.035
    fraction[:, 0, 1] = 0.148
    fraction[:3, 1, 0] = 0.035
    fraction[3:, 1, 0] = 0.148
    fraction[:, 1, 1] = 0.10
    out = compute_capacity_map(fraction, BOUNDS, 1.0)
    assert out.shape == (2, 2)
    assert np.allclose(out, [[35.0, 148.0], [0.035 * 300 + 0.148 * 700, 100.0]])
    per_cell = compute_capacity_map(fraction, BOUNDS, np.array([[0.3, 0.3], [2.0, 5.0]]))
    assert np.allclose(per_cell, [[10.5, 44.4], [0.035 * 300 + 0.148 * 1700, 200.0]])


def t3():
    """Wrong layer counts, fractions outside [0, 1], and non-positive depths are refused."""
    for bad in (np.full(5, 0.1), np.full((6, 2, 2), 1.5), np.full((6, 2, 2), -0.1)):
        try:
            compute_capacity_map(bad, BOUNDS, 1.0)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for a bad fraction array")
    try:
        compute_capacity_map(np.full(6, 0.1), BOUNDS, 0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for zero depth")


def t():
    t1()
    t2()
    t3()
