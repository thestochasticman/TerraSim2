import math
from pathlib import Path

import numpy as np
import zarr

from terrasim2.f.load_model_inputs import load_model_inputs
from terrasim2.f.load_run_result import load_run_result
from terrasim2.f.load_site_observations import load_site_observations
from terrasim2.f.pair_run_with_observations import pair_run_with_observations
from terrasim2.f.score_pairs import score_pairs
from terrasim2.f.score_pairs_by_key import score_pairs_by_key


def read_comparison(inputs_folder: Path, observations_folder: Path, store_folder: Path, root_depth: float) -> dict:
    """How a run compares with its site's observations, for the days written so far.

    Parameters
    ----------
    inputs_folder : Path
        The run's ``model_inputs`` folder, for the soil.
    observations_folder : Path
        The site's ``observations`` folder.
    store_folder : Path
        The run's zarr store.
    root_depth : float, m
        The run's root depth; the soil's wilting point and the depth the
        stored water is spread over come from it.

    Returns
    -------
    dict
        ``days_written``; ``n_points`` and ``n_paired`` (observations with
        a modelled value so far); ``root_depth`` (m); ``layers``, the
        distinct depth intervals observed, each ``{top, bottom, n}`` in m;
        ``stations``, the station names; ``overall``, the scores of
        ``score_pairs`` over every paired observation; ``by_date``, one
        entry per survey date with ``date``, ``t`` (the run's day index)
        and the scores; ``by_station``, one per station with ``station``
        (its index) and the scores. Scores are in m3 m-3, NaN as null.
    """
    inputs = load_model_inputs(inputs_folder)
    if inputs.soil is None:
        raise ValueError(f"model inputs at {inputs_folder} carry no soil, so a run cannot be read as a water content")
    hydraulics = inputs.soil.compute_hydraulics(root_depth)
    observations = load_site_observations(observations_folder)
    group = zarr.open_group(Path(store_folder), mode="r")
    written = int(group.attrs.get("days_written", 0))
    result = load_run_result(store_folder, allow_incomplete=True)
    modelled = pair_run_with_observations(result, observations, hydraulics, days_available=written)

    day_of = {str(d): int(t) for t, d in enumerate(result.dates)}
    by_date = [{"date": date, "t": day_of.get(date), **_clean(scores)} for date, scores in score_pairs_by_key(observations.vwc, modelled, observations.dates).items()]
    by_station = [{"station": station, **_clean(scores)} for station, scores in score_pairs_by_key(observations.vwc, modelled, observations.station).items()]
    intervals, counts = np.unique(np.stack([observations.depth_top, observations.depth_bottom], axis=1), axis=0, return_counts=True)
    return {
        "days_written": written,
        "n_points": observations.n_points,
        "n_paired": int(np.isfinite(modelled).sum()),
        "root_depth": root_depth,
        "layers": [{"top": float(top), "bottom": float(bottom), "n": int(n)} for (top, bottom), n in zip(intervals, counts)],
        "stations": observations.stations,
        "overall": _clean(score_pairs(observations.vwc, modelled)),
        "by_date": by_date,
        "by_station": by_station,
    }


def _clean(scores: dict) -> dict:
    """NaN is not JSON; serve it as null."""
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in scores.items()}


def t():
    """A complete tarrawarra run: every observation is paired, there is a row per survey date with the run's day
    index, the overall scores agree with the pairing done directly, and the JSON has no NaN."""
    import json
    import tempfile

    from app.api.f.execute_run import execute_run
    from app.api.f.find_inputs import find_inputs
    from app.api.f.find_observations import find_observations
    from app.api.k.run_request import RunRequest

    inputs_folder = find_inputs("tarrawarra")
    store = execute_run(RunRequest(stub="tarrawarra", write_every_days=64, record_fluxes=False), inputs_folder, Path(tempfile.mkdtemp()) / "store.zarr")
    c = read_comparison(inputs_folder, find_observations("tarrawarra"), store, 0.3)
    assert c["days_written"] == 432 and c["n_points"] == c["n_paired"] == 8644
    assert c["layers"] == [{"top": 0.0, "bottom": 0.3, "n": 8644}] and len(c["stations"]) == 3610
    assert len(c["by_date"]) == 19 and c["by_date"][0]["date"] == "1995-09-25" and c["by_date"][0]["t"] == 0
    assert all(row["n"] > 0 for row in c["by_date"]) and sum(row["n"] for row in c["by_date"]) == 8644
    assert len(c["by_station"]) == 3610 and c["by_station"][0]["station"] == 0
    assert c["overall"]["n"] == 8644 and c["overall"]["bias"] < 0, "the bucket cannot reach contents above field capacity"
    assert 0 < c["overall"]["rmse"] < 0.5 and -1 < c["overall"]["r"] < 1
    json.dumps(c)
    assert all(v is None for v in c["by_station"][0].values() if isinstance(v, float) and math.isnan(v))


if __name__ == "__main__":
    t()
