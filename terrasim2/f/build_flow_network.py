import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET, compute_flow_direction
from terrasim2.f.compute_flow_order import compute_flow_order
from terrasim2.f.compute_upslope_cells import compute_upslope_cells
from terrasim2.f.fill_pits import fill_pits
from terrasim2.k.flow_network import FlowNetwork
from terrasim2.k.terrain_grid import TerrainGrid


def build_flow_network(grid: TerrainGrid) -> FlowNetwork:
    """Work out a terrain's drainage once: fill its pits, take the steepest
    descent from every cell, order the cells, and count what drains through each.

    Parameters
    ----------
    grid : TerrainGrid
        Uses ``elevation`` (m) and ``cell_size`` (m).

    Returns
    -------
    FlowNetwork
        On which every cell but the outlets drains to a strictly lower cell,
        and the outlets lie on the grid's edge.
    """
    filled = fill_pits(grid.elevation)
    downstream, slope = compute_flow_direction(filled, grid.cell_size)
    order = compute_flow_order(filled, downstream)
    return FlowNetwork(filled, downstream, slope, order, compute_upslope_cells(downstream, order))


def t1():
    """A hill with a hollow: the hollow is filled, every interior cell drains, and all water reaches the edge."""
    rows, cols = np.mgrid[0:9, 0:9]
    z = 50.0 - 0.5 * np.hypot(rows - 4, cols - 4) ** 2 / 4
    z[6, 6] -= 3.0
    net = build_flow_network(TerrainGrid(elevation=z, cell_size=10.0))
    assert net.filled[6, 6] > z[6, 6]
    outlets = net.get_outlets()
    edge = np.zeros((9, 9), dtype=bool)
    edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
    assert np.all(outlets[~edge] == False)  # noqa: E712
    assert net.upslope_cells.min() >= 1
    assert net.upslope_cells[outlets].sum() == 81, "every cell drains through exactly one outlet"


def t2():
    """Tarrawarra: every cell drains to the edge through strictly lower cells, and one outlet gathers a large share."""
    from pathlib import Path

    from terrasim2.f.load_model_inputs import load_model_inputs

    inputs = load_model_inputs(Path(__file__).resolve().parents[2] / "data" / "dev_sites" / "tarrawarra" / "model_inputs")
    net = build_flow_network(inputs.grid)
    n = inputs.grid.elevation.size
    down = net.downstream.ravel()
    has = down != NO_OUTLET
    assert np.all(net.filled.ravel()[down[has]] < net.filled.ravel()[has])
    assert net.get_outlets().sum() < n and np.all(net.get_outlets()[1:-1, 1:-1] == False)  # noqa: E712
    assert net.upslope_cells.max() > 0.1 * n, "a catchment outlet should gather a sizeable share of the cells"
    assert np.abs(net.filled - inputs.grid.elevation).max() < 5.0, "filling a real DEM should not raise anything by metres"


def t():
    t1()
    t2()
