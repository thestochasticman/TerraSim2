import numpy as np

from terrasim2.f.classify_soil_texture import classify_soil_texture
from terrasim2.f.compute_available_fraction import compute_available_fraction
from terrasim2.f.compute_campbell_water_content import compute_campbell_water_content
from terrasim2.f.compute_geometric_mean_diameter import compute_geometric_mean_diameter
from terrasim2.f.estimate_campbell_params import estimate_campbell_params
from terrasim2.k.soil_conventions import SoilConventions

PARTICLE_DENSITY = 2650.0


def prepare_soil_layer(sand: np.ndarray, silt: np.ndarray, clay: np.ndarray, bulk_density: np.ndarray, conventions: SoilConventions = SoilConventions()) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One soil layer's available water, texture and Campbell curve from measured properties.

    The book's continuous route: the three fractions give a geometric mean
    diameter (eq. 2.36), which gives Campbell's air entry and b (eqs. 5.36
    and 5.37); the saturated content is the porosity ``1 - bulk_density /
    2650``; the available fraction is the curve's content at the
    conventions' field capacity minus that at their wilting point. The
    textural class is the USDA triangle's.

    Parameters
    ----------
    sand, silt, clay : ndarray, dimensionless
        Mass fractions in [0, 1], any common shape; normalised to sum to
        one. NaN where unknown.
    bulk_density : ndarray, kg m-3
        Dry bulk density, same shape. NaN where unknown.
    conventions : SoilConventions
        Where on the curve field capacity and wilting point are read.

    Returns
    -------
    available_fraction : ndarray, m3 m-3
        NaN wherever any input is NaN or the porosity is not in (0, 1).
    texture_index : ndarray of int, dimensionless
        Index into ``list(SoilTexture)``; -1 where the fractions are unknown.
    campbell : ndarray
        Shape (3, ...): ``theta_s`` (m3 m-3), ``psi_e`` (J kg-1) and ``b``
        (dimensionless) of each cell's curve, NaN where unknown.
    """
    sand, silt, clay, bulk_density = (np.asarray(v, dtype=np.float64) for v in (sand, silt, clay, bulk_density))
    total = sand + silt + clay
    known = np.isfinite(total) & (total > 0)
    fractions = [np.where(known, v / np.where(known, total, 1.0), np.nan) for v in (sand, silt, clay)]

    texture = np.full(sand.shape, -1, dtype=np.int8)
    if np.any(known):
        texture[known] = classify_soil_texture(*(f[known] for f in fractions))

    theta_s = 1.0 - bulk_density / PARTICLE_DENSITY
    usable = known & np.isfinite(theta_s) & (theta_s > 0) & (theta_s < 1)
    available = np.full(sand.shape, np.nan, dtype=np.float64)
    campbell = np.full((3, *sand.shape), np.nan, dtype=np.float64)
    if np.any(usable):
        diameter = compute_geometric_mean_diameter(*(f[usable] for f in fractions))
        params = estimate_campbell_params(diameter, theta_s[usable])
        available[usable] = compute_available_fraction(compute_campbell_water_content, params, conventions.field_capacity_suction, conventions.wilting_point_suction)
        campbell[0][usable], campbell[1][usable], campbell[2][usable] = params.theta_s, params.psi_e, params.b
    return available, texture, campbell


def t1():
    """Table 2.4's sand and clay at a bulk density of 1400 kg/m3: sand holds far less; classes come out right."""
    sand = np.array([0.92, 0.20])
    silt = np.array([0.05, 0.20])
    clay = np.array([0.03, 0.60])
    available, texture, campbell = prepare_soil_layer(sand, silt, clay, np.array([1400.0, 1400.0]))
    assert texture.tolist() == [0, 11]
    assert campbell.shape == (3, 2) and np.allclose(campbell[0], 1 - 1400 / 2650)
    assert campbell[1, 0] > campbell[1, 1] and campbell[2, 0] < campbell[2, 1], "sand: wetter air entry, smaller b"
    assert 0.03 < available[0] < 0.12 and 0.15 < available[1] < 0.35
    assert available[0] < available[1] / 2
    book, _, _ = prepare_soil_layer(sand, silt, clay, np.array([1400.0, 1400.0]), SoilConventions(-33.0, -1500.0))
    assert np.all(book < available), "the book's narrower limits hold less"
    assert 0.01 < book[0] < 0.06 and 0.10 < book[1] < 0.25


def t2():
    """Percent-like inputs that do not quite sum to one are normalised; NaN inputs give NaN and -1; a bulk
    density that leaves no porosity gives NaN but still a class."""
    available, texture, campbell = prepare_soil_layer(np.array([0.41, np.nan, 0.41]), np.array([0.41, 0.3, 0.41]), np.array([0.20, 0.3, 0.20]), np.array([1300.0, 1300.0, 2700.0]))
    assert texture.tolist() == [4, -1, 4]
    assert np.isfinite(available[0]) and np.isnan(available[1]) and np.isnan(available[2])
    assert np.isfinite(campbell[:, 0]).all() and np.isnan(campbell[:, 1:]).all()


def t3():
    """Shapes are kept and an all-NaN layer is handled."""
    shape = (2, 3)
    available, texture, campbell = prepare_soil_layer(np.full(shape, np.nan), np.full(shape, np.nan), np.full(shape, np.nan), np.full(shape, np.nan))
    assert available.shape == shape and texture.shape == shape and campbell.shape == (3, *shape)
    assert np.isnan(available).all() and np.all(texture == -1)


def t():
    t1()
    t2()
    t3()
