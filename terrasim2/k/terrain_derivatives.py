from functools import cached_property

import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET, compute_flow_direction
from terrasim2.f.compute_flow_order import compute_flow_order
from terrasim2.f.compute_slope_aspect import compute_slope_aspect
from terrasim2.f.compute_solar_ratio import compute_solar_ratio
from terrasim2.f.compute_upslope_cells import compute_upslope_cells
from terrasim2.f.fill_pits import fill_pits
from terrasim2.k.terrain_grid import TerrainGrid


class TerrainDerivatives:
    """Everything that follows from a terrain's shape, computed on first use and kept.

    Each derivative is a property that calls its ``f/`` function the first
    time it is read and caches the result, so a step that never asks pays
    nothing, and asking for a later one pulls in the ones it rests on.
    Every derivative is a function of the grid's elevation and cell size
    alone, plus the latitude for the sun's path; nothing that depends on
    a day, a run or a parameter belongs here.

    Parameters
    ----------
    grid : TerrainGrid
        Uses ``elevation`` (m) and ``cell_size`` (m).
    latitude : float, degrees, optional
        Of the grid, negative south; needed for ``solar_ratio`` only.

    Attributes
    ----------
    grid : TerrainGrid
    latitude : float or None, degrees
    shape : tuple[int, int], dimensionless
    filled : ndarray (rows, cols), m
        The elevation with pits filled, from ``fill_pits``.
    downstream : ndarray (rows, cols) of int, dimensionless
        Flat index of the cell each cell drains to, or ``NO_OUTLET`` (-1).
    slope : ndarray (rows, cols), dimensionless
        Drop per metre toward the downstream cell, 0 at outlets.
    order : ndarray (rows * cols,) of int, dimensionless
        Flat indices, upstream before downstream.
    upslope_cells : ndarray (rows, cols) of int, dimensionless
        Cells draining through each cell, itself included.
    surface_slope : ndarray (rows, cols), radians
        The ground's own tilt by central differences, from ``compute_slope_aspect``.
    aspect : ndarray (rows, cols), radians
        The direction the ground faces, downslope clockwise from north.
    solar_ratio : ndarray (rows, cols), dimensionless
        Direct sun on the tilted ground over a year relative to flat
        ground, from ``compute_solar_ratio``; needs the latitude.
    """

    def __init__(self, grid: TerrainGrid, latitude: float | None = None):
        self.grid = grid
        self.latitude = None if latitude is None else float(latitude)

    @property
    def shape(self) -> tuple[int, int]:
        return self.grid.shape

    @cached_property
    def filled(self) -> np.ndarray:
        return fill_pits(self.grid.elevation)

    @cached_property
    def _direction(self) -> tuple[np.ndarray, np.ndarray]:
        return compute_flow_direction(self.filled, self.grid.cell_size)

    @cached_property
    def downstream(self) -> np.ndarray:
        return self._direction[0]

    @cached_property
    def slope(self) -> np.ndarray:
        return self._direction[1]

    @cached_property
    def order(self) -> np.ndarray:
        return compute_flow_order(self.filled, self.downstream)

    @cached_property
    def upslope_cells(self) -> np.ndarray:
        return compute_upslope_cells(self.downstream, self.order)

    @cached_property
    def _tilt(self) -> tuple[np.ndarray, np.ndarray]:
        return compute_slope_aspect(self.grid.elevation, self.grid.cell_size)

    @cached_property
    def surface_slope(self) -> np.ndarray:
        return self._tilt[0]

    @cached_property
    def aspect(self) -> np.ndarray:
        return self._tilt[1]

    @cached_property
    def solar_ratio(self) -> np.ndarray:
        if self.latitude is None:
            raise ValueError("solar_ratio needs the grid's latitude; these inputs do not say where they are")
        return compute_solar_ratio(self.surface_slope, self.aspect, self.latitude)

    def get_outlets(self) -> np.ndarray:
        """The cells that drain off the grid, as a boolean mask of shape (rows, cols)."""
        return self.downstream == NO_OUTLET


