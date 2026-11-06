from enum import IntEnum


class SubsurfaceBucketFlux(IntEnum):
    """Index of each flux along axis 0 of the array ``step_subsurface_bucket_model`` returns.

    All in millimetres (mm) per cell per day.

    INFILTRATION : the cell's own rain that entered its stores
    INFLOW : water that arrived from upslope, over the surface or through the soil, and entered
    DRAINAGE : free water that left downslope through the soil
    LEAK : free water that left straight down, out of the root zone
    RUNOFF : water that left the grid at this cell; non-zero only at outlets
    EVAPORATION : water that left the stores to the air
    """

    INFILTRATION = 0
    INFLOW = 1
    DRAINAGE = 2
    LEAK = 3
    RUNOFF = 4
    EVAPORATION = 5


def t():
    """Six fluxes in declared order, usable directly as array indices."""
    import numpy as np

    assert [f.value for f in SubsurfaceBucketFlux] == [0, 1, 2, 3, 4, 5]
    assert SubsurfaceBucketFlux["LEAK"] is SubsurfaceBucketFlux.LEAK
    assert np.arange(6 * 2 * 2).reshape(6, 2, 2)[SubsurfaceBucketFlux.RUNOFF][0, 0] == 16
