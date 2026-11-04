import heapq

import numpy as np

EPSILON = 1e-4


def fill_pits(elevation: np.ndarray, epsilon: float = EPSILON) -> np.ndarray:
    """Raise every depression so that each cell has a strictly lower neighbour or sits on the edge.

    Priority flood from the grid edge inward: cells are visited lowest
    first, and a cell is never allowed to sit below the cell it was reached
    from by less than ``epsilon``. The result is the original surface with
    its pits filled to their spill level and given a faint slope toward
    the spill, so water routed by steepest descent always reaches the edge.

    Parameters
    ----------
    elevation : ndarray, m
        Shape (rows, cols), finite.
    epsilon : float, m
        The least drop from a cell to the one it drains to inside a filled
        area. Small against real slopes.

    Returns
    -------
    ndarray, m
        Same shape; never below ``elevation``.
    """
    z = np.asarray(elevation, dtype=np.float64)
    if z.ndim != 2 or not np.isfinite(z).all():
        raise ValueError("elevation must be a finite 2-D array")
    rows, cols = z.shape
    filled = z.copy()
    visited = np.zeros(z.shape, dtype=bool)
    heap: list[tuple[float, int, int]] = []
    for r in range(rows):
        for c in (0, cols - 1):
            if not visited[r, c]:
                visited[r, c] = True
                heapq.heappush(heap, (filled[r, c], r, c))
    for c in range(cols):
        for r in (0, rows - 1):
            if not visited[r, c]:
                visited[r, c] = True
                heapq.heappush(heap, (filled[r, c], r, c))
    while heap:
        level, r, c = heapq.heappop(heap)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (dr or dc) and 0 <= rr < rows and 0 <= cc < cols and not visited[rr, cc]:
                    visited[rr, cc] = True
                    filled[rr, cc] = max(filled[rr, cc], level + epsilon)
                    heapq.heappush(heap, (filled[rr, cc], rr, cc))
    return filled


def t1():
    """A bowl inside a plateau is raised to its rim plus a faint slope, and nothing else moves."""
    z = np.full((5, 5), 10.0)
    z[1:4, 1:4] = 5.0
    z[2, 2] = 1.0
    out = fill_pits(z)
    assert np.array_equal(out[0], z[0]) and np.array_equal(out[:, 0], z[:, 0])
    assert out.min() >= 10.0 and out[2, 2] > 10.0
    assert np.all(out >= z)
    assert out[2, 2] - 10.0 < 10 * EPSILON


def t2():
    """A surface with no pits comes back unchanged, and every interior cell gains a strictly lower neighbour."""
    rows, cols = np.mgrid[0:6, 0:7]
    plane = 100.0 - 0.5 * rows - 0.25 * cols
    assert np.array_equal(fill_pits(plane), plane)
    z = np.full((6, 6), 20.0)
    z[2:4, 2:4] = 3.0
    out = fill_pits(z)
    for r in range(1, 5):
        for c in range(1, 5):
            neighbours = out[r - 1 : r + 2, c - 1 : c + 2]
            assert neighbours.min() < out[r, c], (r, c)


def t3():
    """NaN and non-2-D inputs are refused."""
    for bad in (np.array([1.0, 2.0]), np.array([[1.0, np.nan], [0.0, 1.0]])):
        try:
            fill_pits(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
    t3()
