from collections.abc import Callable

import numpy as np


def compute_available_water(
    compute_water_content: Callable[[np.ndarray | float, object], np.ndarray],
    params: object,
    root_depth: np.ndarray | float,
    psi_fc: float = -33.0,
    psi_pwp: float = -1500.0,
) -> np.ndarray:
    """Plant-available water of a soil column, as a depth of water.

    Field capacity minus permanent wilting point, each read off the soil's
    retention curve, times the depth of soil the roots reach. This is the
    definition in exercise 5.6 of Bittelli, Campbell and Tomei (2015) and
    is the quantity ``TerrainGrid.capacity`` stands for.

    Parameters
    ----------
    compute_water_content : callable
        A retention curve, ``(psi, params) -> theta``, such as
        ``compute_campbell_water_content`` or
        ``compute_van_genuchten_water_content``.
    params : object
        The parameters that curve takes.
    root_depth : ndarray or float, m
        Depth of soil the plants draw on. Positive. Any shape; the result
        has the same shape.
    psi_fc : float, J kg-1
        Matric potential taken as field capacity. Default -33.
    psi_pwp : float, J kg-1
        Matric potential taken as permanent wilting point. Default -1500.
        Must be drier (more negative) than psi_fc.

    Returns
    -------
    ndarray, mm
        Water the column can hold between wilting point and field
        capacity, same shape as ``root_depth``.
    """
    if not psi_pwp < psi_fc:
        raise ValueError(f"wilting point {psi_pwp} must be more negative than field capacity {psi_fc}")
    root_depth = np.asarray(root_depth, dtype=np.float64)
    if not np.all(root_depth > 0):
        raise ValueError("root_depth must be positive")
    theta_fc = compute_water_content(psi_fc, params)
    theta_pwp = compute_water_content(psi_pwp, params)
    return (theta_fc - theta_pwp) * root_depth * 1000.0


def t1():
    """Exercise 5.6: the van Genuchten soil holds 0.1823 m3/m3 between field capacity and wilting
    point, so one metre of it holds about 182 mm, and half a metre half that."""
    from terrasim2.f.compute_van_genuchten_water_content import compute_van_genuchten_water_content
    from terrasim2.k.van_genuchten_params import VanGenuchtenParams

    p = VanGenuchtenParams(theta_s=0.46, theta_r=0.01, alpha=0.15, n=1.35)
    one = compute_available_water(compute_van_genuchten_water_content, p, 1.0)
    assert one.shape == () and abs(float(one) - 182.3) < 0.5
    assert np.isclose(compute_available_water(compute_van_genuchten_water_content, p, 0.5), one / 2)


def t2():
    """A hand-computed Campbell case: theta_s 0.4, air entry -1, b 1 gives 0.4/33 at field capacity and
    0.4/1500 at wilting point; over 2 m that is about 23.7 mm. Depth may be an array."""
    from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
    from terrasim2.k.campbell_params import CampbellParams

    p = CampbellParams(theta_s=0.4, psi_e=-1.0, b=1.0)
    expected = (0.4 / 33 - 0.4 / 1500) * 2 * 1000
    out = compute_available_water(compute_campbell_water_content, p, np.array([[2.0, 1.0]]))
    assert out.shape == (1, 2)
    assert np.isclose(out[0, 0], expected) and np.isclose(out[0, 1], expected / 2)


def t3():
    """With both tables, sand holds least and the three coarsest classes hold less than every finer one."""
    from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
    from terrasim2.f.compute_van_genuchten_water_content import compute_van_genuchten_water_content
    from terrasim2.f.lookup_campbell_params import lookup_campbell_params
    from terrasim2.f.lookup_van_genuchten_params import lookup_van_genuchten_params
    from terrasim2.k.soil_texture import SoilTexture

    coarse = (SoilTexture.SAND, SoilTexture.LOAMY_SAND, SoilTexture.SANDY_LOAM)
    for curve, lookup in ((compute_campbell_water_content, lookup_campbell_params), (compute_van_genuchten_water_content, lookup_van_genuchten_params)):
        mm = {tex: float(compute_available_water(curve, lookup(tex), 1.0)) for tex in SoilTexture}
        assert mm[SoilTexture.SAND] < mm[SoilTexture.LOAMY_SAND] < mm[SoilTexture.SANDY_LOAM]
        assert mm[SoilTexture.SANDY_LOAM] < min(v for k, v in mm.items() if k not in coarse)
        assert 30 < mm[SoilTexture.SAND] < 40 and 140 < mm[SoilTexture.CLAY] < 150


def t4():
    """A wilting point wetter than field capacity, or a non-positive depth, is refused."""
    from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
    from terrasim2.k.campbell_params import CampbellParams

    p = CampbellParams(theta_s=0.4, psi_e=-1.0, b=2.0)
    for kwargs in (dict(root_depth=1.0, psi_fc=-1500.0, psi_pwp=-33.0), dict(root_depth=0.0), dict(root_depth=np.array([1.0, -0.5]))):
        try:
            compute_available_water(compute_campbell_water_content, p, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {kwargs}")


def t():
    t1()
    t2()
    t3()
    t4()
