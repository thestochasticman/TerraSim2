import numpy as np

from terrasim2.k.vegetation_thresholds import VegetationThresholds

# The classes a cell can take, in index order; -1 is unknown.
VEGETATION_CLASSES = ("grass", "tree")
GRASS, TREE, UNKNOWN = 0, 1, -1


def classify_vegetation(low: np.ndarray, high: np.ndarray, thresholds: VegetationThresholds = VegetationThresholds()) -> np.ndarray:
    """Tree or grass per cell from a year's NDVI low and high.

    A cell is a tree where its low NDVI is at least ``tree_low_min`` and
    its swing, high minus low, is at most ``tree_amplitude_max``: a canopy
    that stays. Everything else is grass, which here means any cover that
    comes and goes, crops and bare ground included. A cell with no
    statistics is unknown.

    Parameters
    ----------
    low, high : ndarray, dimensionless
        The 10th and 90th percentiles of NDVI over a year, any one shape;
        NaN where unseen.
    thresholds : VegetationThresholds

    Returns
    -------
    ndarray of int8, dimensionless
        Index into ``VEGETATION_CLASSES``: 0 grass, 1 tree; -1 unknown.
    """
    low = np.asarray(low, dtype=np.float64)
    high = np.asarray(high, dtype=np.float64)
    if low.shape != high.shape:
        raise ValueError(f"low {low.shape} and high {high.shape} must have one shape")
    known = np.isfinite(low) & np.isfinite(high)
    tree = known & (low >= thresholds.tree_low_min) & (high - low <= thresholds.tree_amplitude_max)
    out = np.full(low.shape, GRASS, dtype=np.int8)
    out[tree] = TREE
    out[~known] = UNKNOWN
    return out


def t():
    """A steady green cell is a tree, a browning one grass, a swinging but green one grass, an unseen one unknown;
    thresholds move the boundary; a shape mismatch is refused."""
    low = np.array([[0.6, 0.2, 0.5, np.nan], [0.45, 0.35, 0.7, 0.9]])
    high = np.array([[0.75, 0.8, 0.9, 0.5], [0.6, 0.5, 0.7, np.nan]])
    out = classify_vegetation(low, high)
    assert out.dtype == np.int8
    assert out.tolist() == [[TREE, GRASS, GRASS, UNKNOWN], [TREE, GRASS, TREE, UNKNOWN]]
    strict = classify_vegetation(low, high, VegetationThresholds(tree_low_min=0.5, tree_amplitude_max=0.1))
    assert strict.tolist() == [[GRASS, GRASS, GRASS, UNKNOWN], [GRASS, GRASS, TREE, UNKNOWN]]
    loose = classify_vegetation(low, high, VegetationThresholds(tree_low_min=0.3, tree_amplitude_max=0.35))
    assert loose.tolist() == [[TREE, GRASS, GRASS, UNKNOWN], [TREE, TREE, TREE, UNKNOWN]]
    assert VEGETATION_CLASSES[TREE] == "tree" and VEGETATION_CLASSES[GRASS] == "grass"
    try:
        classify_vegetation(low, high[:, :3])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
