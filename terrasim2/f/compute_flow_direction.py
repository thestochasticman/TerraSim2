import numpy as np

# The eight neighbours as (row step, column step), and their distance factor.
OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
NO_OUTLET = -1


def compute_flow_direction(elevation: np.ndarray, cell_size: float) -> tuple[np.ndarray, np.ndarray]:
    """Where each cell drains: its steepest downhill neighbour of eight.

    The D8 rule. Slope to each neighbour is the drop divided by the
    distance between cell centres, so a diagonal neighbour must drop by
    sqrt(2) times more to win over a straight one. A cell with no lower
    neighbour drains nowhere; on a pit-filled surface those are the edge
    cells only.

    Parameters
    ----------
    elevation : ndarray, m
        Shape (rows, cols), finite.
    cell_size : float, m
        Edge length of one cell. Positive.

    Returns
    -------
    downstream : ndarray of int, dimensionless
        Shape (rows, cols): the flat index ``row * cols + col`` of the cell
        each cell drains to, or ``NO_OUTLET`` (-1).
    slope : ndarray, dimensionless
        Shape (rows, cols): the drop per metre along that direction, 0
        where there is no outlet.
    """
    z = np.asarray(elevation, dtype=np.float64)
    if z.ndim != 2 or not np.isfinite(z).all():
        raise ValueError("elevation must be a finite 2-D array")
    if not cell_size > 0:
        raise ValueError("cell_size must be positive")
    rows, cols = z.shape
    padded = np.pad(z, 1, constant_values=np.inf)
    best_slope = np.zeros(z.shape)
    best_target = np.full(z.shape, NO_OUTLET, dtype=np.int64)
    flat = np.arange(rows * cols).reshape(z.shape)
    for dr, dc in OFFSETS:
        neighbour = padded[1 + dr : 1 + dr + rows, 1 + dc : 1 + dc + cols]
        distance = cell_size * (np.sqrt(2.0) if dr and dc else 1.0)
        slope = (z - neighbour) / distance
        better = slope > best_slope
        best_slope = np.where(better, slope, best_slope)
        target = np.roll(np.roll(flat, -dr, axis=0), -dc, axis=1)
        best_target = np.where(better, target, best_target)
    return best_target, best_slope


def t1():
    """On a plane tilted to the east every interior cell drains east, with the plane's slope."""
    rows, cols = np.mgrid[0:4, 0:5]
    z = 100.0 - 2.0 * cols
    downstream, slope = compute_flow_direction(z, cell_size=10.0)
    flat = np.arange(20).reshape(4, 5)
    assert np.array_equal(downstream[:, :-1], flat[:, 1:])
    assert np.all(downstream[:, -1] == NO_OUTLET)
    assert np.allclose(slope[:, :-1], 0.2) and np.all(slope[:, -1] == 0)


def t2():
    """A diagonal only wins when its drop per metre beats the straight neighbour's."""
    z = np.array([[5.0, 4.0, 5.0], [5.0, 5.0, 5.0], [5.0, 5.0, 3.5]])
    downstream, _ = compute_flow_direction(z, cell_size=1.0)
    assert downstream[1, 1] == 2 * 3 + 2, "drop 1.5 over sqrt(2) beats drop 1 over 1"
    z[2, 2] = 3.8
    downstream, _ = compute_flow_direction(z, cell_size=1.0)
    assert downstream[1, 1] == 0 * 3 + 1, "drop 1.2 over sqrt(2) loses to drop 1 over 1"


def t3():
    """A cone drains inward to its lowest cell, a flat drains nowhere, and bad inputs are refused."""
    rows, cols = np.mgrid[0:5, 0:5]
    cone = np.hypot(rows - 2, cols - 2)
    downstream, _ = compute_flow_direction(cone, cell_size=1.0)
    assert downstream[2, 2] == NO_OUTLET
    centre = 2 * 5 + 2
    assert all(downstream[r, c] == centre for r, c in ((1, 1), (1, 2), (2, 1), (3, 3)))
    assert np.all(compute_flow_direction(np.zeros((3, 3)), 1.0)[0] == NO_OUTLET)
    for bad in (dict(elevation=np.zeros((3, 3)), cell_size=0.0), dict(elevation=np.array([[np.nan]]), cell_size=1.0)):
        try:
            compute_flow_direction(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
    t3()
