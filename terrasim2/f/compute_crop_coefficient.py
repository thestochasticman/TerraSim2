import numpy as np


def compute_crop_coefficient(ndvi: np.ndarray, ndvi_bare: float = 0.1, ndvi_full: float = 0.7, kc_bare: float = 0.3, kc_full: float = 1.1) -> np.ndarray:
    """How much of the reference evapotranspiration a cell's cover demands, from its greenness.

    FAO-56's crop coefficient read off NDVI, the linear map between bare
    ground and a full canopy that TerraSim's first version used: cover
    rises from 0 at ``ndvi_bare`` to 1 at ``ndvi_full``, and the
    coefficient from ``kc_bare`` to ``kc_full`` with it. Fed the greenness
    a cell keeps through its brownest season, it says which cells go on
    transpiring when the pattern is set.

    Parameters
    ----------
    ndvi : ndarray, dimensionless
        Any shape; NaN where unseen.
    ndvi_bare, ndvi_full : float, dimensionless
        The greenness of bare ground and of a closed canopy, ``ndvi_bare < ndvi_full``.
    kc_bare, kc_full : float, dimensionless
        The coefficient at those two, ``0 < kc_bare <= kc_full``.

    Returns
    -------
    ndarray, dimensionless
        The same shape, within [kc_bare, kc_full]; NaN where ``ndvi`` is.
    """
    if not ndvi_bare < ndvi_full:
        raise ValueError(f"ndvi_bare {ndvi_bare} must be below ndvi_full {ndvi_full}")
    if not 0 < kc_bare <= kc_full:
        raise ValueError(f"need 0 < kc_bare <= kc_full, got {kc_bare} and {kc_full}")
    ndvi = np.asarray(ndvi, dtype=np.float64)
    cover = np.clip((ndvi - ndvi_bare) / (ndvi_full - ndvi_bare), 0.0, 1.0)
    return kc_bare + (kc_full - kc_bare) * cover


def t():
    """Bare ground and below give the floor, a closed canopy and above the ceiling, halfway lies halfway; NaN passes
    through; bad limits are refused."""
    out = compute_crop_coefficient(np.array([[0.0, 0.1, 0.4, 0.7, 0.9, np.nan]]))
    assert out.shape == (1, 6)
    assert np.allclose(out[0, :5], [0.3, 0.3, 0.7, 1.1, 1.1]) and np.isnan(out[0, 5])
    assert np.isclose(compute_crop_coefficient(0.55, ndvi_bare=0.1, ndvi_full=1.0, kc_bare=0.2, kc_full=1.2), 0.7)
    for bad in (dict(ndvi_bare=0.7, ndvi_full=0.1), dict(kc_bare=0.0), dict(kc_bare=1.2, kc_full=1.1)):
        try:
            compute_crop_coefficient(np.array([0.5]), **bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
