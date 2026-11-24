import numpy as np

from terrasim2.f.compute_flow_direction import NO_OUTLET


def cascade_downhill(
    excess: np.ndarray,
    lateral: np.ndarray,
    room: np.ndarray,
    limit: np.ndarray,
    downstream: np.ndarray,
    cells: np.ndarray,
    bounds: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pass surface excess and subsurface lateral flow down the flow paths within one day.

    The cells are visited level by level (``compute_flow_levels``), all
    cells of a level at once. A cell first takes what arrived through the
    soil, up to its room; then what arrived over the surface, up to the
    room left and its infiltration limit. What it does not take, plus its
    own surface excess, passes on over the surface to the cell it drains
    to, and its own lateral flow passes on through the soil. At an outlet
    both leave the grid as runoff.

    The same arithmetic as visiting the cells one at a time in flow order,
    since everything draining into a cell sits on a lower level; sums of
    what arrives may be added in another order, so results can differ in
    the last bits of a float.

    Parameters
    ----------
    excess : ndarray (n,), millimetres (mm)
        Each cell's own rain that did not enter it.
    lateral : ndarray (n,), millimetres (mm)
        Each cell's own subsurface lateral flow, sent to the cell it drains to.
    room : ndarray (n,), millimetres (mm)
        Space left in each cell's store.
    limit : ndarray (n,), millimetres (mm)
        How much more surface water each cell can infiltrate today; ``inf`` for none.
    downstream : ndarray (n,) of int, dimensionless
        Flat index each cell drains to, ``NO_OUTLET`` at outlets.
    cells, bounds : ndarray of int, dimensionless
        From ``compute_flow_levels``.

    Returns
    -------
    inflow : ndarray (n,), mm
        What each cell took from what arrived.
    surface_flow : ndarray (n,), mm
        What each cell passed on over the surface; 0 at outlets.
    runoff : ndarray (n,), mm
        What left the grid at each outlet; 0 elsewhere.
    """
    n = excess.shape[0]
    inflow = np.zeros(n)
    surface_flow = np.zeros(n)
    runoff = np.zeros(n)
    surface = np.zeros(n)
    subsurface = np.zeros(n)
    for k in range(len(bounds) - 1):
        c = cells[bounds[k]:bounds[k + 1]]
        sub, surf, rm = subsurface[c], surface[c], room[c]
        # np.where(b < a, b, a) is Python's min(a, b): a NaN room or limit keeps what arrived, as the one-at-a-time walk does
        taken_sub = np.where(rm < sub, rm, sub)
        left = rm - taken_sub
        taken_surf = np.where(left < surf, left, surf)
        taken_surf = np.where(limit[c] < taken_surf, limit[c], taken_surf)
        inflow[c] = taken_sub + taken_surf
        passing = excess[c] + surf - taken_surf + sub - taken_sub
        target = downstream[c]
        out = target == NO_OUTLET
        if out.any():
            runoff[c[out]] = passing[out] + lateral[c[out]]
            on = ~out
            c, target, passing = c[on], target[on], passing[on]
        surface_flow[c] = passing
        np.add.at(surface, target, passing)
        np.add.at(subsurface, target, lateral[c])
    return inflow, surface_flow, runoff


def _cascade_one_at_a_time(excess, lateral, room, limit, downstream, order):
    """The reference: the same rules, one cell at a time in flow order."""
    n = excess.shape[0]
    inflow, surface_flow, runoff, surface, subsurface = (np.zeros(n) for _ in range(5))
    for cell in order:
        taken_sub = min(subsurface[cell], room[cell])
        taken_surf = min(surface[cell], room[cell] - taken_sub, limit[cell])
        inflow[cell] = taken_sub + taken_surf
        passing = excess[cell] + surface[cell] - taken_surf + subsurface[cell] - taken_sub
        target = downstream[cell]
        if target == NO_OUTLET:
            runoff[cell] = passing + lateral[cell]
        else:
            surface_flow[cell] = passing
            surface[target] += passing
            subsurface[target] += lateral[cell]
    return inflow, surface_flow, runoff


def t1():
    """A slope of three: surface excess finds room downslope; lateral flow is taken before surface water; the rest leaves at the outlet."""
    downstream = np.array([1, 2, NO_OUTLET])
    cells, bounds = np.array([0, 1, 2]), np.array([0, 1, 2, 3])
    excess = np.array([6.0, 0.0, 0.0])
    lateral = np.array([2.0, 1.0, 0.5])
    room = np.array([0.0, 5.0, 1.0])
    limit = np.full(3, np.inf)
    inflow, surface_flow, runoff = cascade_downhill(excess, lateral, room, limit, downstream, cells, bounds)
    # cell 1 takes the 2 mm of lateral flow first, then 3 of the 6 arriving over the surface
    assert np.allclose(inflow, [0.0, 5.0, 1.0])
    assert np.allclose(surface_flow, [6.0, 3.0, 0.0])
    # cell 2 receives 3 over the surface and 1 through the soil, takes 1, sheds the rest and its own lateral flow
    assert np.allclose(runoff, [0.0, 0.0, 3.0 + 1.0 - 1.0 + 0.5])


def t2():
    """The infiltration limit caps what a cell takes from the surface, not from the soil."""
    downstream = np.array([1, NO_OUTLET])
    cells, bounds = np.array([0, 1]), np.array([0, 1, 2])
    inflow, surface_flow, runoff = cascade_downhill(np.array([4.0, 0.0]), np.array([3.0, 0.0]), np.array([0.0, 10.0]), np.array([np.inf, 1.0]), downstream, cells, bounds)
    assert np.allclose(inflow, [0.0, 3.0 + 1.0])
    assert np.allclose(runoff, [0.0, 3.0])


def t3():
    """On a random hill, with NaN room on some cells, the levels give what the one-at-a-time walk gives."""
    from terrasim2.f.compute_flow_direction import compute_flow_direction
    from terrasim2.f.compute_flow_levels import compute_flow_levels
    from terrasim2.f.compute_flow_order import compute_flow_order
    from terrasim2.f.fill_pits import fill_pits

    rng = np.random.default_rng(7)
    rows, cols = np.mgrid[0:40, 0:50]
    z = fill_pits(60.0 - 0.25 * np.hypot(rows - 20, cols - 25) + rng.normal(0, 0.4, (40, 50)))
    downstream, _ = compute_flow_direction(z, 10.0)
    order = compute_flow_order(z, downstream)
    cells, bounds = compute_flow_levels(downstream, order)
    n = 40 * 50
    excess, lateral = rng.exponential(2.0, n), rng.exponential(0.5, n)
    room, limit = rng.uniform(0, 4, n), rng.uniform(0, 6, n)
    room[rng.choice(n, 30, replace=False)] = np.nan
    limit[rng.choice(n, 30, replace=False)] = np.inf
    got = cascade_downhill(excess, lateral, room, limit, downstream.ravel(), cells, bounds)
    want = _cascade_one_at_a_time(excess, lateral, room, limit, downstream.ravel(), order)
    for g, w in zip(got, want):
        assert np.allclose(g, w, rtol=1e-12, atol=1e-9, equal_nan=True)
    assert abs(excess.sum() + lateral.sum() - got[0].sum() - got[2].sum()) < 1e-6, "every millimetre is taken somewhere or leaves at an outlet"


def t():
    t1()
    t2()
    t3()
