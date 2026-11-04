import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET


def compute_flow_order(elevation: np.ndarray, downstream: np.ndarray) -> np.ndarray:
    """The order to visit cells so that every cell comes before the cell it drains to.

    Highest first. That is a valid order whenever each cell drains to a
    strictly lower one, which pit filling guarantees; the function checks
    it rather than trusting it.

    Parameters
    ----------
    elevation : ndarray, m
        Shape (rows, cols), the surface the directions were taken from.
    downstream : ndarray of int, dimensionless
        From ``compute_flow_direction`` on that surface.

    Returns
    -------
    ndarray of int, dimensionless
        Shape (rows * cols,): flat cell indices, upstream before downstream.
    """
    z = np.asarray(elevation, dtype=np.float64).ravel()
    down = np.asarray(downstream).ravel()
    if down.shape != z.shape:
        raise ValueError("downstream must have the elevation's shape")
    has_outlet = down != NO_OUTLET
    if np.any(z[down[has_outlet]] >= z[has_outlet]):
        raise ValueError("every cell must drain to a strictly lower cell; fill pits first")
    return np.argsort(-z, kind="stable")


def t1():
    """On a tilted plane the order runs from the high edge down, and each cell precedes its outlet."""
    from terrasim2.f.compute_flow_direction import compute_flow_direction

    rows, cols = np.mgrid[0:3, 0:4]
    z = 10.0 - cols
    downstream, _ = compute_flow_direction(z, 1.0)
    order = compute_flow_order(z, downstream)
    position = np.empty(12, dtype=int)
    position[order] = np.arange(12)
    for cell in range(12):
        if downstream.ravel()[cell] != NO_OUTLET:
            assert position[cell] < position[downstream.ravel()[cell]]


def t2():
    """A direction into a cell that is not lower is refused."""
    z = np.array([[1.0, 1.0]])
    try:
        compute_flow_order(z, np.array([[1, NO_OUTLET]]))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for a flat step")


def t():
    t1()
    t2()
