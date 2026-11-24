from enum import IntEnum


class SubsurfaceBucketFlux(IntEnum):
    """Index of each flux along axis 0 of the array ``step_subsurface_bucket_model`` returns.

    All in millimetres (mm) per cell per day.

    INFILTRATION : the cell's own rain that entered its stores
    INFLOW : water that arrived from upslope, over the surface or through the soil, and entered
    SURFACE_FLOW : water the cell passed on over the surface to the cell it drains to; zero at outlets
    SUBSURFACE_LATERAL_FLOW : free water that left downslope through the soil
    PERCOLATION : free water that left straight down, out of the root zone
    RUNOFF : water that left the grid at this cell; non-zero only at outlets
    EVAPORATION : water that left the stores to the air
    """

    INFILTRATION = 0
    INFLOW = 1
    SURFACE_FLOW = 2
    SUBSURFACE_LATERAL_FLOW = 3
    PERCOLATION = 4
    RUNOFF = 5
    EVAPORATION = 6


def t():
    """Seven fluxes in declared order, usable directly as array indices."""
    import numpy as np

    assert [f.value for f in SubsurfaceBucketFlux] == [0, 1, 2, 3, 4, 5, 6]
    assert SubsurfaceBucketFlux["PERCOLATION"] is SubsurfaceBucketFlux.PERCOLATION
    assert np.arange(7 * 2 * 2).reshape(7, 2, 2)[SubsurfaceBucketFlux.RUNOFF][0, 0] == 20
