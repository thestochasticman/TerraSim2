import numpy as np
import numpy.typing as npt


class SoilHydraulics:
    """What a step needs to know about each cell's soil, over the root depth, as arrays.

    Built once per run: from the soil layers at the run's root depth by
    ``SoilLayers.compute_hydraulics``, or from a bare capacity array for
    inputs that carry no soil. Capacity is always present; the conductivity
    fields are present only when a soil curve is known, and a step that
    needs them calls ``require_conductivity``.

    Parameters
    ----------
    capacity : array_like, mm
        Plant-available water each cell can hold, shape (rows, cols).
    root_depth : float, m, optional
        The depth the fields were evaluated over.
    k_sat : array_like, kg s m-3, optional
        Saturated hydraulic conductivity per cell.
    b : array_like, dimensionless, optional
        Campbell's shape parameter per cell.
    theta_s : array_like, m3 m-3, optional
        Saturated water content per cell.
    theta_fc : array_like, m3 m-3, optional
        Water content at field capacity, -33 J/kg, per cell.
    theta_wp : array_like, m3 m-3, optional
        Water content at wilting point, -1500 J/kg, per cell.

    Attributes
    ----------
    capacity, root_depth, k_sat, b, theta_s, theta_fc, theta_wp : as given, as arrays
    shape : tuple[int, int], dimensionless
    has_conductivity : bool
    """

    FIELDS = ("k_sat", "b", "theta_s", "theta_fc", "theta_wp")

    def __init__(
        self,
        capacity: npt.ArrayLike,
        root_depth: float | None = None,
        k_sat: npt.ArrayLike | None = None,
        b: npt.ArrayLike | None = None,
        theta_s: npt.ArrayLike | None = None,
        theta_fc: npt.ArrayLike | None = None,
        theta_wp: npt.ArrayLike | None = None,
    ):
        self.capacity = np.asarray(capacity, dtype=np.float64)
        if self.capacity.ndim != 2:
            raise ValueError("capacity must be 2-D")
        given = {"k_sat": k_sat, "b": b, "theta_s": theta_s, "theta_fc": theta_fc, "theta_wp": theta_wp}
        present = [k for k, v in given.items() if v is not None]
        if present and len(present) != len(self.FIELDS):
            raise ValueError(f"conductivity fields must all be given or none; got {present}")
        for name, value in given.items():
            arr = None if value is None else np.asarray(value, dtype=np.float64)
            if arr is not None and arr.shape != self.capacity.shape:
                raise ValueError(f"{name} must have the capacity's shape {self.capacity.shape}")
            setattr(self, name, arr)
        self.root_depth = None if root_depth is None else float(root_depth)
        if self.root_depth is not None and not self.root_depth > 0:
            raise ValueError("root_depth must be positive")

    @property
    def shape(self) -> tuple[int, int]:
        return self.capacity.shape

    @property
    def has_conductivity(self) -> bool:
        return self.k_sat is not None

    @property
    def free_capacity(self) -> np.ndarray:
        """Pore space above field capacity per cell, mm: what can hold free, drainable water.

        ``(theta_s - theta_fc) * root_depth``, so it needs the conductivity
        fields and the root depth.
        """
        self.require_conductivity("free_capacity")
        return (self.theta_s - self.theta_fc) * self.root_depth * 1000.0

    def require_conductivity(self, step_name: str) -> None:
        """Raise a clear error when a step needs the conductivity fields and they are absent."""
        if not self.has_conductivity or self.root_depth is None:
            raise ValueError(f"{step_name} needs soil hydraulics with conductivity and a root depth; these inputs carry no soil curve")


def t1():
    """Capacity alone is enough for a closed bucket; a conductive step is refused until the fields exist."""
    h = SoilHydraulics(capacity=np.full((2, 3), 40.0))
    assert h.shape == (2, 3) and not h.has_conductivity and h.root_depth is None
    try:
        h.require_conductivity("step_x")
    except ValueError as err:
        assert "step_x" in str(err)
    else:
        raise AssertionError("expected ValueError")
    full = SoilHydraulics(np.full((2, 3), 40.0), 0.3, np.full((2, 3), 1e-3), np.full((2, 3), 3.0), np.full((2, 3), 0.45), np.full((2, 3), 0.25), np.full((2, 3), 0.1))
    assert full.has_conductivity and full.root_depth == 0.3
    full.require_conductivity("step_x")
    assert np.allclose(full.free_capacity, (0.45 - 0.25) * 0.3 * 1000)
    try:
        h.free_capacity
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for free_capacity without a curve")


def t2():
    """Partial fields, a mismatched shape, a 1-D capacity and a non-positive depth are refused."""
    cap = np.full((2, 3), 40.0)
    for kwargs in (
        dict(capacity=cap, k_sat=cap),
        dict(capacity=cap, k_sat=cap, b=cap, theta_s=cap, theta_fc=cap, theta_wp=np.zeros((3, 3))),
        dict(capacity=np.ones(3)),
        dict(capacity=cap, root_depth=0.0),
    ):
        try:
            SoilHydraulics(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {list(kwargs)}")


def t():
    t1()
    t2()
