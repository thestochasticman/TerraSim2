import numpy as np

from terrasim2.k.soil_hydraulics import SoilHydraulics


def compute_water_content(moisture: np.ndarray, soil_hydraulics: SoilHydraulics) -> np.ndarray:
    """The volumetric water content a cell's stored water amounts to over the root depth.

    Every step holds water as millimetres above wilting point: the bucket
    steps up to field capacity, the subsurface step up to saturation. The
    content a probe would read over the root zone is then::

        theta = theta_wp + moisture / (root_depth * 1000)

    which is what an observation of volumetric water content can be
    compared with.

    Parameters
    ----------
    moisture : ndarray, millimetres (mm)
        Stored water per cell, shape (rows, cols) or (T, rows, cols).
    soil_hydraulics : SoilHydraulics
        Needs ``theta_wp`` and the root depth.

    Returns
    -------
    ndarray, m3 m-3
        The same shape as ``moisture``. NaN where the soil is unknown.
    """
    soil_hydraulics.require_conductivity("compute_water_content")
    moisture = np.asarray(moisture, dtype=np.float64)
    if moisture.shape[-2:] != soil_hydraulics.shape:
        raise ValueError(f"moisture must end in the soil's shape {soil_hydraulics.shape}, got {moisture.shape}")
    return soil_hydraulics.theta_wp + moisture / (soil_hydraulics.root_depth * 1000.0)


def _hydraulics() -> SoilHydraulics:
    shape = (2, 3)
    full = lambda v: np.full(shape, v, dtype=float)  # noqa: E731
    return SoilHydraulics(full(45.0), 0.3, full(7e-4), full(3.0), full(0.45), full(0.25), full(0.10))


def t1():
    """Empty reads wilting point, the plant store full reads field capacity, the free store full reads saturation."""
    h = _hydraulics()
    assert np.allclose(compute_water_content(np.zeros((2, 3)), h), 0.10)
    assert np.allclose(compute_water_content(np.full((2, 3), 45.0), h), 0.25)
    assert np.allclose(compute_water_content(np.full((2, 3), 45.0 + 60.0), h), 0.45)
    history = np.stack([np.zeros((2, 3)), np.full((2, 3), 15.0)])
    theta = compute_water_content(history, h)
    assert theta.shape == (2, 2, 3) and np.allclose(theta[1], 0.15)


def t2():
    """Hydraulics without a curve are refused naming the function, and a wrong shape is refused."""
    try:
        compute_water_content(np.zeros((2, 3)), SoilHydraulics(np.full((2, 3), 45.0), 0.3))
    except ValueError as err:
        assert "compute_water_content" in str(err)
    else:
        raise AssertionError("expected ValueError without a curve")
    try:
        compute_water_content(np.zeros((3, 2)), _hydraulics())
    except ValueError as err:
        assert "shape" in str(err)
    else:
        raise AssertionError("expected ValueError for a wrong shape")


def t():
    t1()
    t2()
