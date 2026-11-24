import numpy as np

from terrasim2.f.compute_campbell_conductivity import compute_campbell_conductivity
from terrasim2.f.compute_flow_direction import NO_OUTLET
from terrasim2.k.soil_hydraulics import SoilHydraulics
from terrasim2.k.subsurface_bucket_flux import SubsurfaceBucketFlux
from terrasim2.k.subsurface_bucket_params import SubsurfaceBucketParams
from terrasim2.k.terrain_derivatives import TerrainDerivatives

GRAVITY = 9.81
SECONDS_PER_DAY = 86400.0


def step_subsurface_bucket_model(
    moisture: np.ndarray,
    soil_hydraulics: SoilHydraulics,
    rain: np.ndarray,
    pet: np.ndarray,
    terrain_derivatives: TerrainDerivatives,
    params: SubsurfaceBucketParams,
) -> tuple[np.ndarray, np.ndarray]:
    """One day of buckets with a free store above field capacity that drains downslope.

    Each cell holds water up to saturation. The first ``capacity`` mm is
    the plant store, between wilting point and field capacity, which only
    evaporation empties. Above it is the free store, ``free_capacity`` mm
    of pore space between field capacity and saturation, which drains.
    ``moisture`` is their sum. In order:

    1. Rain infiltrates up to the room left and up to the day's
       infiltration limit, ``K_s * g * rain_hours``; the rest is excess
       on the surface.
    2. The free store drains by Darcy's law along the slope with gravity
       as the driver (the kinematic approximation), at Campbell's
       conductivity for the cell's content::

           lateral_flow = lateral_multiplier * K(theta) * g * slope * root_depth / cell_size * seconds_per_day

       and percolates straight down at ``K(theta) * g * percolation_fraction``.
       ``lateral_multiplier`` is the anisotropy of a real hillslope, where
       macropores and layer boundaries carry water along the slope many
       times faster than the matrix does; 1 is the matrix value. Both
       fluxes are taken from the start-of-day state and capped at the free
       water. The flow width is taken as one cell size whatever the
       direction; a diagonal neighbour's slope already uses the longer
       distance, so this overstates diagonal flow by at most sqrt(2).
    3. Excess and lateral flow cascade from the ridges down. Water arriving
       through the soil enters up to the room left; water arriving over
       the surface enters up to the room and the infiltration limit; the
       rest passes on over the surface, recorded as surface flow, and
       outlets shed it as runoff.
    4. Evaporation takes ``demand * (plant fullness ** stress_exponent)``,
       capped at what the cell holds, where the demand is ``pet`` scaled
       by the sun the cell's slope receives relative to flat ground,
       ``solar_ratio ** aspect_strength``; a strength of 0 leaves every
       cell at ``pet``.

    Per cell, ``new - old == infiltration + inflow - subsurface lateral flow
    - percolation - evaporation``. Over the grid, excess plus lateral flow
    equals inflow plus runoff. Surface flow is what passed between cells
    over the surface; it enters neither balance.

    Parameters
    ----------
    moisture : ndarray (rows, cols), millimetres (mm)
        Water at the start of the day, plant store plus free store, in
        [0, capacity + free_capacity].
    soil_hydraulics : SoilHydraulics
        Needs the conductivity fields and the root depth.
    rain : ndarray (rows, cols), millimetres (mm)
        Rain arriving during the day, non-negative.
    pet : ndarray (rows, cols), millimetres (mm)
        Reference evapotranspiration demand for the day, non-negative.
    terrain_derivatives : TerrainDerivatives
        Reads ``downstream``, ``order``, ``slope`` and the grid's cell
        size, and ``solar_ratio`` when ``aspect_strength`` is not 0.
    params : SubsurfaceBucketParams

    Returns
    -------
    moisture : ndarray (rows, cols), mm
        Water at the end of the day, plant store plus free store.
    fluxes : ndarray (7, rows, cols), mm
        Indexed by ``SubsurfaceBucketFlux``.
    """
    soil_hydraulics.require_conductivity("step_subsurface_bucket_model")
    capacity = soil_hydraulics.capacity
    free_capacity = soil_hydraulics.free_capacity
    total_capacity = capacity + free_capacity
    depth_mm = soil_hydraulics.root_depth * 1000.0
    limit = np.nan_to_num(soil_hydraulics.k_sat) * GRAVITY * params.rain_hours * 3600.0

    room = total_capacity - moisture
    infiltration = np.minimum(np.minimum(rain, room), limit)
    excess = (rain - infiltration).ravel()
    total = moisture + infiltration

    free = np.maximum(total - capacity, 0.0)
    theta = soil_hydraulics.theta_fc + free / depth_mm
    conductivity = compute_campbell_conductivity(np.nan_to_num(theta), np.nan_to_num(soil_hydraulics.theta_s, nan=1.0), np.nan_to_num(soil_hydraulics.b, nan=1.0), np.nan_to_num(soil_hydraulics.k_sat))
    lateral_flow = np.minimum(params.lateral_multiplier * conductivity * GRAVITY * terrain_derivatives.slope * soil_hydraulics.root_depth / terrain_derivatives.grid.cell_size * SECONDS_PER_DAY, free)
    percolation = np.minimum(conductivity * GRAVITY * params.percolation_fraction * SECONDS_PER_DAY, free - lateral_flow)
    total = (total - lateral_flow - percolation).ravel()

    room = total_capacity.ravel() - total
    remaining_limit = (limit - infiltration).ravel()
    inflow = np.zeros_like(total)
    surface = np.zeros_like(total)
    subsurface = np.zeros_like(total)
    surface_flow = np.zeros_like(total)
    runoff = np.zeros_like(total)
    downstream = terrain_derivatives.downstream.ravel()
    sent_lateral = lateral_flow.ravel()

    for cell in terrain_derivatives.order:
        taken_sub = min(subsurface[cell], room[cell])
        taken_surf = min(surface[cell], room[cell] - taken_sub, remaining_limit[cell])
        inflow[cell] = taken_sub + taken_surf
        passing = excess[cell] + surface[cell] - taken_surf + subsurface[cell] - taken_sub
        target = downstream[cell]
        if target == NO_OUTLET:
            runoff[cell] = passing + sent_lateral[cell]
        else:
            surface_flow[cell] = passing
            surface[target] += passing
            subsurface[target] += sent_lateral[cell]

    total = (total + inflow).reshape(moisture.shape)
    plant = np.minimum(total, capacity)
    with np.errstate(divide="ignore", invalid="ignore"):
        fullness = np.where(capacity > 0, plant / capacity, 0.0)
    demand = pet if params.aspect_strength == 0 else pet * terrain_derivatives.solar_ratio**params.aspect_strength
    evaporation = np.minimum(demand * fullness**params.stress_exponent, total)

    fluxes = np.empty((len(SubsurfaceBucketFlux), *moisture.shape), dtype=np.float64)
    fluxes[SubsurfaceBucketFlux.INFILTRATION] = infiltration
    fluxes[SubsurfaceBucketFlux.INFLOW] = inflow.reshape(moisture.shape)
    fluxes[SubsurfaceBucketFlux.SURFACE_FLOW] = surface_flow.reshape(moisture.shape)
    fluxes[SubsurfaceBucketFlux.SUBSURFACE_LATERAL_FLOW] = lateral_flow
    fluxes[SubsurfaceBucketFlux.PERCOLATION] = percolation
    fluxes[SubsurfaceBucketFlux.RUNOFF] = runoff.reshape(moisture.shape)
    fluxes[SubsurfaceBucketFlux.EVAPORATION] = evaporation
    return total - evaporation, fluxes


