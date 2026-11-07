import math

import numpy as np


def score_pairs(observed: np.ndarray, modelled: np.ndarray) -> dict:
    """How well modelled values match observed ones, by the usual soil moisture scores.

    Pairs where either value is not finite are left out. With fewer than
    two pairs, or no spread in one side, the scores that need them are NaN.

    Parameters
    ----------
    observed, modelled : array_like, same units
        Any shape, broadcast together.

    Returns
    -------
    dict
        ``n`` (int, pairs scored), ``observed_mean``, ``modelled_mean``,
        ``bias`` (modelled minus observed), ``rmse``, ``ubrmse`` (the rmse
        after removing the bias), ``r`` (Pearson), ``nse`` (Nash–Sutcliffe
        efficiency) and ``kge`` (Kling–Gupta efficiency, Gupta et al. 2009),
        all floats in the input units except the dimensionless r, nse and kge.
    """
    o, m = np.broadcast_arrays(np.asarray(observed, dtype=np.float64), np.asarray(modelled, dtype=np.float64))
    keep = np.isfinite(o) & np.isfinite(m)
    o, m = o[keep], m[keep]
    n = int(o.size)
    nan = float("nan")
    if n == 0:
        return {"n": 0, "observed_mean": nan, "modelled_mean": nan, "bias": nan, "rmse": nan, "ubrmse": nan, "r": nan, "nse": nan, "kge": nan}
    error = m - o
    bias = float(error.mean())
    rmse = float(math.sqrt(np.mean(error**2)))
    ubrmse = float(math.sqrt(max(rmse**2 - bias**2, 0.0)))
    o_mean, m_mean = float(o.mean()), float(m.mean())
    o_sd, m_sd = float(o.std()), float(m.std())
    o_spread, m_spread = bool(np.ptp(o) > 0), bool(np.ptp(m) > 0)
    spread = n >= 2 and o_spread and m_spread
    r = float(np.mean((o - o_mean) * (m - m_mean)) / (o_sd * m_sd)) if spread else nan
    nse = float(1.0 - np.sum(error**2) / np.sum((o - o_mean) ** 2)) if n >= 2 and o_spread else nan
    kge = float(1.0 - math.sqrt((r - 1.0) ** 2 + (m_sd / o_sd - 1.0) ** 2 + (m_mean / o_mean - 1.0) ** 2)) if spread and o_mean != 0 else nan
    return {"n": n, "observed_mean": o_mean, "modelled_mean": m_mean, "bias": bias, "rmse": rmse, "ubrmse": ubrmse, "r": r, "nse": nse, "kge": kge}


def t1():
    """Hand-computed: a constant offset is pure bias with no unbiased error and perfect r; a perfect match scores 1."""
    o = np.array([0.2, 0.3, 0.4, 0.5])
    s = score_pairs(o, o + 0.05)
    assert s["n"] == 4 and abs(s["bias"] - 0.05) < 1e-12 and abs(s["rmse"] - 0.05) < 1e-12 and s["ubrmse"] < 1e-9
    assert abs(s["r"] - 1.0) < 1e-12 and abs(s["observed_mean"] - 0.35) < 1e-12 and abs(s["modelled_mean"] - 0.40) < 1e-12
    assert abs(s["nse"] - (1.0 - 4 * 0.05**2 / 0.05)) < 1e-12, "sum of squares about the mean is 0.05"
    assert abs(s["kge"] - (1.0 - 0.40 / 0.35 + 1.0)) < 1e-12, "only the mean ratio term is off"
    perfect = score_pairs(o, o)
    assert perfect["rmse"] == 0.0 and perfect["nse"] == 1.0 and abs(perfect["kge"] - 1.0) < 1e-12


def t2():
    """Non-finite pairs are dropped; a single pair or a flat side gives NaN where a score needs spread; no pairs gives n of 0."""
    s = score_pairs([0.2, np.nan, 0.4, 0.5], [0.25, 0.3, np.nan, 0.45])
    assert s["n"] == 2 and abs(s["bias"]) < 1e-12 and abs(s["rmse"] - 0.05) < 1e-12 and abs(s["ubrmse"] - 0.05) < 1e-12
    assert abs(s["r"] - 1.0) < 1e-12, "both sides rise from the first pair to the second"
    one = score_pairs([0.2], [0.3])
    assert one["n"] == 1 and abs(one["bias"] - 0.1) < 1e-12 and math.isnan(one["r"]) and math.isnan(one["nse"]) and math.isnan(one["kge"])
    flat = score_pairs([0.2, 0.2, 0.2], [0.1, 0.2, 0.3])
    assert math.isnan(flat["r"]) and math.isnan(flat["nse"]) and abs(flat["rmse"] - math.sqrt(0.02 / 3)) < 1e-12
    empty = score_pairs([np.nan], [1.0])
    assert empty["n"] == 0 and all(math.isnan(v) for k, v in empty.items() if k != "n")
    anti = score_pairs([1.0, 2.0, 3.0], [3.0, 2.0, 1.0])
    assert abs(anti["r"] + 1.0) < 1e-12 and abs(anti["nse"] + 3.0) < 1e-12 and abs(anti["kge"] - (1.0 - 2.0)) < 1e-12


def t():
    t1()
    t2()
