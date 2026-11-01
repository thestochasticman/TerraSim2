import numpy as np
import numpy.typing as npt

from terrasim2.f.compute_capacity_map import compute_capacity_map
from terrasim2.k.cell_to_tile_map import CellToTileMap
from terrasim2.k.soil_texture import SoilTexture


class SoilLayers:
    """A layered soil on the terrain, held per tile of a coarse soil source.

    Soil products come on their own lattice, far coarser than the terrain,
    so each cell reads one tile through ``cell_map`` and the values live
    once per tile. What is kept per tile and layer is prepared, not raw:
    the plant-available fraction, already evaluated from a retention
    curve, and the textural class for display.

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

    Attributes
    ----------
    cell_map, layer_bounds, available_fraction, texture_index : as given, as arrays
    n_layers, n_tiles : int, dimensionless
    shape : tuple[int, int], dimensionless, the terrain's (rows, cols)
    """

    def __init__(self, cell_map: CellToTileMap, layer_bounds: npt.ArrayLike, available_fraction: npt.ArrayLike, texture_index: npt.ArrayLike):
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
        self.cell_map = cell_map
        self.layer_bounds: np.ndarray = bounds
        self.available_fraction: np.ndarray = fraction
        self.texture_index: np.ndarray = texture.astype(np.int8)

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


def _fixture() -> SoilLayers:
    from terrasim2.k.terrain_grid import TerrainGrid

    grid = TerrainGrid(elevation=np.zeros((2, 3)), cell_size=10.0)
    cell_map = CellToTileMap(grid, tile_index=[[0, 0, 1], [0, 1, 1]], n_tiles=2)
    # Tile 0 is sand over clay; tile 1 is loam throughout.
    fraction = [[0.035, 0.116], [0.035, 0.116], [0.148, 0.116]]
    texture = [[0, 4], [0, 4], [11, 4]]
    return SoilLayers(cell_map, [0.0, 0.1, 0.3, 1.0], fraction, texture)


def t1():
    """Shapes and counts, and the capacity of each cell follows its tile's column and the root depth."""
    soil = _fixture()
    assert soil.n_layers == 3 and soil.n_tiles == 2 and soil.shape == (2, 3)
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
    """Bad bounds, a fraction array of the wrong shape or range, and bad texture indices are refused."""
    soil = _fixture()
    good = dict(cell_map=soil.cell_map, layer_bounds=soil.layer_bounds, available_fraction=soil.available_fraction, texture_index=soil.texture_index)
    bad = [
        {**good, "layer_bounds": [0.1, 0.3, 1.0, 2.0]},
        {**good, "available_fraction": np.zeros((2, 2))},
        {**good, "available_fraction": np.full((3, 2), 1.5)},
        {**good, "texture_index": np.full((3, 2), 12)},
        {**good, "texture_index": np.zeros((3, 2))},
    ]
    for kwargs in bad:
        try:
            SoilLayers(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
    t3()
