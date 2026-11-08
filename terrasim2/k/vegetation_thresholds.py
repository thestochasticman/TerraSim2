from dataclasses import dataclass


@dataclass(frozen=True)
class VegetationThresholds:
    """The rule that tells trees from grass in a year of NDVI.

    Trees keep their canopy through the brownest season; grass and crops
    do not. So a cell is a tree where its NDVI stays green at its lowest
    and swings little over the year. The swing is what carries between
    sites: an evergreen canopy moves by a fifth or less, while grass
    swings by a third to a half at a dry site and still by a quarter at a
    temperate one whose pasture never browns off.

    Attributes
    ----------
    tree_low_min : float, dimensionless
        The lowest NDVI (the 10th percentile over the year) a tree cell
        keeps; at or above it the cell may be tree. Rules out bare ground
        and water, which also swing little. Within [-1, 1].
    tree_amplitude_max : float, dimensionless
        The largest swing (90th minus 10th percentile) a tree cell shows;
        above it the cell is grass however green its low. Non-negative.
    """

    tree_low_min: float = 0.4
    tree_amplitude_max: float = 0.2

    def __post_init__(self):
        if not -1 <= self.tree_low_min <= 1:
            raise ValueError(f"tree_low_min must be within [-1, 1], got {self.tree_low_min}")
        if not self.tree_amplitude_max >= 0:
            raise ValueError(f"tree_amplitude_max must be non-negative, got {self.tree_amplitude_max}")


def t():
    """Defaults, bounds and immutability."""
    p = VegetationThresholds()
    assert (p.tree_low_min, p.tree_amplitude_max) == (0.4, 0.2)
    assert VegetationThresholds(tree_low_min=0.5).tree_low_min == 0.5
    for bad in (dict(tree_low_min=1.5), dict(tree_amplitude_max=-0.1)):
        try:
            VegetationThresholds(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")
    try:
        p.tree_low_min = 0.3  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("expected the thresholds to be frozen")
