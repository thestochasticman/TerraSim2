import numpy as np
import numpy.typing as npt


DEFAULT_CAPACITY_MM = 100.0


class TerrainGrid:
    """Regular raster of terrain cells, stored as one array per property.

    Every property is a float64 array of shape (rows, cols). Static
    properties (elevation, capacity) are set once; state (moisture)
    changes as the model steps.

    Parameters
    ----------
    elevation : array_like
        Ground elevation per cell, metres. Defines the grid shape.
    cell_size : float
        Edge length of one square cell, metres.
    capacity : array_like, optional
        Bucket capacity per cell, millimetres. Defaults to DEFAULT_CAPACITY_MM everywhere.
    moisture : array_like, optional
        Initial water stored per cell, millimetres. Defaults to zeros.
    """

    def __init__(
        self,
        elevation: npt.ArrayLike,
        cell_size: float,
        capacity: npt.ArrayLike | None = None,
        moisture: npt.ArrayLike | None = None,
    ):
        elev = np.array(elevation, dtype=np.float64)
        if elev.ndim != 2:
            raise ValueError(f"elevation must be 2-D, got shape {elev.shape}")
        if cell_size <= 0:
            raise ValueError(f"cell_size must be positive, got {cell_size}")
        self.rows: int
        self.cols: int
        self.rows, self.cols = elev.shape
        self.cell_size: float = float(cell_size)
        self.elevation: np.ndarray = elev

        self.capacity: np.ndarray = (
            np.full(self.shape, DEFAULT_CAPACITY_MM, dtype=np.float64)
            if capacity is None
            else np.array(capacity, dtype=np.float64)
        )
        if self.capacity.shape != self.shape:
            raise ValueError(f"capacity shape {self.capacity.shape} does not match grid shape {self.shape}")

        self.moisture: np.ndarray = (
            np.zeros(self.shape, dtype=np.float64)
            if moisture is None
            else np.array(moisture, dtype=np.float64)
        )
        if self.moisture.shape != self.shape:
            raise ValueError(f"moisture shape {self.moisture.shape} does not match grid shape {self.shape}")

    @property
    def shape(self) -> tuple[int, int]:
        return (self.rows, self.cols)



def t1():
    """Construction from a 2-D array sets shape and defaults."""
    g = TerrainGrid([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], cell_size=10.0)
    assert g.shape == (2, 3)
    assert g.rows == 2 and g.cols == 3
    assert g.cell_size == 10.0
    assert g.elevation.dtype == np.float64
    assert np.all(g.capacity == DEFAULT_CAPACITY_MM)
    assert np.all(g.moisture == 0.0)
    assert g.capacity.shape == g.shape and g.moisture.shape == g.shape


def t2():
    """Explicit capacity and moisture are stored as float64 copies."""
    cap = np.array([[10, 20], [30, 40]])
    g = TerrainGrid(np.zeros((2, 2)), cell_size=1.0, capacity=cap, moisture=cap / 2)
    assert g.capacity.dtype == np.float64
    assert np.array_equal(g.capacity, [[10.0, 20.0], [30.0, 40.0]])
    assert np.array_equal(g.moisture, [[5.0, 10.0], [15.0, 20.0]])
    cap[0, 0] = 99
    assert g.capacity[0, 0] == 10.0, "grid must own its data, not alias the input"


def t3():
    """Bad inputs raise ValueError."""
    for bad in (dict(elevation=[1.0, 2.0], cell_size=1.0),
                dict(elevation=np.zeros((2, 2)), cell_size=0.0),
                dict(elevation=np.zeros((2, 2)), cell_size=1.0, capacity=np.zeros((3, 3)))):
        try:
            TerrainGrid(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")



def t():
    t1()
    t2()
    t3()


if __name__ == "__main__":
    t()
    print("terrain_grid: ok")
