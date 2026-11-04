import numpy as np

from terrasim2.k.soil_texture import SoilTexture

# How far the three fractions may stray from summing to one before the
# input is refused; data products round each fraction separately.
SUM_TOLERANCE = 0.02


def classify_soil_texture(sand: np.ndarray | float, silt: np.ndarray | float, clay: np.ndarray | float) -> np.ndarray:
    """USDA textural class of a soil from its sand, silt and clay fractions.

    The boundaries of the USDA texture triangle, applied in order so every
    composition falls in exactly one class. The fractions are normalised
    to sum to one before the rules are applied.

    Parameters
    ----------
    sand, silt, clay : ndarray or float, dimensionless
        Mass fractions in [0, 1], any common shape. Their sum must be
        within ``SUM_TOLERANCE`` of one.

    Returns
    -------
    ndarray of int, dimensionless
        Index into ``list(SoilTexture)``, same shape as the inputs.
    """
    sand, silt, clay = (np.asarray(v, dtype=np.float64) for v in (sand, silt, clay))
    for name, v in (("sand", sand), ("silt", silt), ("clay", clay)):
        if np.any((v < 0) | (v > 1)):
            raise ValueError(f"{name} fraction must be within [0, 1]")
    total = sand + silt + clay
    if np.any(np.abs(total - 1) > SUM_TOLERANCE):
        raise ValueError(f"fractions must sum to one within {SUM_TOLERANCE}")
    sa, si, cl = (100 * v / total for v in (sand, silt, clay))

    order = list(SoilTexture)
    rules = [
        (SoilTexture.SAND, si + 1.5 * cl < 15),
        (SoilTexture.LOAMY_SAND, (si + 1.5 * cl >= 15) & (si + 2 * cl < 30)),
        (SoilTexture.SANDY_LOAM, ((cl >= 7) & (cl < 20) & (sa > 52) & (si + 2 * cl >= 30)) | ((cl < 7) & (si < 50) & (si + 2 * cl >= 30))),
        (SoilTexture.LOAM, (cl >= 7) & (cl < 27) & (si >= 28) & (si < 50) & (sa <= 52)),
        (SoilTexture.SILT_LOAM, ((si >= 50) & (cl >= 12) & (cl < 27)) | ((si >= 50) & (si < 80) & (cl < 12))),
        (SoilTexture.SILT, (si >= 80) & (cl < 12)),
        (SoilTexture.SANDY_CLAY_LOAM, (cl >= 20) & (cl < 35) & (si < 28) & (sa > 45)),
        (SoilTexture.CLAY_LOAM, (cl >= 27) & (cl < 40) & (sa > 20) & (sa <= 45)),
        (SoilTexture.SILTY_CLAY_LOAM, (cl >= 27) & (cl < 40) & (sa <= 20)),
        (SoilTexture.SANDY_CLAY, (cl >= 35) & (sa > 45)),
        (SoilTexture.SILTY_CLAY, (cl >= 40) & (si >= 40)),
        (SoilTexture.CLAY, (cl >= 40) & (sa <= 45) & (si < 40)),
    ]
    out = np.select([mask for _, mask in rules], [order.index(tex) for tex, _ in rules], default=-1)
    if np.any(out < 0):
        raise AssertionError("a composition matched no class; the rules should partition the triangle")
    return out


def _name(index) -> SoilTexture:
    return list(SoilTexture)[int(index)]


def t1():
    """Hand-placed points land in the class the triangle shows for them."""
    cases = {
        (0.90, 0.05, 0.05): SoilTexture.SAND,
        (0.82, 0.10, 0.08): SoilTexture.LOAMY_SAND,
        (0.65, 0.25, 0.10): SoilTexture.SANDY_LOAM,
        (0.40, 0.40, 0.20): SoilTexture.LOAM,
        (0.20, 0.65, 0.15): SoilTexture.SILT_LOAM,
        (0.10, 0.85, 0.05): SoilTexture.SILT,
        (0.60, 0.10, 0.30): SoilTexture.SANDY_CLAY_LOAM,
        (0.35, 0.30, 0.35): SoilTexture.CLAY_LOAM,
        (0.10, 0.60, 0.30): SoilTexture.SILTY_CLAY_LOAM,
        (0.50, 0.10, 0.40): SoilTexture.SANDY_CLAY,
        (0.05, 0.50, 0.45): SoilTexture.SILTY_CLAY,
        (0.20, 0.20, 0.60): SoilTexture.CLAY,
    }
    for (sand, silt, clay), expected in cases.items():
        assert _name(classify_soil_texture(sand, silt, clay)) is expected, (sand, silt, clay)


def t2():
    """Every composition on a one-percent grid gets exactly one class, all twelve occur, and arrays keep their shape."""
    pts = [(s, si, 100 - s - si) for s in range(101) for si in range(101 - s)]
    sand, silt, clay = (np.array(v, dtype=float) / 100 for v in zip(*pts))
    out = classify_soil_texture(sand.reshape(-1, 1), silt.reshape(-1, 1), clay.reshape(-1, 1))
    assert out.shape == (len(pts), 1) and out.min() >= 0 and out.max() < 12
    assert set(np.unique(out)) == set(range(12))


def t3():
    """Table 2.4's typical compositions classify as their own class."""
    from terrasim2.f.lookup_typical_fractions import lookup_typical_fractions

    for expected in SoilTexture:
        assert _name(classify_soil_texture(*lookup_typical_fractions(expected))) is expected, expected


def t4():
    """Fractions outside [0, 1] or not summing to one are refused; a small rounding slack is normalised away."""
    for bad in ((1.2, 0.0, 0.0), (-0.1, 0.6, 0.5), (0.5, 0.3, 0.3), (0.3, 0.3, 0.3)):
        try:
            classify_soil_texture(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
    assert _name(classify_soil_texture(0.405, 0.405, 0.20)) is SoilTexture.LOAM


def t():
    t1()
    t2()
    t3()
    t4()
