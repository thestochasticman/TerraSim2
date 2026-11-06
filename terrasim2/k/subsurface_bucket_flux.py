from enum import IntEnum


class SubsurfaceBucketFlux(IntEnum):
    """Index of each flux along axis 0 of the array ``step_subsurface_bucket_model`` returns.

    All in millimetres (mm) per cell per day.

    INFILTRATION : the cell's own rain that entered its store
    INFLOW : water that arrived from upslope, by overflow or by drainage, and entered the store
    DRAINAGE : water that left the store downslope through the soil
    RUNOFF : water that left the grid at this cell; non-zero only at outlets
    EVAPORATION : water that left the store to the air
    """

    INFILTRATION = 0
    INFLOW = 1
    DRAINAGE = 2
    RUNOFF = 3
    EVAPORATION = 4


def t():
    """Five fluxes in declared order, usable directly as array indices."""
    import numpy as np

    assert [f.value for f in SubsurfaceBucketFlux] == [0, 1, 2, 3, 4]
    assert SubsurfaceBucketFlux["DRAINAGE"] is SubsurfaceBucketFlux.DRAINAGE
    assert np.arange(5 * 2 * 2).reshape(5, 2, 2)[SubsurfaceBucketFlux.RUNOFF][0, 0] == 12
