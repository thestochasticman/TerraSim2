import hashlib
import json

from app.api.k.run_request import RunRequest


def compute_run_id(request: RunRequest) -> str:
    """A stable id for a run: the same request always maps to the same id.

    Parameters
    ----------
    request : RunRequest

    Returns
    -------
    str
        The stub followed by the first 12 hex digits of the SHA-256 of the
        request's canonical JSON, for example ``"tarrawarra-3f9a1c0b7e2d"``.
    """
    canonical = json.dumps(request.model_dump(), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:12]
    return f"{request.stub}-{digest}"


def t():
    """Equal requests share an id; any changed field changes it; the stub is readable in it."""
    a = compute_run_id(RunRequest(stub="tarrawarra"))
    b = compute_run_id(RunRequest(stub="tarrawarra", write_every_days=1, stress_exponent=1.0))
    c = compute_run_id(RunRequest(stub="tarrawarra", stress_exponent=2.0))
    d = compute_run_id(RunRequest(stub="esdale"))
    assert a == b and a != c and a != d
    assert a.startswith("tarrawarra-") and len(a) == len("tarrawarra-") + 12
