from pathlib import Path

import numpy as np
import zarr

from terrasim2.f.get_values_on_cells import get_values_on_cells
from terrasim2.f.load_model_inputs import load_model_inputs
from terrasim2.k.bucket_flux import BucketFlux


def read_series(inputs_folder: Path, store_folder: Path, block_days: int = 64) -> dict:
    """Grid-mean daily series for the days written so far.

    Parameters
    ----------
    inputs_folder : Path
        The run's ``model_inputs`` folder, for rain and pet.
    store_folder : Path
        The run's zarr store, for moisture and fluxes.
    block_days : int, dimensionless
        Days read from the store at a time.

    Returns
    -------
    dict
        ``dates`` (ISO strings) and, each a list of grid means in
        millimetres (mm) with one entry per written day: ``rain``, ``pet``,
        ``moisture``, and if fluxes were stored ``infiltration``, ``runoff``,
        ``evaporation``.
    """
    inputs = load_model_inputs(inputs_folder)
    group = zarr.open_group(Path(store_folder), mode="r")
    written = int(group.attrs.get("days_written", 0))

    rain = [float(get_values_on_cells(inputs.cell_map, inputs.rain, t).mean()) for t in range(written)]
    pet = [float(get_values_on_cells(inputs.cell_map, inputs.pet, t).mean()) for t in range(written)]
    moisture: list[float] = []
    fluxes: dict[str, list[float]] = {f.name.lower(): [] for f in BucketFlux} if "fluxes" in group else {}
    for t0 in range(0, written, block_days):
        t1 = min(t0 + block_days, written)
        moisture.extend(np.asarray(group["moisture"][t0:t1]).mean(axis=(1, 2)).tolist())
        if fluxes:
            block = np.asarray(group["fluxes"][t0:t1]).mean(axis=(2, 3))
            for f in BucketFlux:
                fluxes[f.name.lower()].extend(block[:, f].tolist())

    return {"dates": [str(d) for d in inputs.dates[:written]], "rain": rain, "pet": pet, "moisture": moisture, **fluxes}


def t():
    """Series lengths track days_written, and the grid means close the water balance day by day."""
    import tempfile

    from app.api.f.execute_run import execute_run
    from app.api.f.find_inputs import find_inputs
    from app.api.k.run_request import RunRequest

    inputs_folder = find_inputs("example")
    store = execute_run(RunRequest(stub="example", write_every_days=5), inputs_folder, Path(tempfile.mkdtemp()) / "store.zarr")
    s = read_series(inputs_folder, store, block_days=7)
    n = len(s["dates"])
    assert n == 31 and all(len(s[k]) == n for k in ("rain", "pet", "moisture", "infiltration", "runoff", "evaporation"))
    prev = 0.5 * float(np.load(inputs_folder / "capacity.npy").mean())
    for t in range(n):
        assert abs((s["moisture"][t] - prev) - (s["rain"][t] - s["runoff"][t] - s["evaporation"][t])) < 1e-9, t
        prev = s["moisture"][t]
