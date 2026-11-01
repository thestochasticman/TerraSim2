import numpy as np

from terrasim2.f.compute_available_water import compute_available_water
from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
from terrasim2.f.compute_van_genuchten_water_content import compute_van_genuchten_water_content
from terrasim2.f.lookup_campbell_params import lookup_campbell_params
from terrasim2.f.lookup_van_genuchten_params import lookup_van_genuchten_params
from terrasim2.k.soil_texture import SoilTexture

FIELD_CAPACITY = -33.0
WILTING_POINT = -1500.0

_CURVES = {
    "campbell": (compute_campbell_water_content, lookup_campbell_params),
    "van_genuchten": (compute_van_genuchten_water_content, lookup_van_genuchten_params),
}


def compute_retention_curves(n_points: int = 200, suction_min: float = 0.1, suction_max: float = 1e6) -> dict:
    """The book's retention curves for every texture, in the visualiser's JSON shape.

    Parameters
    ----------
    n_points : int, dimensionless
        Number of suctions sampled, evenly spaced in log10.
    suction_min, suction_max : float, J kg-1
        Range of suction (the absolute value of matric potential) sampled.

    Returns
    -------
    dict
        ``suction`` : list, J kg-1, ascending.
        ``field_capacity``, ``wilting_point`` : suctions, J kg-1, positive.
        ``models`` : model name -> list of one record per texture, coarsest
        first, each with ``texture``, ``theta`` (m3 m-3 per suction),
        ``theta_fc`` and ``theta_pwp`` (m3 m-3 at field capacity and wilting
        point) and ``available_water`` (mm per metre of soil between them).
    """
    suction = np.logspace(np.log10(suction_min), np.log10(suction_max), n_points)
    psi = -suction
    models: dict[str, list[dict]] = {}
    for model, (curve, lookup) in _CURVES.items():
        records = []
        for tex in SoilTexture:
            params = lookup(tex)
            records.append({
                "texture": str(tex),
                "theta": curve(psi, params).tolist(),
                "theta_fc": float(curve(FIELD_CAPACITY, params)),
                "theta_pwp": float(curve(WILTING_POINT, params)),
                "available_water": float(compute_available_water(curve, params, 1.0, FIELD_CAPACITY, WILTING_POINT)),
            })
        models[model] = records
    return {
        "suction": suction.tolist(),
        "field_capacity": -FIELD_CAPACITY,
        "wilting_point": -WILTING_POINT,
        "models": models,
    }

def t():
    """Both models, twelve textures coarsest first, one value per suction, monotone, serialisable, and
    the per-texture numbers agree with calling the terrasim2 functions directly."""
    import json

    out = compute_retention_curves(n_points=50)
    assert len(out["suction"]) == 50 and out["suction"][0] == 0.1 and abs(out["suction"][-1] - 1e6) < 1e-6
    assert out["field_capacity"] == 33.0 and out["wilting_point"] == 1500.0
    for model in ("campbell", "van_genuchten"):
        records = out["models"][model]
        assert [r["texture"] for r in records] == [str(tex) for tex in SoilTexture]
        for r in records:
            theta = r["theta"]
            assert len(theta) == 50 and all(b <= a for a, b in zip(theta, theta[1:])), (model, r["texture"])
            assert r["theta_pwp"] < r["theta_fc"] <= theta[0]
            assert abs(r["available_water"] - 1000 * (r["theta_fc"] - r["theta_pwp"])) < 1e-9
        assert records[0]["available_water"] < records[-1]["available_water"]
    loam = next(r for r in out["models"]["campbell"] if r["texture"] == "loam")
    direct = compute_available_water(compute_campbell_water_content, lookup_campbell_params("loam"), 1.0)
    assert abs(loam["available_water"] - float(direct)) < 1e-9
    json.dumps(out)
