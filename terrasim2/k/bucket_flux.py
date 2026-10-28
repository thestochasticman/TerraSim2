from enum import IntEnum


class BucketFlux(IntEnum):
    """Index of each flux along axis 0 of the array ``step_bucket_model`` returns.

    A step's fluxes are one array of shape ``(len(BucketFlux), rows, cols)``
    in millimetres (mm); ``fluxes[BucketFlux.RUNOFF]`` is the runoff field.
    A run's flux history has a leading time axis:
    ``flux_history[:, BucketFlux.RUNOFF]``.

    INFILTRATION : rain that entered the store
    RUNOFF : rain that did not fit
    EVAPORATION : water that left the store to the air
    """

    INFILTRATION = 0
    RUNOFF = 1
    EVAPORATION = 2


def t():
    """Indices are 0, 1, 2 in declared order, usable directly as array indices, and names round-trip."""
    assert [f.value for f in BucketFlux] == [0, 1, 2]
    assert len(BucketFlux) == 3
    assert BucketFlux.RUNOFF == 1 and BucketFlux["EVAPORATION"] is BucketFlux.EVAPORATION
    import numpy as np

    a = np.arange(3 * 2 * 2).reshape(3, 2, 2)
    assert a[BucketFlux.EVAPORATION][0, 0] == 8
