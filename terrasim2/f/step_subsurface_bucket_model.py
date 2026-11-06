import numpy as np

from terrasim2.f.compute_campbell_conductivity import compute_campbell_conductivity
from terrasim2.f.compute_flow_direction import NO_OUTLET
from terrasim2.k.bucket_model_params import BucketModelParams
from terrasim2.k.soil_hydraulics import SoilHydraulics
from terrasim2.k.subsurface_bucket_flux import SubsurfaceBucketFlux
from terrasim2.k.terrain_derivatives import TerrainDerivatives

GRAVITY = 9.81
SECONDS_PER_DAY = 86400.0


def step_subsurface_bucket_model(
    moisture: np.ndarray,
    soil_hydraulics: SoilHydraulics,
    rain: np.ndarray,
    pet: np.ndarray,
    terrain_derivatives: TerrainDerivatives,
    params: BucketModelParams,
) -> tuple[np.ndarray, np.ndarray]:
    """One day of buckets that drain downslope through the soil and overflow downhill.

    Each cell is a store of size ``capacity`` whose water content runs
    from wilting point when empty to field capacity when full. In order:

    1. Rain fills the room left in each store. What does not fit is excess.
    2. Each cell drains to the cell it flows to, by Darcy's law along the
       slope with gravity as the driver (the kinematic approximation:
       matric gradients between cells are ignored)::

           drainage = K(theta) * g * slope * root_depth / cell_size * seconds_per_day

       in mm per day, where ``K(theta)`` is the Campbell conductivity at
       the cell's content after rain (eq. 6.35). Drainage is taken from
       the start-of-day state and capped at what the store holds.
    3. Excess and drainage cascade: walking the cells from the ridges
       down, each cell receives what its upslope neighbours sent, keeps
       what room it has, and passes the rest on as surface excess. Water
       reaching an outlet leaves the grid as runoff, whether it arrived
       over the surface or through the soil.
    4. Evaporation takes ``pet * (fullness ** stress_exponent)``, capped at
       what the store holds.

    Per cell, ``new - old == infiltration + inflow - drainage - evaporation``.
    Over the grid, excess plus drainage equals inflow plus runoff.

    Parameters
    ----------
    moisture : ndarray (rows, cols), millimetres (mm)
        Store contents at the start of the day, in [0, capacity].
    soil_hydraulics : SoilHydraulics
        Needs the conductivity fields and the root depth.
    rain : ndarray (rows, cols), millimetres (mm)
        Rain arriving during the day, non-negative.
    pet : ndarray (rows, cols), millimetres (mm)
        Reference evapotranspiration demand for the day, non-negative.
    terrain_derivatives : TerrainDerivatives
        Reads ``downstream``, ``order``, ``slope`` and the grid's cell size.
    params : BucketModelParams

    Returns
    -------
    moisture : ndarray (rows, cols), mm
        Store contents at the end of the day.
    fluxes : ndarray (5, rows, cols), mm
        Indexed by ``SubsurfaceBucketFlux``.
    """
    soil_hydraulics.require_conductivity("step_subsurface_bucket_model")
    capacity = soil_hydraulics.capacity
    room = capacity - moisture
    infiltration = np.minimum(rain, room)
    excess = (rain - infiltration).ravel()
    wet = moisture + infiltration

    with np.errstate(divide="ignore", invalid="ignore"):
        fullness = np.where(capacity > 0, wet / capacity, 0.0)
    theta = soil_hydraulics.theta_wp + fullness * (soil_hydraulics.theta_fc - soil_hydraulics.theta_wp)
    conductivity = compute_campbell_conductivity(np.nan_to_num(theta), np.nan_to_num(soil_hydraulics.theta_s, nan=1.0), np.nan_to_num(soil_hydraulics.b, nan=1.0), np.nan_to_num(soil_hydraulics.k_sat))
    rate = conductivity * GRAVITY * terrain_derivatives.slope * soil_hydraulics.root_depth / terrain_derivatives.grid.cell_size * SECONDS_PER_DAY
    drainage = np.minimum(rate, wet)

    wet = (wet - drainage).ravel()
    room = capacity.ravel() - wet
    sent = excess + drainage.ravel()
    inflow = np.zeros_like(wet)
    arriving = np.zeros_like(wet)
    runoff = np.zeros_like(wet)
    downstream = terrain_derivatives.downstream.ravel()

    for cell in terrain_derivatives.order:
        taken = min(arriving[cell], room[cell])
        inflow[cell] = taken
        passing = sent[cell] + arriving[cell] - taken
        target = downstream[cell]
        if target == NO_OUTLET:
            runoff[cell] = passing
        else:
            arriving[target] += passing

    wet = (wet + inflow).reshape(moisture.shape)
    with np.errstate(divide="ignore", invalid="ignore"):
        fullness = np.where(capacity > 0, wet / capacity, 0.0)
    evaporation = np.minimum(pet * fullness**params.stress_exponent, wet)

    fluxes = np.empty((len(SubsurfaceBucketFlux), *moisture.shape), dtype=np.float64)
    fluxes[SubsurfaceBucketFlux.INFILTRATION] = infiltration
    fluxes[SubsurfaceBucketFlux.INFLOW] = inflow.reshape(moisture.shape)
    fluxes[SubsurfaceBucketFlux.DRAINAGE] = drainage
    fluxes[SubsurfaceBucketFlux.RUNOFF] = runoff.reshape(moisture.shape)
    fluxes[SubsurfaceBucketFlux.EVAPORATION] = evaporation
    return wet - evaporation, fluxes


