import sys
from pathlib import Path

from troi import config as troi_config

from app.api.f.create_app import create_app
from app.api.f.find_inputs import DEV_DATA


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the service with uvicorn.

    Runs go to ``{troi out_dir}/terrasim2_runs``. Inputs are looked up in
    the Troi output directory first, then the committed ``dev_data``.

    Usage, from the repo root in the borevitz_lab environment:
        python -m app.api.f.serve [port]
    """
    import uvicorn

    app = create_app(Path(troi_config.out_dir) / "terrasim2_runs", inputs_roots=(Path(troi_config.out_dir), DEV_DATA))
    uvicorn.run(app, host=host, port=port, log_level="info")


def t():
    """The app the server would run builds with the real roots and lists the committed sites."""
    from fastapi.testclient import TestClient

    app = create_app(Path(troi_config.out_dir) / "terrasim2_runs", inputs_roots=(Path(troi_config.out_dir), DEV_DATA))
    sites = TestClient(app).get("/sites").json()
    assert {"example", "tarrawarra", "nerrigundah"} <= set(sites)


if __name__ == "__main__":
    serve(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
