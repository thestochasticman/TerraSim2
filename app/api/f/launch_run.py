import subprocess
import sys
from pathlib import Path

from app.api.k.run_request import RunRequest

REPO = Path(__file__).resolve().parents[3]


def launch_run(request: RunRequest, inputs_folder: Path, run_folder: Path) -> subprocess.Popen:
    """Start ``execute_run`` for a request in its own process and return at once.

    Writes ``{run_folder}/request.json`` first, so the run can be identified
    even if the worker dies. The worker writes ``{run_folder}/store.zarr``
    and logs to ``{run_folder}/worker.log``.

    Parameters
    ----------
    request : RunRequest
    inputs_folder : Path
        A prepared ``model_inputs`` folder.
    run_folder : Path
        Created if missing.

    Returns
    -------
    subprocess.Popen
        The worker. ``poll()`` is None while it runs, 0 when it finished cleanly.
    """
    run_folder = Path(run_folder)
    run_folder.mkdir(parents=True, exist_ok=True)
    request_path = run_folder / "request.json"
    request_path.write_text(request.model_dump_json(indent=2) + "\n")
    log = open(run_folder / "worker.log", "w")
    return subprocess.Popen(
        [sys.executable, "-m", "app.api.f.execute_run", str(request_path), str(inputs_folder), str(run_folder / "store.zarr")],
        cwd=REPO,
        stdout=log,
        stderr=subprocess.STDOUT,
    )


def t():
    """The worker runs the example site in the background, exits 0, and leaves a complete store and the request."""
    import json
    import tempfile

    from app.api.f.find_inputs import find_inputs
    from app.api.f.read_run_status import read_run_status

    run_folder = Path(tempfile.mkdtemp()) / "run"
    proc = launch_run(RunRequest(stub="example", write_every_days=3), find_inputs("example"), run_folder)
    proc.wait(timeout=120)
    assert proc.returncode == 0, (run_folder / "worker.log").read_text()
    assert json.loads((run_folder / "request.json").read_text())["write_every_days"] == 3
    status = read_run_status(run_folder / "store.zarr")
    assert status["status"] == "complete" and status["days_written"] == status["n_days"] == 31
