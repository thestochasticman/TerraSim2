import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response

from app.api.f.compute_run_id import compute_run_id
from app.api.f.find_inputs import DEV_DATA, find_inputs
from app.api.f.launch_run import launch_run
from app.api.f.read_moisture_day import read_moisture_day
from app.api.f.read_run_status import read_run_status
from app.api.f.read_series import read_series
from app.api.f.read_terrain import read_terrain
from app.api.k.run_request import RunRequest


def create_app(runs_root: Path, inputs_roots: tuple[Path, ...] = (DEV_DATA,)) -> FastAPI:
    """Build the service.

    Routes
    ------
    GET  /sites                       stubs with prepared inputs under ``inputs_roots``
    POST /runs                        body RunRequest -> {run_id, status}; starts the run
                                      unless its store is already complete or in progress
    GET  /runs/{run_id}               status (missing, running, complete, failed),
                                      days_written, n_days, rows, cols, dates, meta
    GET  /runs/{run_id}/terrain       elevation and capacity for the run's site
    GET  /runs/{run_id}/moisture/{t}  one day as little-endian float32 bytes; 409 until written
    GET  /runs/{run_id}/series        grid-mean daily series for the days written

    Parameters
    ----------
    runs_root : Path
        Each run lives at ``{runs_root}/{run_id}/`` with ``request.json``,
        ``store.zarr`` and ``worker.log``.
    inputs_roots : tuple of Path
        Where ``find_inputs`` looks, in order.

    Returns
    -------
    FastAPI
    """
    runs_root = Path(runs_root)
    workers: dict[str, subprocess.Popen] = {}
    app = FastAPI(title="TerraSim2")

    def run_folder(run_id: str) -> Path:
        return runs_root / run_id

    def request_of(run_id: str) -> RunRequest:
        path = run_folder(run_id) / "request.json"
        if not path.exists():
            raise HTTPException(404, f"unknown run {run_id}")
        return RunRequest.model_validate_json(path.read_text())

    def worker_failed(run_id: str) -> bool:
        worker = workers.get(run_id)
        return worker is not None and worker.poll() not in (None, 0)

    @app.get("/sites")
    def sites() -> list[str]:
        found = set()
        for root in inputs_roots:
            for manifest in Path(root).glob("*/model_inputs/manifest.json"):
                found.add(manifest.parents[1].name)
        return sorted(found)

    @app.post("/runs")
    def start(request: RunRequest) -> dict:
        try:
            inputs = find_inputs(request.stub, inputs_roots)
        except FileNotFoundError as err:
            raise HTTPException(404, str(err)) from err
        run_id = compute_run_id(request)
        if read_run_status(run_folder(run_id) / "store.zarr")["status"] == "complete":
            return {"run_id": run_id, "status": "complete"}
        worker = workers.get(run_id)
        if worker is None or worker.poll() is not None:
            workers[run_id] = launch_run(request, inputs, run_folder(run_id))
        return {"run_id": run_id, "status": "running"}

    @app.get("/runs/{run_id}")
    def status(run_id: str) -> dict:
        request_of(run_id)
        s = read_run_status(run_folder(run_id) / "store.zarr")
        if s["status"] in ("missing", "running") and worker_failed(run_id):
            s = {**s, "status": "failed"}
        return {"run_id": run_id, **s}

    @app.get("/runs/{run_id}/terrain")
    def terrain(run_id: str) -> dict:
        request = request_of(run_id)
        return read_terrain(find_inputs(request.stub, inputs_roots))

    @app.get("/runs/{run_id}/moisture/{t}")
    def moisture(run_id: str, t: int) -> Response:
        request_of(run_id)
        try:
            raw = read_moisture_day(run_folder(run_id) / "store.zarr", t)
        except (IndexError, FileNotFoundError) as err:
            raise HTTPException(409, str(err)) from err
        return Response(content=raw, media_type="application/octet-stream")

    @app.get("/runs/{run_id}/series")
    def series(run_id: str) -> dict:
        request = request_of(run_id)
        store = run_folder(run_id) / "store.zarr"
        if read_run_status(store)["status"] == "missing":
            raise HTTPException(409, "run has not started writing yet")
        return read_series(find_inputs(request.stub, inputs_roots), store)

    return app


def t():
    """Through HTTP: start a run, poll it to completion, read a day and the series, repost and get the cache, and get 404s for unknowns."""
    import tempfile
    import time

    import numpy as np
    from fastapi.testclient import TestClient

    client = TestClient(create_app(Path(tempfile.mkdtemp()) / "runs"))
    assert "tarrawarra" in client.get("/sites").json()

    body = {"stub": "example", "write_every_days": 4}
    started = client.post("/runs", json=body).json()
    run_id = started["run_id"]
    assert started["status"] == "running" and run_id.startswith("example-")

    s = {}
    for _ in range(600):
        s = client.get(f"/runs/{run_id}").json()
        if s["status"] == "complete":
            break
        assert s["status"] in ("running", "missing"), s
        time.sleep(0.1)
    assert s["status"] == "complete" and s["days_written"] == s["n_days"] == 31, s

    terrain = client.get(f"/runs/{run_id}/terrain").json()
    assert (terrain["rows"], terrain["cols"]) == (s["rows"], s["cols"])

    raw = client.get(f"/runs/{run_id}/moisture/30").content
    field = np.frombuffer(raw, dtype="<f4").reshape(s["rows"], s["cols"])
    assert np.isfinite(field).all() and 0 <= field.min() and field.max() <= 100.0
    assert client.get(f"/runs/{run_id}/moisture/31").status_code == 409

    series = client.get(f"/runs/{run_id}/series").json()
    assert len(series["dates"]) == 31 and abs(series["moisture"][-1] - field.mean()) < 1e-3

    assert client.post("/runs", json=body).json() == {"run_id": run_id, "status": "complete"}
    assert client.post("/runs", json={"stub": "nowhere"}).status_code == 404
    assert client.get("/runs/not-a-run").status_code == 404
