from datetime import date, timedelta

# Sentinel-2 imagery on Digital Earth Australia begins in mid-2015; a year of it is the unit of a vegetation map.
SENTINEL2_FROM = date(2015, 7, 1)
REFERENCE_YEAR = (date(2023, 1, 1), date(2023, 12, 31))


def choose_reference_period(start: date, end: date) -> tuple[date, date]:
    """The year of imagery a site's vegetation map is made from.

    Trees keep their leaves through the dry season and grass browns off,
    so a year of NDVI separates them; one full year is used so every
    season is seen. When a site's own dates give a year of imagery, the
    last year of them is used, so the map matches the period modelled.
    When they do not, because the site predates Sentinel-2 or spans less
    than a year of it, a fixed reference year stands in: trees persist,
    so a recent year still maps them.

    Parameters
    ----------
    start, end : date
        The site's dates, inclusive.

    Returns
    -------
    tuple of date
        ``(from, to)``, inclusive, 365 days apart.
    """
    if start > end:
        raise ValueError(f"start {start} is after end {end}")
    last_year_start = end - timedelta(days=364)
    if last_year_start >= SENTINEL2_FROM and last_year_start >= start:
        return (last_year_start, end)
    return REFERENCE_YEAR


def t():
    """A site within Sentinel-2's years takes its own last year; one before them, or shorter than a year, takes the reference year."""
    assert choose_reference_period(date(2025, 4, 30), date(2026, 7, 1)) == (date(2025, 7, 2), date(2026, 7, 1))
    assert choose_reference_period(date(2020, 9, 25), date(2026, 6, 3)) == (date(2025, 6, 4), date(2026, 6, 3))
    assert choose_reference_period(date(1995, 9, 25), date(1996, 11, 29)) == REFERENCE_YEAR
    assert choose_reference_period(date(2025, 1, 1), date(2025, 6, 30)) == REFERENCE_YEAR, "half a year is not enough"
    assert choose_reference_period(date(2015, 1, 1), date(2015, 12, 31)) == REFERENCE_YEAR, "the year straddles the start of the archive"
    try:
        choose_reference_period(date(2026, 1, 1), date(2025, 1, 1))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
