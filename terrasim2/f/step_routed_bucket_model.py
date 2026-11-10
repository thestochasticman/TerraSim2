import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET
from terrasim2.k.bucket_model_params import BucketModelParams
from terrasim2.k.routed_bucket_flux import RoutedBucketFlux
from terrasim2.k.soil_hydraulics import SoilHydraulics
from terrasim2.k.terrain_derivatives import TerrainDerivatives


def step_routed_bucket_model(
    moisture: np.ndarray,
    soil_hydraulics: SoilHydraulics,
    rain: np.ndarray,
    pet: np.ndarray,
    terrain_derivatives: TerrainDerivatives,
    params: BucketModelParams,
) -> tuple[np.ndarray, np.ndarray]:
    """One day of buckets whose overflow runs downhill.

    Each cell is a store of size ``soil_hydraulics.capacity``. In order:

    1. Rain fills the room left in each store. What does not fit is excess.
    2. Excess cascades: walking the cells from the ridges down, each cell
       receives what its upslope neighbours passed on, keeps what room it
       has left, and passes the rest to the cell it drains to, recorded as
       surface flow. Water reaching an outlet leaves the grid as runoff. The cascade runs to
       completion within the day, since a day is long against the time
       water takes to cross a hillslope.
    3. Evaporation takes ``pet * (fullness ** stress_exponent)``, capped at
       what the store holds.

    Per cell, ``new - old == infiltration + inflow - evaporation``; over the
    grid, the rain that did not enter a store equals the runoff at the
    outlets. No subsurface flow yet.

    Parameters
    ----------
    moisture : ndarray (rows, cols), millimetres (mm)
        Store contents at the start of the day, in [0, capacity].
    soil_hydraulics : SoilHydraulics
        Only ``capacity`` (mm) is read: store size per cell, non-negative.
    rain : ndarray (rows, cols), millimetres (mm)
        Rain arriving during the day, non-negative.
    pet : ndarray (rows, cols), millimetres (mm)
        Reference evapotranspiration demand for the day, non-negative.
    terrain_derivatives : TerrainDerivatives
        Reads ``downstream`` and ``order``.
    params : BucketModelParams

    Returns
    -------
    moisture : ndarray (rows, cols), mm
        Store contents at the end of the day.
    fluxes : ndarray (5, rows, cols), mm
        Indexed by ``RoutedBucketFlux``: INFILTRATION, INFLOW, SURFACE_FLOW, RUNOFF, EVAPORATION.
    """
    capacity = soil_hydraulics.capacity
    room = capacity - moisture
    infiltration = np.minimum(rain, room)
    excess = (rain - infiltration).ravel()
    wet = (moisture + infiltration).ravel()
    room = capacity.ravel() - wet
    inflow = np.zeros_like(wet)
    arriving = np.zeros_like(wet)
    surface_flow = np.zeros_like(wet)
    runoff = np.zeros_like(wet)
    downstream = terrain_derivatives.downstream.ravel()

    for cell in terrain_derivatives.order:
        taken = min(arriving[cell], room[cell])
        inflow[cell] = taken
        passing = excess[cell] + arriving[cell] - taken
        target = downstream[cell]
        if target == NO_OUTLET:
            runoff[cell] = passing
        else:
            surface_flow[cell] = passing
            arriving[target] += passing

    wet = (wet + inflow).reshape(moisture.shape)
    with np.errstate(divide="ignore", invalid="ignore"):
        fullness = np.where(capacity > 0, wet / capacity, 0.0)
    evaporation = np.minimum(pet * fullness**params.stress_exponent, wet)

    fluxes = np.empty((len(RoutedBucketFlux), *moisture.shape), dtype=np.float64)
    fluxes[RoutedBucketFlux.INFILTRATION] = infiltration
    fluxes[RoutedBucketFlux.INFLOW] = inflow.reshape(moisture.shape)
    fluxes[RoutedBucketFlux.SURFACE_FLOW] = surface_flow.reshape(moisture.shape)
    fluxes[RoutedBucketFlux.RUNOFF] = runoff.reshape(moisture.shape)
    fluxes[RoutedBucketFlux.EVAPORATION] = evaporation
    return wet - evaporation, fluxes


def _derivatives(elevation) -> TerrainDerivatives:
    from terrasim2.k.terrain_grid import TerrainGrid

    return TerrainDerivatives(TerrainGrid(elevation=np.asarray(elevation, dtype=float), cell_size=10.0))


def t1():
    """A slope of three cells, all full: rain on the top runs through the middle to the bottom and leaves there."""
    z = [[3.0, 2.0, 1.0]]
    capacity = np.full((1, 3), 10.0)
    moisture = capacity.copy()
    rain = np.array([[6.0, 0.0, 0.0]])
    new, f = step_routed_bucket_model(moisture, SoilHydraulics(capacity), rain, np.zeros((1, 3)), _derivatives(z), BucketModelParams())
    assert np.array_equal(new, capacity)
    assert np.array_equal(f[RoutedBucketFlux.RUNOFF], [[0.0, 0.0, 6.0]])
    assert np.array_equal(f[RoutedBucketFlux.SURFACE_FLOW], [[6.0, 6.0, 0.0]]), "what each cell passed on over the surface; nothing at the outlet"
    assert np.all(f[RoutedBucketFlux.INFLOW] == 0.0)


