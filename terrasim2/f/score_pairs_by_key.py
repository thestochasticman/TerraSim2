import numpy as np

from terrasim2.f.score_pairs import score_pairs


def score_pairs_by_key(observed: np.ndarray, modelled: np.ndarray, keys: np.ndarray) -> dict:
    """``score_pairs`` for each group of pairs sharing a key, keys in sorted order.

    Parameters
    ----------
    observed, modelled : array_like, same units
        Shape (N,).
    keys : array_like
        Shape (N,); anything NumPy can sort and compare, such as dates,
        station indices or strings.

    Returns
    -------
    dict
        Key (as a Python scalar) to that group's scores, every key present
        even when none of its pairs are finite.
    """
    observed, modelled, keys = np.asarray(observed), np.asarray(modelled), np.asarray(keys)
    if not observed.shape == modelled.shape == keys.shape:
        raise ValueError(f"observed {observed.shape}, modelled {modelled.shape} and keys {keys.shape} must have one shape")
    unique, inverse = np.unique(keys, return_inverse=True)
    return {_scalar(key): score_pairs(observed[inverse == k], modelled[inverse == k]) for k, key in enumerate(unique)}


def _scalar(key):
    return str(key) if np.issubdtype(np.asarray(key).dtype, np.datetime64) else key.item()


def t():
    """Groups by date and by station index, keys come out sorted as plain scalars, and a shape mismatch is refused."""
    o = np.array([0.2, 0.3, 0.4, 0.5, 0.6])
    m = np.array([0.25, 0.35, 0.4, 0.5, np.nan])
    dates = np.array(["2024-01-05", "2024-01-05", "2024-01-02", "2024-01-02", "2024-01-09"], dtype="datetime64[D]")
    by_date = score_pairs_by_key(o, m, dates)
    assert list(by_date) == ["2024-01-02", "2024-01-05", "2024-01-09"]
    assert by_date["2024-01-02"]["n"] == 2 and by_date["2024-01-02"]["rmse"] == 0.0
    assert by_date["2024-01-05"]["n"] == 2 and abs(by_date["2024-01-05"]["bias"] - 0.05) < 1e-12
    assert by_date["2024-01-09"]["n"] == 0
    by_station = score_pairs_by_key(o, m, np.array([1, 0, 1, 0, 0]))
    assert list(by_station) == [0, 1] and isinstance(next(iter(by_station)), int)
    assert by_station[0]["n"] == 2 and by_station[1]["n"] == 2
    try:
        score_pairs_by_key(o, m, dates[:3])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for a shape mismatch")
