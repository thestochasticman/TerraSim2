import hashlib
import json

from app.api.k.run_request import RunRequest


def compute_run_id(request: RunRequest, inputs_key: str = "") -> str:
    """A stable id for a run: the same request on the same inputs always maps to the same id.

    Parameters
    ----------
    request : RunRequest
    inputs_key : str
        What identifies the site's prepared inputs, from ``read_inputs_key``,
        so a store computed on older inputs is not served for the current ones.

    Returns
    -------
    str
        The stub followed by the first 12 hex digits of the SHA-256 of the
        request's canonical JSON plus the key, for example
        ``"tarrawarra-3f9a1c0b7e2d"``.
    """
    canonical = json.dumps({**request.model_dump(), "inputs": inputs_key}, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:12]
    return f"{request.stub}-{digest}"


def t():
    """Equal requests on the same inputs share an id; any changed field, or other inputs, changes it."""
    a = compute_run_id(RunRequest(stub="tarrawarra"), "v2@t0")
    b = compute_run_id(RunRequest(stub="tarrawarra", write_every_days=1, stress_exponent=1.0), "v2@t0")
    c = compute_run_id(RunRequest(stub="tarrawarra", stress_exponent=2.0), "v2@t0")
    d = compute_run_id(RunRequest(stub="esdale"), "v2@t0")
    e = compute_run_id(RunRequest(stub="tarrawarra"), "v2@t1")
    f = compute_run_id(RunRequest(stub="tarrawarra", root_depth=1.0), "v2@t0")
    assert a == b and a != c and a != d and a != e and a != f
    assert a.startswith("tarrawarra-") and len(a) == len("tarrawarra-") + 12
