import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET


def compute_upslope_cells(downstream: np.ndarray, order: np.ndarray) -> np.ndarray:
    """How many cells drain through each cell, itself included.

    Walks the cells in flow order, handing each cell's count on to the
    cell it drains to. Multiply by the cell area for the upslope area.

    Parameters
    ----------
    downstream : ndarray of int, dimensionless
        Shape (rows, cols), from ``compute_flow_direction``.
    order : ndarray of int, dimensionless
        From ``compute_flow_order``: upstream before downstream.

    Returns
    -------
    ndarray of int, dimensionless
        Shape (rows, cols). At least 1 everywhere.
    """
    down = np.asarray(downstream).ravel()
    count = np.ones(down.shape, dtype=np.int64)
    for cell in np.asarray(order):
        target = down[cell]
        if target != NO_OUTLET:
            count[target] += count[cell]
    return count.reshape(np.asarray(downstream).shape)


def t():
    """On a plane tilted east each cell gathers the cells to its west; a cone's centre gathers all."""
    from terrasim2.f.compute_flow_direction import compute_flow_direction
    from terrasim2.f.compute_flow_order import compute_flow_order

    rows, cols = np.mgrid[0:3, 0:4]
    z = 10.0 - cols
    downstream, _ = compute_flow_direction(z, 1.0)
    count = compute_upslope_cells(downstream, compute_flow_order(z, downstream))
    assert np.array_equal(count, np.tile([1, 2, 3, 4], (3, 1)))
    cone = np.hypot(rows - 1, cols - 1)
    downstream, _ = compute_flow_direction(cone, 1.0)
    count = compute_upslope_cells(downstream, compute_flow_order(cone, downstream))
    assert count[1, 1] == 12 and count.max() == 12 and count.min() == 1
