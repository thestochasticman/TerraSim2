import numpy as np

from terrasim2.f.classify_soil_texture import classify_soil_texture
from terrasim2.f.compute_geometric_mean_diameter import compute_geometric_mean_diameter
from terrasim2.f.estimate_campbell_params import estimate_campbell_params
from terrasim2.f.lookup_typical_fractions import lookup_typical_fractions
from terrasim2.k.soil_texture import SoilTexture


def compute_texture_triangle(step: int = 1) -> dict:
    """The USDA texture triangle sampled on a grid, in the visualiser's JSON shape.

    Every composition with sand, silt and clay on multiples of ``step``
    percent, classified and given the book's particle-size estimates.

    Parameters
    ----------
    step : int, percent
        Grid spacing; 1 gives 5151 points.

    Returns
    -------
    dict
        ``textures`` : the twelve classes, coarsest first.
        ``step`` : the spacing, percent.
        ``points`` : columns ``sand``, ``silt``, ``clay`` (percent),
        ``texture`` (index into textures), ``diameter`` (geometric mean,
        micrometres), ``psi_e`` (J kg-1) and ``b`` (dimensionless) from
        eqs. 2.36, 5.36 and 5.37.
        ``typical`` : table 2.4, one record per class with ``texture``,
        ``sand``, ``silt``, ``clay`` (percent) and ``diameter``.
    """
    if step < 1 or 100 % step:
        raise ValueError("step must be a positive divisor of 100")
    pts = [(s, si, 100 - s - si) for s in range(0, 101, step) for si in range(0, 101 - s, step)]
    sand, silt, clay = (np.array(col, dtype=np.float64) for col in zip(*pts))
    fractions = (sand / 100, silt / 100, clay / 100)
    texture = classify_soil_texture(*fractions)
    diameter = compute_geometric_mean_diameter(*fractions)
    params = estimate_campbell_params(diameter, 0.5)
    typical = []
    for tex in SoilTexture:
        fs = lookup_typical_fractions(tex)
        typical.append({"texture": str(tex), "sand": 100 * fs[0], "silt": 100 * fs[1], "clay": 100 * fs[2], "diameter": float(compute_geometric_mean_diameter(*fs))})
    return {
        "textures": [str(tex) for tex in SoilTexture],
        "step": step,
        "points": {
            "sand": sand.tolist(),
            "silt": silt.tolist(),
            "clay": clay.tolist(),
            "texture": texture.tolist(),
            "diameter": diameter.tolist(),
            "psi_e": np.asarray(params.psi_e).tolist(),
            "b": np.asarray(params.b).tolist(),
        },
        "typical": typical,
    }


def t():
    """The grid covers the triangle once, every class appears, the columns line up, and the output serialises."""
    import json

    out = compute_texture_triangle(step=5)
    n = len(out["points"]["sand"])
    assert n == 231 and all(len(out["points"][k]) == n for k in ("silt", "clay", "texture", "diameter", "psi_e", "b"))
    assert set(out["points"]["texture"]) == set(range(12)) and len(out["textures"]) == 12
    assert all(abs(s + si + c - 100) < 1e-9 for s, si, c in zip(out["points"]["sand"], out["points"]["silt"], out["points"]["clay"]))
    assert len(out["typical"]) == 12 and out["typical"][0]["texture"] == "sand" and abs(out["typical"][0]["diameter"] - 211.75) < 0.05
    assert all(p < 0 for p in out["points"]["psi_e"]) and all(b > 0 for b in out["points"]["b"])
    assert len(compute_texture_triangle(step=1)["points"]["sand"]) == 5151
    json.dumps(out)
    try:
        compute_texture_triangle(step=3)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for a step that does not divide 100")
