from typing import Any, Protocol

import numpy as np

from terrasim2.k.soil_hydraulics import SoilHydraulics
from terrasim2.k.terrain_derivatives import TerrainDerivatives


class StepFunction(Protocol):
    """What run_model expects of a process step.

    A step advances every cell by one day. It is pure: arrays in, arrays
    out, nothing mutated.

    Parameters
    ----------
    moisture : ndarray (rows, cols), millimetres (mm)
        Water in each cell's store at the start of the day.
    soil_hydraulics : SoilHydraulics
        Each cell's soil over the root depth: capacity always, and the
        conductivity fields when the inputs carry a curve. A step that
        needs the latter calls ``require_conductivity``.
    rain : ndarray (rows, cols), millimetres (mm)
        Rain arriving on each cell during the day.
    pet : ndarray (rows, cols), millimetres (mm)
        Reference evapotranspiration demand for the day.
    terrain_derivatives : TerrainDerivatives
        What follows from the terrain's shape: flow directions, slopes and
        the rest, computed on first use. A step that treats cells as
        independent takes it and does not read it.
    params : Any
        The step's own parameter dataclass: tunables only.

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
        soil_hydraulics: SoilHydraulics,
        rain: np.ndarray,
        pet: np.ndarray,
        terrain_derivatives: TerrainDerivatives,
        params: Any,
    ) -> tuple[np.ndarray, np.ndarray]: ...


def t():
    """A plain function with the right signature satisfies the protocol at type-check time; at runtime it is callable."""
    from terrasim2.k.terrain_grid import TerrainGrid

    def no_change(moisture, soil_hydraulics, rain, pet, terrain_derivatives, params):
        return moisture.copy(), np.zeros((1, *moisture.shape))

    step: StepFunction = no_change
    derivatives = TerrainDerivatives(TerrainGrid(elevation=np.zeros((2, 2)), cell_size=1.0))
    out, fluxes = step(np.ones((2, 2)), SoilHydraulics(np.ones((2, 2))), np.zeros((2, 2)), np.zeros((2, 2)), derivatives, None)
    assert np.all(out == 1.0) and fluxes.shape == (1, 2, 2)
