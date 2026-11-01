import numpy as np


def compute_layer_thickness_in_depth(layer_bounds: np.ndarray, depth: np.ndarray | float) -> np.ndarray:
    """How much of each soil layer lies above a depth.

    Parameters
    ----------
    layer_bounds : ndarray, m
        Shape (L + 1,), ascending from 0: layer i spans
        ``layer_bounds[i]`` to ``layer_bounds[i + 1]``.
    depth : ndarray or float, m
        The depth of interest, non-negative; a scalar or a field of shape
        ``(rows, cols)``.

    Returns
    -------
    ndarray, m
        Shape ``(L,)`` for a scalar depth, ``(L, rows, cols)`` for a field.
        Layers wholly above the depth give their full thickness, the layer
        straddling it the part above, deeper layers zero. A depth below the
        last bound counts only the layers that exist.
    """
    bounds = np.asarray(layer_bounds, dtype=np.float64)
    if bounds.ndim != 1 or bounds.size < 2 or bounds[0] != 0 or np.any(np.diff(bounds) <= 0):
        raise ValueError("layer_bounds must be one ascending vector starting at 0")
    depth = np.asarray(depth, dtype=np.float64)
    if np.any(depth < 0):
        raise ValueError("depth must be non-negative")
    shape = (bounds.size - 1,) + depth.shape
    top = np.broadcast_to(bounds[:-1].reshape((-1,) + (1,) * depth.ndim), shape)
    bottom = np.broadcast_to(bounds[1:].reshape((-1,) + (1,) * depth.ndim), shape)
    return np.minimum(bottom, depth) - np.minimum(top, depth)


BOUNDS = np.array([0.0, 0.05, 0.15, 0.30, 0.60, 1.0, 2.0])


def t1():
    """A depth inside a layer takes whole layers above it, the part of its own, nothing below."""
    out = compute_layer_thickness_in_depth(BOUNDS, 0.4)
    assert out.shape == (6,)
    assert np.allclose(out, [0.05, 0.10, 0.15, 0.10, 0.0, 0.0])
    assert np.allclose(compute_layer_thickness_in_depth(BOUNDS, 0.0), 0.0)


def t2():
    """A depth on a bound, beyond the last bound, and a field of depths."""
    assert np.allclose(compute_layer_thickness_in_depth(BOUNDS, 0.15), [0.05, 0.10, 0.0, 0.0, 0.0, 0.0])
    assert np.allclose(compute_layer_thickness_in_depth(BOUNDS, 5.0), np.diff(BOUNDS))
    field = np.array([[0.4, 2.0], [0.05, 0.0]])
    out = compute_layer_thickness_in_depth(BOUNDS, field)
    assert out.shape == (6, 2, 2)
    assert np.allclose(out[:, 0, 0], [0.05, 0.10, 0.15, 0.10, 0.0, 0.0])
    assert np.allclose(out[:, 0, 1], np.diff(BOUNDS))
    assert np.allclose(out[:, 1, 0], [0.05, 0, 0, 0, 0, 0]) and np.allclose(out[:, 1, 1], 0.0)
    assert np.allclose(out.sum(axis=0), np.minimum(field, 2.0))


def t3():
    """Bounds that do not start at 0 or do not ascend, and negative depths, are refused."""
    for bad_bounds in ([0.1, 0.2], [0.0, 0.3, 0.2], [0.0]):
        try:
            compute_layer_thickness_in_depth(np.array(bad_bounds), 0.5)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for bounds {bad_bounds}")
    try:
        compute_layer_thickness_in_depth(BOUNDS, -0.1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for a negative depth")


def t():
    t1()
    t2()
    t3()
