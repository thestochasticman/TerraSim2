import numpy as np


def compute_slope_aspect(elevation: np.ndarray, cell_size: float) -> tuple[np.ndarray, np.ndarray]:
    """The tilt of the ground at each cell and the direction it faces.

    The gradient is taken by central differences over the neighbouring
    cells (one-sided at the edges), so this is the surface's own tilt,
    not the steepest-descent slope to one neighbour that routing uses.
    Rows run south, columns east.

    Parameters
    ----------
    elevation : ndarray, m
        Shape (rows, cols).
    cell_size : float, m
        Positive.

    Returns
    -------
    slope : ndarray, radians
        Shape (rows, cols), from 0 (flat) toward pi/2.
    aspect : ndarray, radians
        Shape (rows, cols): the downslope direction clockwise from north,
        0 facing north, pi/2 east, pi south, -pi/2 west. 0 where flat.
    """
    z = np.asarray(elevation, dtype=np.float64)
    if z.ndim != 2 or min(z.shape) < 2:
        raise ValueError(f"elevation must be a 2-D grid of at least 2 x 2, got {z.shape}")
    if not cell_size > 0:
        raise ValueError("cell_size must be positive")
    dz_east = np.gradient(z, cell_size, axis=1)
    dz_north = -np.gradient(z, cell_size, axis=0)
    slope = np.arctan(np.hypot(dz_east, dz_north))
    aspect = np.where(slope > 0, np.arctan2(-dz_east, -dz_north), 0.0)
    return slope, aspect


def t():
    """Planes tilting each way give their tilt and face downhill; flat ground is slope 0 facing north."""
    rows, cols = np.mgrid[0:5, 0:6]
    cell = 10.0
    north_down = 1.0 * rows * cell  # higher to the south, so the ground faces north
    slope, aspect = compute_slope_aspect(north_down, cell)
    assert slope.shape == (5, 6) and np.allclose(slope, np.arctan(1.0)) and np.allclose(aspect, 0.0)
    east_down = -0.5 * cols * cell
    slope, aspect = compute_slope_aspect(east_down, cell)
    assert np.allclose(slope, np.arctan(0.5)) and np.allclose(aspect, np.pi / 2)
    south_down = -0.2 * rows * cell
    _, aspect = compute_slope_aspect(south_down, cell)
    assert np.allclose(np.abs(aspect), np.pi)
    west_down = 0.3 * cols * cell
    _, aspect = compute_slope_aspect(west_down, cell)
    assert np.allclose(aspect, -np.pi / 2)
    slope, aspect = compute_slope_aspect(np.full((3, 3), 7.0), cell)
    assert np.all(slope == 0.0) and np.all(aspect == 0.0)
    diagonal = (rows - cols) * cell  # falls to the north-east
    _, aspect = compute_slope_aspect(diagonal, cell)
    assert np.allclose(aspect, np.pi / 4)
    for bad in (np.zeros(5), np.zeros((1, 5))):
        try:
            compute_slope_aspect(bad, cell)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")