def _derivatives(elevation, cell_size=10.0) -> TerrainDerivatives:
    from terrasim2.k.terrain_grid import TerrainGrid

    return TerrainDerivatives(TerrainGrid(elevation=np.asarray(elevation, dtype=float), cell_size=cell_size))


def _hydraulics(shape, capacity=30.0, k_sat=7.2e-4, b=3.0, theta_s=0.45, theta_fc=0.25, theta_wp=0.10, root_depth=0.3) -> SoilHydraulics:
    full = lambda v: np.full(shape, v, dtype=float)  # noqa: E731
    return SoilHydraulics(full(capacity), root_depth, full(k_sat), full(b), full(theta_s), full(theta_fc), full(theta_wp))


def t1():
    """Three full cells down a 10 percent slope, no rain: each drains the hand-computed Darcy amount at the
    conductivity of field capacity, the foot's drainage leaves as runoff, and water arriving from above
    refills what the cell below lost. A full bucket sits at field capacity, where Campbell's conductivity
    is (theta_fc / theta_s) ** (2 b + 3) of saturated, here half a percent: 0.009 mm a day, not the
    1.8 mm a saturated cell would pass. That is the finding behind the free store that follows."""
    z = [[2.0, 1.0, 0.0]]
    h = _hydraulics((1, 3))
    moisture = np.full((1, 3), 30.0)
    d = _derivatives(z)
    new, f = step_subsurface_bucket_model(moisture, h, np.zeros((1, 3)), np.zeros((1, 3)), d, BucketModelParams())
    saturated = 7.2e-4 * 9.81 * 0.1 * 0.3 / 10.0 * 86400
    assert abs(saturated - 1.831) < 0.001, "what a saturated cell would pass"
    expected = saturated * (0.25 / 0.45) ** 9
    assert abs(expected - 0.00923) < 0.0001
    assert np.allclose(f[SubsurfaceBucketFlux.DRAINAGE][0, :2], expected)
    assert f[SubsurfaceBucketFlux.DRAINAGE][0, 2] == 0.0, "the outlet cell has no slope of its own"
    assert np.allclose(f[SubsurfaceBucketFlux.INFLOW], [[0.0, expected, 0.0]]), "the full foot cannot take what arrives"
    assert np.allclose(f[SubsurfaceBucketFlux.RUNOFF], [[0.0, 0.0, expected]]), "so it leaves the grid there"
    assert np.allclose(new, [[30.0 - expected, 30.0, 30.0]])


