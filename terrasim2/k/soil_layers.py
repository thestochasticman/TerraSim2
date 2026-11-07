import numpy as np
import numpy.typing as npt

from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
from terrasim2.f.compute_capacity_map import compute_capacity_map
from terrasim2.f.compute_layer_thickness_in_depth import compute_layer_thickness_in_depth
from terrasim2.f.estimate_saturated_conductivity import estimate_saturated_conductivity
from terrasim2.k.campbell_params import CampbellParams
from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.soil_hydraulics import SoilHydraulics
from terrasim2.k.soil_texture import SoilTexture


class SoilLayers:
    """A layered soil on the terrain, held per tile of a coarse soil source.

    Soil products come on their own lattice, far coarser than the terrain,
    so each cell reads one tile through ``cell_map`` and the values live
    once per tile. What is kept per tile and layer is prepared, not raw:
    the plant-available fraction, already evaluated from a retention
    curve, the textural class for display, and the curve itself so that
    conductivity can be derived from the same soil as capacity.

    Parameters
    ----------
    cell_map : CellToTileMap
        Which soil tile each terrain cell reads.
    layer_bounds : array_like, m
        Shape (L + 1,), ascending from 0; layer i spans
        ``layer_bounds[i]`` to ``layer_bounds[i + 1]``.
    available_fraction : array_like, m3 m-3
        Shape (L, n_tiles): field capacity minus wilting point of each
        layer of each tile, in [0, 1]. NaN where the source has no data.
    texture_index : array_like, dimensionless
        Shape (L, n_tiles), integers: index into ``list(SoilTexture)``,
        or -1 where the texture is unknown.
    campbell : array_like, optional
        Shape (3, L, n_tiles): Campbell's ``theta_s`` (m3 m-3), ``psi_e``
        (J kg-1) and ``b`` (dimensionless) per layer and tile, NaN where
        unknown. Absent for soils prepared without a curve.

    Attributes
    ----------
    cell_map, layer_bounds, available_fraction, texture_index, campbell : as given, as arrays
    n_layers, n_tiles : int, dimensionless
    shape : tuple[int, int], dimensionless, the terrain's (rows, cols)
    """

    def __init__(self, cell_map: CellToTileMap, layer_bounds: npt.ArrayLike, available_fraction: npt.ArrayLike, texture_index: npt.ArrayLike, campbell: npt.ArrayLike | None = None):
        bounds = np.array(layer_bounds, dtype=np.float64)
        if bounds.ndim != 1 or bounds.size < 2 or bounds[0] != 0 or np.any(np.diff(bounds) <= 0):
            raise ValueError("layer_bounds must be one ascending vector starting at 0")
        fraction = np.array(available_fraction, dtype=np.float64)
        expected = (bounds.size - 1, cell_map.n_tiles)
        if fraction.shape != expected:
            raise ValueError(f"available_fraction must have shape {expected}, got {fraction.shape}")
        if np.any(fraction < 0) or np.any(fraction > 1):
            raise ValueError("available_fraction must be within [0, 1] where known")
        texture = np.array(texture_index)
        if not np.issubdtype(texture.dtype, np.integer) or texture.shape != expected:
            raise ValueError(f"texture_index must be integers of shape {expected}")
        if texture.min() < -1 or texture.max() >= len(SoilTexture):
            raise ValueError(f"texture_index values must lie in [-1, {len(SoilTexture)})")
        curve = None if campbell is None else np.array(campbell, dtype=np.float64)
        if curve is not None:
            if curve.shape != (3, *expected):
                raise ValueError(f"campbell must have shape {(3, *expected)}, got {curve.shape}")
            known = np.isfinite(curve).all(axis=0)
            if np.any((curve[0][known] <= 0) | (curve[0][known] > 1)) or np.any(curve[1][known] >= 0) or np.any(curve[2][known] <= 0):
                raise ValueError("campbell needs theta_s in (0, 1], psi_e negative and b positive where known")
        self.cell_map = cell_map
        self.layer_bounds: np.ndarray = bounds
        self.available_fraction: np.ndarray = fraction
        self.texture_index: np.ndarray = texture.astype(np.int8)
        self.campbell: np.ndarray | None = curve

    @property
    def n_layers(self) -> int:
        return self.layer_bounds.size - 1

    @property
    def n_tiles(self) -> int:
        return self.cell_map.n_tiles

    @property
    def shape(self) -> tuple[int, int]:
        return self.cell_map.shape

    def compute_capacity(self, root_depth: npt.ArrayLike) -> np.ndarray:
        """Plant-available water per cell down to a root depth.

        Parameters
        ----------
        root_depth : array_like, m
            Positive; a scalar or a field of the terrain's shape.

        Returns
        -------
        ndarray, mm
            Shape (rows, cols). NaN where a layer the roots reach has no data.
        """
        on_cells = np.stack([self.cell_map.spread_to_cells(layer) for layer in self.available_fraction])
        return compute_capacity_map(on_cells, self.layer_bounds, root_depth)

    def compute_hydraulics(self, root_depth: npt.ArrayLike) -> SoilHydraulics:
        """Each cell's soil over the root depth, as one set of arrays for a step.

        The curve parameters of the layers the roots reach are averaged,
        weighted by how much of each layer lies within the depth; from that
        one curve per cell come the saturated conductivity (eq. 6.34), the
        contents at field capacity and wilting point, and with the layered
        sum the capacity. Averaging parameters is a simplification: it
        treats the root zone as one soil.

        Parameters
        ----------
        root_depth : float or array_like, m
            Positive; one value, or a field of the terrain's shape where
            roots vary by cell, as under trees and grass.

        Returns
        -------
        SoilHydraulics
            With conductivity fields when the layers carry a curve, else
            capacity only. NaN per cell where a reached layer is unknown.
        """
        depth = np.asarray(root_depth, dtype=np.float64)
        if depth.ndim not in (0, 2) or (depth.ndim == 2 and depth.shape != self.shape):
            raise ValueError(f"root_depth must be one value or a field of shape {self.shape}")
        if not np.all(depth > 0):
            raise ValueError("root_depth must be positive")
        capacity = self.compute_capacity(depth)
        if self.campbell is None:
            return SoilHydraulics(capacity, root_depth)
        thickness = compute_layer_thickness_in_depth(self.layer_bounds, depth)
        if thickness.ndim == 1:
            weights = thickness / thickness.sum()
            mean = np.einsum("l,pln->pn", weights, self.campbell)
            reached = weights > 0
            unknown = ~np.isfinite(self.campbell[:, reached]).all(axis=(0, 1))
            mean[:, unknown] = np.nan
            theta_s, psi_e, b = (self.cell_map.spread_to_cells(row) for row in mean)
        else:
            weights = thickness / thickness.sum(axis=0)
            on_cells = self.campbell[:, :, self.cell_map.tile_index]
            mean = np.einsum("lrc,plrc->prc", weights, on_cells)
            unknown = (~np.isfinite(on_cells) & (weights > 0)[None]).any(axis=(0, 1))
            mean[:, unknown] = np.nan
            theta_s, psi_e, b = mean
        known = np.isfinite(theta_s) & np.isfinite(psi_e) & np.isfinite(b)
        k_sat = np.full(self.shape, np.nan)
        theta_fc = np.full(self.shape, np.nan)
        theta_wp = np.full(self.shape, np.nan)
        if np.any(known):
            params = CampbellParams(theta_s[known], psi_e[known], b[known])
            k_sat[known] = estimate_saturated_conductivity(params.theta_s, params.psi_e, params.b)
            theta_fc[known] = compute_campbell_water_content(-33.0, params)
            theta_wp[known] = compute_campbell_water_content(-1500.0, params)
        return SoilHydraulics(capacity, root_depth, k_sat, b, theta_s, theta_fc, theta_wp)

    def get_texture_on_cells(self, layer: int) -> np.ndarray:
        """One layer's textural class laid out over the cells.

        Parameters
        ----------
        layer : int, dimensionless
            Index into the layers, 0 at the surface.

        Returns
        -------
        ndarray of int, dimensionless
            Shape (rows, cols); index into ``list(SoilTexture)``, -1 where unknown.
        """
        if not 0 <= layer < self.n_layers:
            raise IndexError(f"layer {layer} outside [0, {self.n_layers})")
        return self.cell_map.spread_to_cells(self.texture_index[layer])


