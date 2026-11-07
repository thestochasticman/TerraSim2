import numpy as np

HOURS = np.arange(0.5, 24.0, 1.0)
DAYS = np.arange(1, 366)


def compute_solar_ratio(slope: np.ndarray, aspect: np.ndarray, latitude: float, days: np.ndarray = DAYS, hours: np.ndarray = HOURS) -> np.ndarray:
    """How much direct sun each cell's tilted ground receives over a year, relative to flat ground.

    The sun's position is stepped through every hour of every day given
    and the cosine of its angle to the cell's surface is summed where
    the sun is above the horizon and the surface faces it; the same sum
    for a horizontal surface divides it. Clear sky, no shading by other
    cells, no diffuse light: the geometric part of why a north-facing
    slope in the south dries faster.

    Parameters
    ----------
    slope : ndarray, radians
        Shape (rows, cols), from ``compute_slope_aspect``.
    aspect : ndarray, radians
        Same shape: the downslope direction clockwise from north.
    latitude : float, degrees
        Of the grid; negative south.
    days : ndarray, dimensionless
        Days of the year to integrate over, 1 to 365; a full year by default.
    hours : ndarray, hours
        Solar times to sample within each day.

    Returns
    -------
    ndarray, dimensionless
        Shape (rows, cols): 1 on flat ground, above it on slopes facing
        the equator, below on those facing the pole.
    """
    slope = np.asarray(slope, dtype=np.float64)
    aspect = np.asarray(aspect, dtype=np.float64)
    if slope.shape != aspect.shape:
        raise ValueError(f"slope {slope.shape} and aspect {aspect.shape} must have one shape")
    if not -90 <= latitude <= 90:
        raise ValueError(f"latitude must be within [-90, 90] degrees, got {latitude}")
    phi = np.deg2rad(latitude)
    normal_east = np.sin(slope) * np.sin(aspect)
    normal_north = np.sin(slope) * np.cos(aspect)
    normal_up = np.cos(slope)

    on_slope = np.zeros(slope.shape)
    on_flat = 0.0
    omega = np.deg2rad(15.0 * (np.asarray(hours, dtype=np.float64) - 12.0))
    for day in np.asarray(days):
        declination = np.deg2rad(23.45) * np.sin(2 * np.pi * (284 + day) / 365)
        sun_east = -np.cos(declination) * np.sin(omega)
        sun_north = np.sin(declination) * np.cos(phi) - np.cos(declination) * np.sin(phi) * np.cos(omega)
        sun_up = np.sin(declination) * np.sin(phi) + np.cos(declination) * np.cos(phi) * np.cos(omega)
        above = sun_up > 0
        if not above.any():
            continue
        on_flat += sun_up[above].sum()
        cos_theta = normal_east[..., None] * sun_east[above] + normal_north[..., None] * sun_north[above] + normal_up[..., None] * sun_up[above]
        on_slope += np.maximum(cos_theta, 0.0).sum(axis=-1)
    if on_flat == 0:
        raise ValueError("the sun never rises over the days given")
    return on_slope / on_flat


def t1():
    """Flat ground is 1 everywhere; at 37 degrees south a slope facing north takes more sun than flat and one
    facing south less, east and west alike; at 37 north the two swap; at the equator north and south nearly tie."""
    flat = compute_solar_ratio(np.zeros((2, 2)), np.zeros((2, 2)), -37.66)
    assert np.allclose(flat, 1.0)
    tilt = np.full((1, 4), np.deg2rad(10.0))
    facing = np.array([[0.0, np.pi, np.pi / 2, -np.pi / 2]])  # north, south, east, west
    south_hemisphere = compute_solar_ratio(tilt, facing, -37.66)[0]
    assert south_hemisphere[0] > 1.0 > south_hemisphere[1], south_hemisphere
    assert abs(south_hemisphere[2] - south_hemisphere[3]) < 1e-9 and south_hemisphere[2] < 1.0
    north_hemisphere = compute_solar_ratio(tilt, facing, 37.66)[0]
    assert abs(north_hemisphere[0] - south_hemisphere[1]) < 1e-9 and abs(north_hemisphere[1] - south_hemisphere[0]) < 1e-9
    equator = compute_solar_ratio(tilt, facing, 0.0)[0]
    assert abs(equator[0] - equator[1]) < 1e-9


def t2():
    """Equator-facing ground gains most over flat in winter, when the sun is low, and little or nothing in summer,
    when it rises and sets on the poleward side; pole-facing ground the reverse; a full year lies between; bad
    inputs are refused."""
    tilt = np.full((1, 2), np.deg2rad(20.0))
    facing = np.array([[0.0, np.pi]])
    winter = compute_solar_ratio(tilt, facing, -37.66, days=np.arange(152, 244))
    summer = compute_solar_ratio(tilt, facing, -37.66, days=np.array([1, 15, 30, 335, 350, 365]))
    year = compute_solar_ratio(tilt, facing, -37.66)
    assert winter[0, 0] > year[0, 0] > summer[0, 0], (winter, year, summer)
    assert winter[0, 1] < year[0, 1] < summer[0, 1] < 1.0
    assert winter[0, 0] > 1.5 and year[0, 0] > 1.0 > year[0, 1] and winter[0, 1] < 0.5
    for bad in (dict(slope=np.zeros((2, 2)), aspect=np.zeros((2, 3)), latitude=0.0), dict(slope=np.zeros((2, 2)), aspect=np.zeros((2, 2)), latitude=95.0)):
        try:
            compute_solar_ratio(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def t():
    t1()
    t2()
