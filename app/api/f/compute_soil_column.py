import numpy as np

from terrasim2.f.compute_available_fraction import compute_available_fraction
from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
from terrasim2.f.compute_capacity_map import compute_capacity_map
from terrasim2.f.compute_layer_thickness_in_depth import compute_layer_thickness_in_depth
from terrasim2.f.compute_van_genuchten_water_content import compute_van_genuchten_water_content
from terrasim2.f.lookup_campbell_params import lookup_campbell_params
from terrasim2.f.lookup_van_genuchten_params import lookup_van_genuchten_params
from terrasim2.k.soil_texture import SoilTexture

# The six standard depth intervals of the Soil and Landscape Grid of Australia, in metres.
LAYER_BOUNDS = np.array([0.0, 0.05, 0.15, 0.30, 0.60, 1.0, 2.0])

_CURVES = {
    "campbell": (compute_campbell_water_content, lookup_campbell_params),
    "van_genuchten": (compute_van_genuchten_water_content, lookup_van_genuchten_params),
}


def compute_soil_column(textures: list[str], root_depth: float, model: str = "campbell") -> dict:
    """Plant-available water of one layered soil column, layer by layer.

    Parameters
    ----------
    textures : list of str
        One textural class per layer of ``LAYER_BOUNDS``, top first.
    root_depth : float, m
        How deep the roots reach. Positive.
    model : str
        "campbell" or "van_genuchten": whose table gives each layer's curve.

    Returns
    -------
    dict
        ``textures`` : the twelve classes in ramp order.
        ``layer_bounds`` : m. ``root_depth`` : m. ``model``.
        ``layers`` : one record per layer with ``top``, ``bottom`` (m),
        ``texture``, ``fraction`` (m3 m-3 available), ``thickness_in_roots``
        (m) and ``mm`` (available water within the roots).
        ``total`` : mm, the sum over layers; what a cell's capacity would be.
    """
    n = LAYER_BOUNDS.size - 1
    if len(textures) != n:
        raise ValueError(f"need {n} textures, one per layer, got {len(textures)}")
    if model not in _CURVES:
        raise ValueError(f"model must be one of {sorted(_CURVES)}, got {model!r}")
    if not root_depth > 0:
        raise ValueError("root_depth must be positive")
    curve, lookup = _CURVES[model]
    fraction = np.array([float(compute_available_fraction(curve, lookup(tex))) for tex in textures])
    thickness = compute_layer_thickness_in_depth(LAYER_BOUNDS, root_depth)
    total = float(compute_capacity_map(fraction, LAYER_BOUNDS, root_depth))
    layers = [
        {
            "top": float(LAYER_BOUNDS[i]),
            "bottom": float(LAYER_BOUNDS[i + 1]),
            "texture": str(SoilTexture(textures[i])),
            "fraction": float(fraction[i]),
            "thickness_in_roots": float(thickness[i]),
            "mm": float(fraction[i] * thickness[i] * 1000),
        }
        for i in range(n)
    ]
    return {
        "textures": [str(tex) for tex in SoilTexture],
        "layer_bounds": LAYER_BOUNDS.tolist(),
        "root_depth": root_depth,
        "model": model,
        "layers": layers,
        "total": total,
    }


def t():
    """Per-layer mm sum to the total, roots cut the layer they end in, deeper layers give nothing, and bad
    inputs are refused."""
    import json

    out = compute_soil_column(["sand", "sand", "sand", "clay", "clay", "clay"], 0.4)
    assert len(out["layers"]) == 6 and out["model"] == "campbell"
    assert abs(sum(layer["mm"] for layer in out["layers"]) - out["total"]) < 1e-9
    assert np.allclose([layer["thickness_in_roots"] for layer in out["layers"]], [0.05, 0.10, 0.15, 0.10, 0.0, 0.0])
    assert out["layers"][3]["texture"] == "clay" and out["layers"][3]["mm"] > out["layers"][2]["mm"]
    assert out["layers"][5]["mm"] == 0.0
    json.dumps(out)
    deep = compute_soil_column(["clay"] * 6, 2.0, "van_genuchten")
    assert 280 < deep["total"] < 300
    for bad in (dict(textures=["sand"] * 5, root_depth=1.0), dict(textures=["peat"] + ["sand"] * 5, root_depth=1.0), dict(textures=["sand"] * 6, root_depth=0.0), dict(textures=["sand"] * 6, root_depth=1.0, model="rosetta")):
        try:
            compute_soil_column(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