def _derivatives(elevation, cell_size=10.0) -> TerrainDerivatives:
    from terrasim2.k.terrain_grid import TerrainGrid

    return TerrainDerivatives(TerrainGrid(elevation=np.asarray(elevation, dtype=float), cell_size=cell_size))


def _hydraulics(shape, capacity=45.0, k_sat=7.2e-4, b=3.0, theta_s=0.45, theta_fc=0.25, theta_wp=0.10, root_depth=0.3) -> SoilHydraulics:
    """A sandy-loam-like soil: 45 mm plant store and 60 mm free store at 0.3 m."""
    full = lambda v: np.full(shape, v, dtype=float)  # noqa: E731
    return SoilHydraulics(full(capacity), root_depth, full(k_sat), full(b), full(theta_s), full(theta_fc), full(theta_wp))


F = SubsurfaceBucketFlux


def t1():
    """Three saturated cells down a 10 percent slope, no rain: the two sloping cells each pass the
    hand-computed saturated Darcy amount, 1.83 mm, to the cell below; the saturated foot cannot take it
    and sheds it at the outlet; a cell that drained is refilled by what arrives from above."""
    h = _hydraulics((1, 3))
    saturated = np.full((1, 3), 105.0)
    d = _derivatives([[2.0, 1.0, 0.0]])
    new, f = step_subsurface_bucket_model(saturated, h, np.zeros((1, 3)), np.zeros((1, 3)), d, SubsurfaceBucketParams())
    expected = 7.2e-4 * 9.81 * 0.1 * 0.3 / 10.0 * 86400
    assert abs(expected - 1.831) < 0.001
    assert np.allclose(f[F.SUBSURFACE_LATERAL_FLOW], [[expected, expected, 0.0]])
    assert np.allclose(f[F.INFLOW], [[0.0, expected, 0.0]])
    assert np.allclose(f[F.RUNOFF], [[0.0, 0.0, expected]])
    assert np.all(f[F.PERCOLATION] == 0.0), "the default base is impermeable"
    assert np.allclose(f[F.SURFACE_FLOW], 0.0), "nothing moved over the surface"
    assert np.allclose(new, [[105.0 - expected, 105.0, 105.0]])


