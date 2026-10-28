import numpy as np

from terrasim2.k.bucket_flux import BucketFlux
from terrasim2.k.bucket_model_params import BucketModelParams


def step_bucket_model(
    moisture: np.ndarray,
    capacity: np.ndarray,
    rain: np.ndarray,
    pet: np.ndarray,
    params: BucketModelParams,
) -> tuple[np.ndarray, np.ndarray]:
    """One day of the bucket model on every cell, independently.

    Each cell is a closed store of size ``capacity``. In order:

    1. Rain fills the room left in the store. What does not fit is runoff.
    2. Evaporation takes ``pet * (fullness ** stress_exponent)`` where
       fullness is moisture over capacity after the rain, capped at what
       the store holds.
    3. New moisture is old plus infiltration minus evaporation.

    So ``new - old == rain - runoff - evaporation`` exactly. No drainage,
    no lateral flow; terrain plays no part.

    Parameters
    ----------
    moisture : ndarray (rows, cols), millimetres (mm)
        Store contents at the start of the day. Must lie in [0, capacity].
    capacity : ndarray (rows, cols), millimetres (mm)
        Store size per cell, non-negative. A zero-capacity cell passes all
        rain to runoff and never evaporates.
    rain : ndarray (rows, cols), millimetres (mm)
        Rain arriving during the day, non-negative.
    pet : ndarray (rows, cols), millimetres (mm)
        Reference evapotranspiration demand for the day, non-negative.
    params : BucketModelParams

    Returns
    -------
    moisture : ndarray (rows, cols), mm
        Store contents at the end of the day.
    fluxes : ndarray (3, rows, cols), mm
        Indexed by ``BucketFlux``: INFILTRATION, RUNOFF, EVAPORATION.
    """
    room = capacity - moisture
    infiltration = np.minimum(rain, room)
    runoff = rain - infiltration
    wet = moisture + infiltration

    with np.errstate(divide="ignore", invalid="ignore"):
        fullness = np.where(capacity > 0, wet / capacity, 0.0)
    evaporation = np.minimum(pet * fullness**params.stress_exponent, wet)

    new_moisture = wet - evaporation
    fluxes = np.empty((len(BucketFlux), *moisture.shape), dtype=np.float64)
    fluxes[BucketFlux.INFILTRATION] = infiltration
    fluxes[BucketFlux.RUNOFF] = runoff
    fluxes[BucketFlux.EVAPORATION] = evaporation
    return new_moisture, fluxes


def _cell(moisture, capacity, rain, pet, exponent=1.0):
    """Run one cell as a 1x1 grid and return (new_moisture, infiltration, runoff, evaporation) as floats."""
    m, f = step_bucket_model(
        np.array([[moisture]]), np.array([[capacity]]), np.array([[rain]]), np.array([[pet]]),
        BucketModelParams(stress_exponent=exponent),
    )
    return float(m[0, 0]), float(f[BucketFlux.INFILTRATION, 0, 0]), float(f[BucketFlux.RUNOFF, 0, 0]), float(f[BucketFlux.EVAPORATION, 0, 0])


def t1():
    """Hand-computed cell: 30 mm in a 100 mm store, 20 mm rain, 4 mm demand."""
    m, inf, run, ev = _cell(30.0, 100.0, 20.0, 4.0)
    assert inf == 20.0 and run == 0.0
    assert abs(ev - 4.0 * 0.5) < 1e-12          # wet = 50, fullness 0.5
    assert abs(m - 48.0) < 1e-12


def t2():
    """A full store sheds all rain as runoff; an overflowing one sheds the excess."""
    m, inf, run, ev = _cell(100.0, 100.0, 15.0, 0.0)
    assert inf == 0.0 and run == 15.0 and m == 100.0 and ev == 0.0
    m, inf, run, ev = _cell(90.0, 100.0, 15.0, 0.0)
    assert inf == 10.0 and run == 5.0 and m == 100.0


def t3():
    """Dry-down with no rain decays towards empty without overshooting, and an empty store stays empty."""
    m = 3.0
    for _ in range(10):
        before = m
        m, _, _, ev = _cell(m, 100.0, 0.0, 50.0)
        assert 0.0 <= m < before and ev == before - m
    assert abs(m - 3.0 * 0.5**10) < 1e-12, "linear stress with pet = capacity / 2 halves the store each day"
    m, _, _, ev = _cell(0.0, 100.0, 0.0, 50.0)
    assert m == 0.0 and ev == 0.0


def t4():
    """The stress exponent holds evaporation back harder as the store dries."""
    _, _, _, ev_linear = _cell(25.0, 100.0, 0.0, 10.0, exponent=1.0)
    _, _, _, ev_steep = _cell(25.0, 100.0, 0.0, 10.0, exponent=2.0)
    assert abs(ev_linear - 2.5) < 1e-12 and abs(ev_steep - 0.625) < 1e-12


def t5():
    """Zero-capacity cells pass rain straight to runoff with no evaporation and no NaN."""
    m, inf, run, ev = _cell(0.0, 0.0, 12.0, 5.0)
    assert m == 0.0 and inf == 0.0 and run == 12.0 and ev == 0.0


def t6():
    """Mass balance on a random grid: storage change equals rain minus runoff minus evaporation, to 1e-9."""
    rng = np.random.default_rng(0)
    capacity = rng.uniform(20, 200, (40, 50))
    moisture = rng.uniform(0, 1, (40, 50)) * capacity
    rain = rng.exponential(5, (40, 50)) * (rng.random((40, 50)) < 0.3)
    pet = rng.uniform(0, 8, (40, 50))
    new, f = step_bucket_model(moisture, capacity, rain, pet, BucketModelParams())
    assert f.shape == (3, 40, 50)
    balance = (new - moisture) - (rain - f[BucketFlux.RUNOFF] - f[BucketFlux.EVAPORATION])
    assert np.abs(balance).max() < 1e-9
    assert np.all(new >= 0) and np.all(new <= capacity + 1e-9)
    assert np.all(f >= 0)


def t():
    t1()
    t2()
    t3()
    t4()
    t5()
    t6()