def t2():
    """Flat ground does not drain; a dry slope hardly drains; a full store drains K_s worth and an empty one nothing."""
    h = _hydraulics((1, 3))
    rain = np.zeros((1, 3))
    _, flat = step_subsurface_bucket_model(np.full((1, 3), 30.0), h, rain, rain, _derivatives([[1.0, 1.0, 1.0]]), BucketModelParams())
    assert np.all(flat[SubsurfaceBucketFlux.DRAINAGE] == 0.0)
    d = _derivatives([[2.0, 1.0, 0.0]])
    _, dry = step_subsurface_bucket_model(np.full((1, 3), 3.0), h, rain, rain, d, BucketModelParams())
    _, wet = step_subsurface_bucket_model(np.full((1, 3), 30.0), h, rain, rain, d, BucketModelParams())
    assert dry[SubsurfaceBucketFlux.DRAINAGE][0, 0] < 0.01 * wet[SubsurfaceBucketFlux.DRAINAGE][0, 0]
    _, empty = step_subsurface_bucket_model(np.zeros((1, 3)), h, rain, rain, d, BucketModelParams())
    assert np.all(empty[SubsurfaceBucketFlux.DRAINAGE] == 0.0)


def t3():
    """Mass balance on a random hill with rain: per cell and over the grid, every flux non-negative, no store over capacity."""
    rng = np.random.default_rng(2)
    rows, cols = np.mgrid[0:20, 0:25]
    z = 30.0 - 0.4 * np.hypot(rows - 10, cols - 12) + rng.normal(0, 0.1, (20, 25))
    h = _hydraulics((20, 25), capacity=40.0)
    moisture = rng.uniform(0.5, 1.0, (20, 25)) * 40.0
    rain = np.full((20, 25), 12.0)
    pet = rng.uniform(0, 4, (20, 25))
    new, f = step_subsurface_bucket_model(moisture, h, rain, pet, _derivatives(z), BucketModelParams())
    assert f.shape == (5, 20, 25) and np.all(f >= 0)
    F = SubsurfaceBucketFlux
    per_cell = (new - moisture) - (f[F.INFILTRATION] + f[F.INFLOW] - f[F.DRAINAGE] - f[F.EVAPORATION])
    assert np.abs(per_cell).max() < 1e-9
    sent = (rain - f[F.INFILTRATION]).sum() + f[F.DRAINAGE].sum()
    assert abs(sent - f[F.INFLOW].sum() - f[F.RUNOFF].sum()) < 1e-6
    assert np.all(new >= -1e-12) and np.all(new <= 40.0 + 1e-9)
    assert f[F.RUNOFF][1:-1, 1:-1].sum() == 0.0


def t4():
    """Over a dry fortnight a slope at field capacity barely redistributes: with no store above field
    capacity, conductivity is too low for the foot to gain on the crest. The free store is what changes this."""
    rows, cols = np.mgrid[0:1, 0:12]
    z = 12.0 - cols.astype(float)
    d = _derivatives(z)
    h = _hydraulics((1, 12), capacity=30.0, k_sat=5e-3)
    moisture = np.full((1, 12), 30.0)
    rain = np.zeros((1, 12))
    pet = np.full((1, 12), 1.0)
    for _ in range(14):
        moisture, _ = step_subsurface_bucket_model(moisture, h, rain, pet, d, BucketModelParams())
    assert moisture[0, 0] <= moisture[0, 10], "what moves, moves downhill"
    assert moisture[0, 10] - moisture[0, 0] < 0.5, "but it is under half a millimetre in two weeks"


def t5():
    """Hydraulics without conductivity are refused with a message naming the step."""
    try:
        step_subsurface_bucket_model(np.zeros((1, 3)), SoilHydraulics(np.full((1, 3), 30.0)), np.zeros((1, 3)), np.zeros((1, 3)), _derivatives([[2.0, 1.0, 0.0]]), BucketModelParams())
    except ValueError as err:
        assert "step_subsurface_bucket_model" in str(err)
    else:
        raise AssertionError("expected ValueError")


def t():
    t1()
    t2()
    t3()
    t4()
    t5()