def t2():
    """At field capacity nothing drains; a free store of 30 mm drains at the conductivity of its content,
    between the two; a percolation fraction of one empties the free store downward within the day."""
    h = _hydraulics((1, 3))
    d = _derivatives([[2.0, 1.0, 0.0]])
    rain = np.zeros((1, 3))
    _, at_fc = step_subsurface_bucket_model(np.full((1, 3), 45.0), h, rain, rain, d, SubsurfaceBucketParams())
    assert np.all(at_fc[F.SUBSURFACE_LATERAL_FLOW] == 0.0) and np.all(at_fc[F.INFLOW] == 0.0)
    _, half = step_subsurface_bucket_model(np.full((1, 3), 75.0), h, rain, rain, d, SubsurfaceBucketParams())
    saturated = 7.2e-4 * 9.81 * 0.1 * 0.3 / 10.0 * 86400
    expected = saturated * ((0.25 + 0.1) / 0.45) ** 9
    assert abs(half[F.SUBSURFACE_LATERAL_FLOW][0, 0] - expected) < 1e-9
    new, leaky = step_subsurface_bucket_model(np.full((1, 3), 75.0), h, rain, rain, d, SubsurfaceBucketParams(percolation_fraction=1.0))
    assert np.allclose(leaky[F.PERCOLATION] + leaky[F.SUBSURFACE_LATERAL_FLOW], 30.0)
    gained = half[F.SUBSURFACE_LATERAL_FLOW][0, 0]
    assert np.allclose(new, [[45.0, 45.0 + gained, 45.0 + gained]]), "each cell below the crest keeps what arrived through the soil, having leaked its own"


def t3():
    """The infiltration limit: on a clay cell 20 mm of rain in six hours is 3.6 mm in and the rest excess, even
    with room to spare; with all-day rain 14 mm enters; run-on meets the same limit."""
    h = _hydraulics((1, 2), k_sat=1.7e-5, capacity=60.0)
    d = _derivatives([[1.0, 0.0]])
    rain = np.array([[20.0, 0.0]])
    new, storm = step_subsurface_bucket_model(np.zeros((1, 2)), h, rain, np.zeros((1, 2)), d, SubsurfaceBucketParams(rain_hours=6.0))
    limit = 1.7e-5 * 9.81 * 6 * 3600
    assert abs(limit - 3.60) < 0.01
    assert np.isclose(storm[F.INFILTRATION][0, 0], limit)
    assert np.isclose(storm[F.INFLOW][0, 1], limit), "the cell below takes the same limit from the run-on"
    assert np.isclose(storm[F.RUNOFF][0, 1], 20.0 - 2 * limit)
    assert np.isclose(storm[F.SURFACE_FLOW][0, 0], 20.0 - limit) and storm[F.SURFACE_FLOW][0, 1] == 0.0, "the excess passed over the surface; the outlet sheds rather than passes"
    _, allday = step_subsurface_bucket_model(np.zeros((1, 2)), h, rain, np.zeros((1, 2)), d, SubsurfaceBucketParams())
    assert abs(allday[F.INFILTRATION][0, 0] - 14.41) < 0.01


def t4():
    """Mass balance on a random hill with heavy rain: per cell and over the grid, every flux non-negative,
    nothing above saturation, runoff only at the edge."""
    rng = np.random.default_rng(3)
    rows, cols = np.mgrid[0:20, 0:25]
    z = 30.0 - 0.4 * np.hypot(rows - 10, cols - 12) + rng.normal(0, 0.1, (20, 25))
    h = _hydraulics((20, 25))
    moisture = rng.uniform(0.5, 1.5, (20, 25)) * 45.0
    rain = np.full((20, 25), 40.0)
    pet = rng.uniform(0, 4, (20, 25))
    d = _derivatives(z)
    new, f = step_subsurface_bucket_model(moisture, h, rain, pet, d, SubsurfaceBucketParams(percolation_fraction=0.1, rain_hours=6.0))
    assert f.shape == (7, 20, 25) and np.all(f >= -1e-12)
    assert np.all(f[F.SURFACE_FLOW][d.downstream == NO_OUTLET] == 0.0), "outlets shed, they do not pass on"
    per_cell = (new - moisture) - (f[F.INFILTRATION] + f[F.INFLOW] - f[F.SUBSURFACE_LATERAL_FLOW] - f[F.PERCOLATION] - f[F.EVAPORATION])
    assert np.abs(per_cell).max() < 1e-9
    sent = (rain - f[F.INFILTRATION]).sum() + f[F.SUBSURFACE_LATERAL_FLOW].sum()
    assert abs(sent - f[F.INFLOW].sum() - f[F.RUNOFF].sum()) < 1e-6
    assert np.all(new >= -1e-12) and np.all(new <= 105.0 + 1e-9)
    assert f[F.RUNOFF][1:-1, 1:-1].sum() == 0.0


