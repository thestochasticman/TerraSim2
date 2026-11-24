import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET


def compute_flow_levels(downstream: np.ndarray, order: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The cells grouped into levels that can each be stepped at once.

    A cell's level is the length of the longest flow path that ends in it:
    0 for a cell nothing drains into, and one more than the highest level
    among the cells draining into it otherwise. Every cell that drains into
    a cell therefore sits on a lower level, so a cascade can visit the
    levels in turn and treat all cells of a level together, with what
    arrives from upslope already known. The number of levels is the
    longest flow path on the grid, in cells.

    Parameters
    ----------
    downstream : ndarray of int, dimensionless
        Shape (rows, cols), from ``compute_flow_direction``.
    order : ndarray of int, dimensionless
        From ``compute_flow_order``: upstream before downstream.

    Returns
    -------
    cells : ndarray (rows * cols,) of int, dimensionless
        Flat indices sorted by level, ties in flow order.
    bounds : ndarray (n_levels + 1,) of int, dimensionless
        Level k is ``cells[bounds[k]:bounds[k + 1]]``.
    """
    down = np.asarray(downstream).ravel().tolist()
    level = [0] * len(down)
    for cell in np.asarray(order).tolist():
        target = down[cell]
        if target != NO_OUTLET and level[target] <= level[cell]:
            level[target] = level[cell] + 1
    level = np.asarray(level, dtype=np.int64)
    order = np.asarray(order)
    cells = order[np.argsort(level[order], kind="stable")]
    bounds = np.concatenate([[0], np.cumsum(np.bincount(level, minlength=int(level.max()) + 1 if level.size else 0))])
    return cells, bounds


def t1():
    """A plane tilted east: each column is one level, west to east."""
    from terrasim2.f.compute_flow_direction import compute_flow_direction
    from terrasim2.f.compute_flow_order import compute_flow_order

    rows, cols = np.mgrid[0:3, 0:4]
    z = 10.0 - cols
    downstream, _ = compute_flow_direction(z, 1.0)
    cells, bounds = compute_flow_levels(downstream, compute_flow_order(z, downstream))
    assert np.array_equal(bounds, [0, 3, 6, 9, 12])
    for k in range(4):
        assert sorted(np.asarray(cells[bounds[k]:bounds[k + 1]]) % 4) == [k, k, k]


def t2():
    """On a random hill every cell appears once, and everything draining into a cell sits on a lower level."""
    from terrasim2.f.compute_flow_direction import compute_flow_direction
    from terrasim2.f.compute_flow_order import compute_flow_order
    from terrasim2.f.fill_pits import fill_pits

    rng = np.random.default_rng(3)
    rows, cols = np.mgrid[0:25, 0:30]
    z = fill_pits(40.0 - 0.2 * np.hypot(rows - 12, cols - 15) + rng.normal(0, 0.3, (25, 30)))
    downstream, _ = compute_flow_direction(z, 10.0)
    cells, bounds = compute_flow_levels(downstream, compute_flow_order(z, downstream))
    assert np.array_equal(np.sort(cells), np.arange(25 * 30))
    level = np.empty(25 * 30, dtype=int)
    for k in range(len(bounds) - 1):
        level[cells[bounds[k]:bounds[k + 1]]] = k
    down = downstream.ravel()
    has = down != NO_OUTLET
    assert np.all(level[has] < level[down[has]])
    assert np.all(level[np.setdiff1d(np.arange(down.size), down[has])] == 0), "a cell nothing drains into is on level 0"


def t():
    t1()
    t2()