def t1():
    """Nothing is computed until asked; each derivative is computed once and matches its function."""
    from unittest import mock

    rows, cols = np.mgrid[0:6, 0:7]
    grid = TerrainGrid(elevation=100.0 - 0.5 * rows - 0.25 * cols, cell_size=10.0)
    d = TerrainDerivatives(grid)
    assert "filled" not in d.__dict__ and d.shape == (6, 7)
    with mock.patch("terrasim2.k.terrain_derivatives.fill_pits", wraps=fill_pits) as spy:
        a = d.filled
        b = d.filled
        assert spy.call_count == 1 and a is b
    assert np.array_equal(d.filled, grid.elevation)
    assert np.array_equal(d.downstream, compute_flow_direction(d.filled, 10.0)[0])
    assert np.array_equal(d.slope, compute_flow_direction(d.filled, 10.0)[1])
    assert np.array_equal(d.order, compute_flow_order(d.filled, d.downstream))
    assert np.array_equal(d.upslope_cells, compute_upslope_cells(d.downstream, d.order))


def t2():
    """A hill with a hollow: the hollow is filled, only edge cells are outlets, and every cell leaves through exactly one."""
    rows, cols = np.mgrid[0:9, 0:9]
    z = 50.0 - 0.5 * np.hypot(rows - 4, cols - 4) ** 2 / 4
    z[6, 6] -= 3.0
    d = TerrainDerivatives(TerrainGrid(elevation=z, cell_size=10.0))
    assert d.filled[6, 6] > z[6, 6]
    outlets = d.get_outlets()
    edge = np.zeros((9, 9), dtype=bool)
    edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
    assert not outlets[~edge].any()
    assert d.upslope_cells.min() >= 1 and d.upslope_cells[outlets].sum() == 81


def t3():
    """Tarrawarra: every cell drains to the edge through strictly lower cells, filling raises nothing by metres,
    and one outlet gathers a large share."""
    from pathlib import Path

    from terrasim2.f.load_model_inputs import load_model_inputs

    inputs = load_model_inputs(Path(__file__).resolve().parents[2] / "data" / "dev_sites" / "tarrawarra" / "model_inputs")
    d = TerrainDerivatives(inputs.grid)
    n = inputs.grid.elevation.size
    down = d.downstream.ravel()
    has = down != NO_OUTLET
    assert np.all(d.filled.ravel()[down[has]] < d.filled.ravel()[has])
    assert d.get_outlets().sum() < n and not d.get_outlets()[1:-1, 1:-1].any()
    assert d.upslope_cells.max() > 0.1 * n
    assert np.abs(d.filled - inputs.grid.elevation).max() < 5.0


def t4():
    """The ground's tilt and the sun: a plane falling north at 37 degrees south takes more sun than flat and is
    computed once; without a latitude the solar ratio is refused while the tilt still works."""
    from unittest import mock

    rows, cols = np.mgrid[0:6, 0:7]
    grid = TerrainGrid(elevation=100.0 + 2.0 * rows, cell_size=10.0)
    bare = TerrainDerivatives(grid)
    assert np.allclose(bare.surface_slope, np.arctan(0.2)) and np.allclose(bare.aspect, 0.0)
    try:
        bare.solar_ratio
    except ValueError as err:
        assert "latitude" in str(err)
    else:
        raise AssertionError("expected ValueError without a latitude")
    d = TerrainDerivatives(grid, latitude=-37.66)
    with mock.patch("terrasim2.k.terrain_derivatives.compute_solar_ratio", wraps=compute_solar_ratio) as spy:
        a = d.solar_ratio
        b = d.solar_ratio
        assert spy.call_count == 1 and a is b
    assert d.latitude == -37.66 and np.all(d.solar_ratio > 1.0)
    assert np.allclose(TerrainDerivatives(TerrainGrid(elevation=np.zeros((3, 3)), cell_size=10.0), latitude=-37.66).solar_ratio, 1.0)


def t():
    t1()
    t2()
    t3()
    t4()