def _fixture(with_curve: bool = False) -> SoilLayers:
    from terrasim2.k.terrain_grid import TerrainGrid

    grid = TerrainGrid(elevation=np.zeros((2, 3)), cell_size=10.0)
    cell_map = CellToTileMap(grid, tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    # Tile 0 is sand over clay; tile 1 is loam throughout.
    fraction = [[0.035, 0.116], [0.035, 0.116], [0.148, 0.116]]
    texture = [[0, 4], [0, 4], [11, 4]]
    campbell = None
    if with_curve:
        campbell = np.array([
            [[0.37, 0.43], [0.37, 0.43], [0.50, 0.43]],
            [[-0.73, -1.12], [-0.73, -1.12], [-3.73, -1.12]],
            [[1.69, 4.55], [1.69, 4.55], [7.63, 4.55]],
        ])
    return SoilLayers(cell_map, [0.0, 0.1, 0.3, 1.0], fraction, texture, campbell)


def t1():
    """Shapes and counts, and the capacity of each cell follows its tile's column and the root depth."""
    soil = _fixture()
    assert soil.n_layers == 3 and soil.n_tiles == 2 and soil.shape == (2, 3) and soil.campbell is None
    shallow = soil.compute_capacity(0.3)
    assert shallow.shape == (2, 3)
    assert np.isclose(shallow[0, 0], 0.035 * 300) and np.isclose(shallow[0, 2], 0.116 * 300)
    deep = soil.compute_capacity(1.0)
    assert np.isclose(deep[0, 0], 0.035 * 300 + 0.148 * 700) and np.isclose(deep[1, 1], 0.116 * 1000)
    per_cell = soil.compute_capacity(np.array([[0.3, 0.3, 0.3], [1.0, 1.0, 1.0]]))
    assert np.isclose(per_cell[0, 0], shallow[0, 0]) and np.isclose(per_cell[1, 0], deep[1, 0])


def t2():
    """Textures spread to cells per layer, and NaN fractions give NaN capacity only where the roots reach them."""
    soil = _fixture()
    assert np.array_equal(soil.get_texture_on_cells(2), [[11, 11, 4], [11, 4, 4]])
    assert soil.texture_index.dtype == np.int8
    try:
        soil.get_texture_on_cells(3)
    except IndexError:
        pass
    else:
        raise AssertionError("expected IndexError")
    fraction = np.array(soil.available_fraction)
    fraction[2, 0] = np.nan
    gappy = SoilLayers(soil.cell_map, soil.layer_bounds, fraction, soil.texture_index)
    assert np.isfinite(gappy.compute_capacity(0.3)).all()
    assert np.isnan(gappy.compute_capacity(1.0)[0, 0]) and np.isfinite(gappy.compute_capacity(1.0)[0, 2])


def t3():
    """Hydraulics over the root depth: without a curve only capacity; with one, the sand tile conducts far
    more than the loam tile at 0.3 m, and at 1 m the sand-over-clay column is a weighted mix."""
    bare = _fixture().compute_hydraulics(0.3)
    assert not bare.has_conductivity and np.isclose(bare.capacity[0, 0], 0.035 * 300) and bare.root_depth == 0.3
    soil = _fixture(with_curve=True)
    h = soil.compute_hydraulics(0.3)
    assert h.has_conductivity and h.shape == (2, 3)
    assert np.isclose(h.b[0, 0], 1.69) and np.isclose(h.b[0, 2], 4.55), "within the top 0.3 m each tile is one soil"
    assert h.k_sat[0, 0] > 3 * h.k_sat[0, 2], "eq. 6.34 compresses the table's sand-to-loam ratio of 16 to about 4.6"
    assert h.theta_wp[0, 0] < h.theta_fc[0, 0] < h.theta_s[0, 0]
    deep = soil.compute_hydraulics(1.0)
    assert np.isclose(deep.b[0, 0], 0.3 * 1.69 + 0.7 * 7.63) and np.isclose(deep.theta_s[0, 0], 0.3 * 0.37 + 0.7 * 0.50)
    assert np.isclose(deep.b[0, 2], 4.55)


def t4():
    """Bad bounds, a fraction array of the wrong shape or range, bad texture indices and a bad curve are refused."""
    soil = _fixture()
    good = dict(cell_map=soil.cell_map, layer_bounds=soil.layer_bounds, available_fraction=soil.available_fraction, texture_index=soil.texture_index)
    bad = [
        {**good, "layer_bounds": [0.1, 0.3, 1.0, 2.0]},
        {**good, "available_fraction": np.zeros((2, 2))},
        {**good, "available_fraction": np.full((3, 2), 1.5)},
        {**good, "texture_index": np.full((3, 2), 12)},
        {**good, "texture_index": np.zeros((3, 2))},
        {**good, "campbell": np.zeros((2, 3, 2))},
        {**good, "campbell": np.full((3, 3, 2), 0.5)},
    ]
    for kwargs in bad:
        try:
            SoilLayers(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t5():
    """A field of root depths gives each cell the hydraulics the scalar depth would, cell by cell; a field of the
    wrong shape is refused."""
    soil = _fixture(with_curve=True)
    field = np.array([[0.3, 0.3, 1.0], [1.0, 0.3, 0.3]])
    varied = soil.compute_hydraulics(field)
    shallow = soil.compute_hydraulics(0.3)
    deep = soil.compute_hydraulics(1.0)
    assert isinstance(varied.root_depth, np.ndarray) and np.array_equal(varied.root_depth, field)
    for name in ("capacity", "k_sat", "b", "theta_s", "theta_fc", "theta_wp"):
        expected = np.where(field == 0.3, getattr(shallow, name), getattr(deep, name))
        assert np.allclose(getattr(varied, name), expected, equal_nan=True), name
    assert varied.capacity[0, 2] > varied.capacity[0, 0], "deeper roots over the same column hold more"
    assert varied.b[0, 2] != varied.b[0, 0], "the clay the deep roots reach changes the curve"
    for bad in (np.full((3, 2), 0.3), np.array([[0.3, 0.3, 0.0], [0.3, 0.3, 0.3]])):
        try:
            soil.compute_hydraulics(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for a bad field")


def t():
    t1()
    t2()
    t3()
    t4()
    t5()
