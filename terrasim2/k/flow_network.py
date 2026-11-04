import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET


class FlowNetwork:
    """Where water goes on a terrain, worked out once from its elevation.

    Built by ``build_flow_network``. Everything here follows from the
    pit-filled surface: the direction each cell drains, the order to visit
    cells so that upstream comes before downstream, and how many cells
    drain through each.

    Parameters
    ----------
    filled : ndarray, m
        Shape (rows, cols): the elevation with pits filled.
    downstream : ndarray of int, dimensionless
        Shape (rows, cols): flat index of the cell each cell drains to, or
        ``NO_OUTLET`` (-1) for the outlets.
    slope : ndarray, dimensionless
        Shape (rows, cols): drop per metre toward the downstream cell.
    order : ndarray of int, dimensionless
        Shape (rows * cols,): flat indices, upstream before downstream.
    upslope_cells : ndarray of int, dimensionless
        Shape (rows, cols): cells draining through each cell, itself included.

    Attributes
    ----------
    filled, downstream, slope, order, upslope_cells : as given
    shape : tuple[int, int], dimensionless
    """

    def __init__(self, filled: np.ndarray, downstream: np.ndarray, slope: np.ndarray, order: np.ndarray, upslope_cells: np.ndarray):
        self.filled = np.asarray(filled, dtype=np.float64)
        shape = self.filled.shape
        for name, arr in (("downstream", downstream), ("slope", slope), ("upslope_cells", upslope_cells)):
            if np.asarray(arr).shape != shape:
                raise ValueError(f"{name} must have shape {shape}")
        if np.asarray(order).shape != (self.filled.size,):
            raise ValueError("order must list every cell once")
        self.downstream = np.asarray(downstream, dtype=np.int64)
        self.slope = np.asarray(slope, dtype=np.float64)
        self.order = np.asarray(order, dtype=np.int64)
        self.upslope_cells = np.asarray(upslope_cells, dtype=np.int64)

    @property
    def shape(self) -> tuple[int, int]:
        return self.filled.shape

    def get_outlets(self) -> np.ndarray:
        """The cells that drain off the grid, as a boolean mask of shape (rows, cols)."""
        return self.downstream == NO_OUTLET


def t():
    """Holds its arrays, reports outlets, and refuses mismatched shapes."""
    filled = np.array([[2.0, 1.0], [2.0, 1.0]])
    downstream = np.array([[1, NO_OUTLET], [3, NO_OUTLET]])
    net = FlowNetwork(filled, downstream, np.ones((2, 2)), np.array([0, 2, 1, 3]), np.array([[1, 2], [1, 2]]))
    assert net.shape == (2, 2) and net.downstream.dtype == np.int64
    assert np.array_equal(net.get_outlets(), [[False, True], [False, True]])
    try:
        FlowNetwork(filled, downstream, np.ones((3, 3)), np.arange(4), np.ones((2, 2), dtype=int))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
