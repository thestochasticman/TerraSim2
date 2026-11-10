from enum import IntEnum


class RoutedBucketFlux(IntEnum):
    """Index of each flux along axis 0 of the array ``step_routed_bucket_model`` returns.

    All in millimetres (mm) per cell per day.

    INFILTRATION : the cell's own rain that entered its store
    INFLOW : water that arrived from upslope cells and entered the store
    SURFACE_FLOW : water the cell passed on over the surface to the cell it drains to; zero at outlets
    RUNOFF : water that left the grid at this cell; non-zero only at outlets
    EVAPORATION : water that left the store to the air
    """

    INFILTRATION = 0
    INFLOW = 1
    SURFACE_FLOW = 2
    RUNOFF = 3
    EVAPORATION = 4


def t():
    """Five fluxes in declared order, usable directly as array indices."""
    import numpy as np

    assert [f.value for f in RoutedBucketFlux] == [0, 1, 2, 3, 4]
    assert RoutedBucketFlux["INFLOW"] is RoutedBucketFlux.INFLOW
    assert np.arange(5 * 2 * 2).reshape(5, 2, 2)[RoutedBucketFlux.RUNOFF][0, 0] == 12