def t5():
    """A saturated slope over a dry fortnight: free water moves downhill, so the foot ends wetter than the crest
    and the crest settles toward field capacity."""
    rows, cols = np.mgrid[0:1, 0:12]
    d = _derivatives(12.0 - cols.astype(float))
    h = _hydraulics((1, 12), k_sat=5e-3)
    moisture = np.full((1, 12), 105.0)
    rain = np.zeros((1, 12))
    pet = np.full((1, 12), 1.0)
    for _ in range(14):
        moisture, _ = step_subsurface_bucket_model(moisture, h, rain, pet, d, SubsurfaceBucketParams())
    assert moisture[0, 0] < moisture[0, 5] < moisture[0, 10]
    assert moisture[0, 10] - moisture[0, 0] > 10.0
    assert moisture[0, 0] < 70.0, "the crest has lost most of its free water; what remains drains ever more slowly as its conductivity falls"


def t6():
    """The lateral multiplier scales the downslope lateral flow alone: ten times the matrix value passes ten times
    the water, the percolation is untouched, and the free store still caps what can leave."""
    h = _hydraulics((1, 3))
    d = _derivatives([[2.0, 1.0, 0.0]])
    rain = np.zeros((1, 3))
    _, matrix = step_subsurface_bucket_model(np.full((1, 3), 105.0), h, rain, rain, d, SubsurfaceBucketParams(percolation_fraction=0.01))
    _, fast = step_subsurface_bucket_model(np.full((1, 3), 105.0), h, rain, rain, d, SubsurfaceBucketParams(percolation_fraction=0.01, lateral_multiplier=10.0))
    assert np.allclose(fast[F.SUBSURFACE_LATERAL_FLOW][0, :2], 10.0 * matrix[F.SUBSURFACE_LATERAL_FLOW][0, :2])
    assert np.allclose(fast[F.PERCOLATION], matrix[F.PERCOLATION])
    _, capped = step_subsurface_bucket_model(np.full((1, 3), 105.0), h, rain, rain, d, SubsurfaceBucketParams(lateral_multiplier=1000.0))
    assert np.allclose(capped[F.SUBSURFACE_LATERAL_FLOW][0, :2], 60.0), "no more than the free store"


def t7():
    """Aspect: with a strength the sunny cell of a ridge evaporates more than the shaded one from the same store, by
    the solar ratio to that power; with none both evaporate pet and the terrain's sun is never asked for."""
    from terrasim2.k.terrain_grid import TerrainGrid

    rows, cols = np.mgrid[0:5, 0:3]
    ridge = 100.0 - 2.0 * np.abs(rows - 2)  # a crest along row 2: rows above face north, rows below face south
    grid = TerrainGrid(elevation=ridge, cell_size=10.0)
    h = _hydraulics((5, 3))
    moisture = np.full((5, 3), 45.0)
    rain = np.zeros((5, 3))
    pet = np.full((5, 3), 3.0)
    unlit = TerrainDerivatives(grid)
    _, flat = step_subsurface_bucket_model(moisture, h, rain, pet, unlit, SubsurfaceBucketParams())
    assert np.allclose(flat[F.EVAPORATION], 3.0) and "solar_ratio" not in unlit.__dict__
    lit = TerrainDerivatives(grid, latitude=-37.66)
    for strength in (1.0, 0.5):
        _, sunny = step_subsurface_bucket_model(moisture, h, rain, pet, lit, SubsurfaceBucketParams(aspect_strength=strength))
        assert np.allclose(sunny[F.EVAPORATION], 3.0 * lit.solar_ratio**strength)
        assert sunny[F.EVAPORATION][0, 1] > 3.0 > sunny[F.EVAPORATION][4, 1], "north-facing dries faster in the south"
    try:
        step_subsurface_bucket_model(moisture, h, rain, pet, unlit, SubsurfaceBucketParams(aspect_strength=1.0))
    except ValueError as err:
        assert "latitude" in str(err)
    else:
        raise AssertionError("expected ValueError for aspect without a latitude")


def t8():
    """Hydraulics without conductivity are refused with a message naming the step."""
    try:
        step_subsurface_bucket_model(np.zeros((1, 3)), SoilHydraulics(np.full((1, 3), 30.0)), np.zeros((1, 3)), np.zeros((1, 3)), _derivatives([[2.0, 1.0, 0.0]]), SubsurfaceBucketParams())
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
    t6()
    t7()
    t8()
