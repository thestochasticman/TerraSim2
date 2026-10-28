from typing import Any, Protocol

import numpy as np


class StepFunction(Protocol):
    """What run_model expects of a process step.

    A step advances every cell by one day. It is pure: arrays in, arrays
    out, nothing mutated.

    Parameters
    ----------
    moisture : ndarray (rows, cols), millimetres (mm)
        Water in each cell's store at the start of the day.
    capacity : ndarray (rows, cols), millimetres (mm)
        Each cell's store size.
    rain : ndarray (rows, cols), millimetres (mm)
        Rain arriving on each cell during the day.
    pet : ndarray (rows, cols), millimetres (mm)
        Reference evapotranspiration demand for the day.
    params : Any
        The step's own parameter dataclass.

    Returns
    -------
    moisture : ndarray (rows, cols), millimetres (mm)
        Water in each store at the end of the day.
    fluxes : ndarray (n_fluxes, rows, cols), millimetres (mm)
        What moved during the day. Which index is which flux is fixed by
        an IntEnum the step publishes, for example ``BucketFlux``.
    """

    def __call__(
        self,
        moisture: np.ndarray,
        capacity: np.ndarray,
        rain: np.ndarray,
        pet: np.ndarray,
        params: Any,
    ) -> tuple[np.ndarray, np.ndarray]: ...


def t():
    """A plain function with the right signature satisfies the protocol at type-check time; at runtime it is callable."""

    def no_change(moisture, capacity, rain, pet, params):
        return moisture.copy(), np.zeros((1, *moisture.shape))

    step: StepFunction = no_change
    out, fluxes = step(np.ones((2, 2)), np.ones((2, 2)), np.zeros((2, 2)), np.zeros((2, 2)), None)
    assert np.all(out == 1.0) and fluxes.shape == (1, 2, 2)