def t2():
    """With room downslope, excess is kept where it first finds room, and only the remainder reaches the outlet."""
    z = [[3.0, 2.0, 1.0]]
    capacity = np.full((1, 3), 10.0)
    moisture = np.array([[10.0, 6.0, 9.0]])
    rain = np.array([[6.0, 0.0, 0.0]])
    new, f = step_routed_bucket_model(moisture, SoilHydraulics(capacity), rain, np.zeros((1, 3)), _derivatives(z), BucketModelParams())
    assert np.array_equal(f[RoutedBucketFlux.INFLOW], [[0.0, 4.0, 1.0]])
    assert np.array_equal(f[RoutedBucketFlux.RUNOFF], [[0.0, 0.0, 1.0]])
    assert np.array_equal(f[RoutedBucketFlux.SURFACE_FLOW], [[6.0, 2.0, 0.0]])
    assert np.array_equal(new, [[10.0, 10.0, 10.0]])


def t3():
    """A bowl: nothing leaves until every cell on the way out is full, then the spill cell sheds the rest."""
    z = np.array([[5.0, 5.0, 5.0], [5.0, 1.0, 5.0], [5.0, 4.0, 5.0]])
    capacity = np.full((3, 3), 10.0)
    moisture = np.zeros((3, 3))
    rain = np.zeros((3, 3))
    rain[1, 1] = 25.0
    d = _derivatives(z)
    new, f = step_routed_bucket_model(moisture, SoilHydraulics(capacity), rain, np.zeros((3, 3)), d, BucketModelParams())
    assert f[RoutedBucketFlux.INFILTRATION][1, 1] == 10.0
    assert new[1, 1] == 10.0 and new[2, 1] == 10.0, "the pit fills, then the spill cell below it"
    assert f[RoutedBucketFlux.RUNOFF].sum() == 5.0 and f[RoutedBucketFlux.RUNOFF][2, 1] == 5.0
    assert new.sum() == 20.0


def t4():
    """Mass balance on a random hill: per cell and over the grid, with every flux non-negative."""
    rng = np.random.default_rng(1)
    rows, cols = np.mgrid[0:30, 0:40]
    z = 50.0 - 0.3 * np.hypot(rows - 15, cols - 20) + rng.normal(0, 0.2, (30, 40))
    capacity = rng.uniform(20, 60, (30, 40))
    moisture = rng.uniform(0.6, 1.0, (30, 40)) * capacity
    rain = np.full((30, 40), 25.0)
    pet = rng.uniform(0, 5, (30, 40))
    new, f = step_routed_bucket_model(moisture, SoilHydraulics(capacity), rain, pet, _derivatives(z), BucketModelParams())
    assert f.shape == (5, 30, 40) and np.all(f >= 0)
    per_cell = (new - moisture) - (f[RoutedBucketFlux.INFILTRATION] + f[RoutedBucketFlux.INFLOW] - f[RoutedBucketFlux.EVAPORATION])
    assert np.abs(per_cell).max() < 1e-9
    excess_total = (rain - f[RoutedBucketFlux.INFILTRATION]).sum()
    assert abs(excess_total - f[RoutedBucketFlux.INFLOW].sum() - f[RoutedBucketFlux.RUNOFF].sum()) < 1e-6
    assert np.all(new >= 0) and np.all(new <= capacity + 1e-9)
    assert f[RoutedBucketFlux.RUNOFF][1:-1, 1:-1].sum() == 0.0, "runoff leaves only at the edge"


def t5():
    """Against the closed bucket: same infiltration and, with all stores full, the same total runoff."""
    from terrasim2.f.step_bucket_model import step_bucket_model
    from terrasim2.k.bucket_flux import BucketFlux

    rows, cols = np.mgrid[0:8, 0:8]
    z = 20.0 - rows.astype(float)
    capacity = np.full((8, 8), 30.0)
    moisture = capacity.copy()
    rain = np.full((8, 8), 4.0)
    pet = np.full((8, 8), 2.0)
    d = _derivatives(z)
    closed, fc = step_bucket_model(moisture, SoilHydraulics(capacity), rain, pet, d, BucketModelParams())
    routed, fr = step_routed_bucket_model(moisture, SoilHydraulics(capacity), rain, pet, d, BucketModelParams())
    assert np.array_equal(fc[BucketFlux.INFILTRATION], fr[RoutedBucketFlux.INFILTRATION])
    assert abs(fc[BucketFlux.RUNOFF].sum() - fr[RoutedBucketFlux.RUNOFF].sum()) < 1e-9
    assert np.array_equal(closed, routed)


def t():
    t1()
    t2()
    t3()
    t4()
    t5()
