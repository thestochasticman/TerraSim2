import numpy as np
import numpy.typing as npt

from terrasim2.f.classify_vegetation import UNKNOWN, VEGETATION_CLASSES


class VegetationMap:
    """What grows on each cell of a terrain, as a class and the statistics it was read from.

    Built by ``troi_ingest`` from a year of Sentinel-2 NDVI, or read from
    disk by ``load_vegetation_map``; written by ``write_vegetation_map``.
    Kept beside the model inputs rather than in them, so an inputs folder
    stays valid without imagery and a map can be remade without touching
    the soil or the climate.

    Parameters
    ----------
    class_index : array_like of int, dimensionless
        Shape (rows, cols): index into ``VEGETATION_CLASSES`` per cell,
        -1 where unknown.
    features : dict of str to array_like, dimensionless
        The NDVI statistics the classes came from, each of shape (rows,
        cols): at least ``low``, ``median`` and ``high``; NaN where unseen.
    meta : dict, optional
        Free-form provenance (stub, imagery period, thresholds, scenes).

    Attributes
    ----------
    class_index : ndarray (rows, cols), int8
    features : dict of str to ndarray (rows, cols), float32
    classes : tuple of str, ``VEGETATION_CLASSES``
    meta : dict
    shape : tuple[int, int], dimensionless
    """

    FORMAT_VERSION = 1

    def __init__(self, class_index: npt.ArrayLike, features: dict[str, npt.ArrayLike], meta: dict | None = None):
        self.class_index = np.asarray(class_index).astype(np.int8)
        if self.class_index.ndim != 2:
            raise ValueError("class_index must be 2-D")
        if np.any(self.class_index < UNKNOWN) or np.any(self.class_index >= len(VEGETATION_CLASSES)):
            raise ValueError(f"class_index must index {VEGETATION_CLASSES} or be -1")
        self.features = {name: np.asarray(values, dtype=np.float32) for name, values in features.items()}
        for name in ("low", "median", "high"):
            if name not in self.features:
                raise ValueError(f"features must include {name!r}")
        for name, values in self.features.items():
            if values.shape != self.class_index.shape:
                raise ValueError(f"feature {name!r} has shape {values.shape}, not {self.class_index.shape}")
        self.classes = VEGETATION_CLASSES
        self.meta: dict = dict(meta or {})

    @property
    def shape(self) -> tuple[int, int]:
        return self.class_index.shape

    def compute_fraction(self, class_name: str) -> float:
        """The share of known cells in a class, dimensionless."""
        known = self.class_index != UNKNOWN
        if not known.any():
            return float("nan")
        return float(np.mean(self.class_index[known] == self.classes.index(class_name)))

    def compute_root_depth(self, depth_by_class: dict[str, float], unknown_depth: float) -> np.ndarray:
        """A root depth per cell from one depth per class.

        Parameters
        ----------
        depth_by_class : dict of str to float, m
            A positive depth for every class in ``classes``.
        unknown_depth : float, m
            The depth of cells whose class is unknown. Positive.

        Returns
        -------
        ndarray, m
            Shape (rows, cols), float64.
        """
        missing = [c for c in self.classes if c not in depth_by_class]
        if missing:
            raise ValueError(f"depth_by_class lacks {missing}")
        depths = [float(depth_by_class[c]) for c in self.classes] + [float(unknown_depth)]
        if any(not d > 0 for d in depths):
            raise ValueError("every root depth must be positive")
        table = np.array(depths)
        return table[np.where(self.class_index == UNKNOWN, len(self.classes), self.class_index)]


def _example() -> VegetationMap:
    return VegetationMap(
        [[0, 1, -1], [1, 1, 0]],
        {"low": [[0.2, 0.6, np.nan], [0.5, 0.7, 0.1]], "median": [[0.4, 0.7, np.nan], [0.6, 0.75, 0.3]], "high": [[0.8, 0.8, np.nan], [0.7, 0.8, 0.6]]},
        meta={"stub": "unit"},
    )


def t1():
    """Holds classes and features with the declared dtypes, counts the tree share among known cells, and turns a
    depth per class into a field with the unknown depth where the class is unknown."""
    v = _example()
    assert v.shape == (2, 3) and v.class_index.dtype == np.int8 and v.features["low"].dtype == np.float32
    assert v.classes == ("grass", "tree") and v.meta == {"stub": "unit"}
    assert abs(v.compute_fraction("tree") - 3 / 5) < 1e-12 and abs(v.compute_fraction("grass") - 2 / 5) < 1e-12
    depth = v.compute_root_depth({"grass": 0.3, "tree": 1.2}, unknown_depth=0.5)
    assert depth.dtype == np.float64 and depth.tolist() == [[0.3, 1.2, 0.5], [1.2, 1.2, 0.3]]
    unknown = VegetationMap(np.full((1, 2), -1), {"low": np.full((1, 2), np.nan), "median": np.full((1, 2), np.nan), "high": np.full((1, 2), np.nan)})
    assert np.isnan(unknown.compute_fraction("tree"))


def t2():
    """A class outside the list, a missing or misshapen feature, a missing depth and a non-positive depth are refused."""
    good = dict(class_index=[[0, 1]], features={"low": [[0.1, 0.5]], "median": [[0.2, 0.6]], "high": [[0.3, 0.7]]})
    for bad in (
        dict(class_index=[[0, 2]]),
        dict(class_index=[[0, -2]]),
        dict(features={"low": [[0.1, 0.5]], "high": [[0.3, 0.7]]}),
        dict(features={**good["features"], "high": [[0.3]]}),
    ):
        try:
            VegetationMap(**{**good, **bad})
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
    v = _example()
    for args in (({"grass": 0.3}, 0.5), ({"grass": 0.3, "tree": 0.0}, 0.5), ({"grass": 0.3, "tree": 1.0}, 0.0)):
        try:
            v.compute_root_depth(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {args}")


def t():
    t1()
    t2()
