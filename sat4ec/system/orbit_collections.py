"""Handle different orbits."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

    from anomaly_detection import Anomalies
    from subset_collections import SubsetCollection

ORBIT_COUNT = 2


class OrbitCollection:
    """Encapsulate data attachment methods per orbit."""

    def __init__(self: OrbitCollection, orbit: str = "asc", monthly: bool = False) -> None:
        """Initialize OrbitCollection class."""
        self.orbit = orbit
        self.monthly = monthly
        self.asc_anomalies = None
        self.des_anomalies = None
        self.asc_subsets = None
        self.des_subsets = None

        self._get_orbits()

    def _get_orbits(self: OrbitCollection) -> None:
        if self.orbit == "both":
            self.orbits = ["asc", "des"]

        else:
            self.orbits = [self.orbit]

    def add_subsets(self: OrbitCollection, subsets: SubsetCollection, orbit: str = "asc") -> None:
        """Define subset collection per orbit."""
        if orbit == "asc":
            self.asc_subsets = subsets

        elif orbit == "des":
            self.des_subsets = subsets

        else:
            raise AttributeError(f"The provided orbit {orbit} is not supported.")

    def add_anomalies(self: OrbitCollection, anomalies: Anomalies, orbit: str = "asc") -> None:
        """Attach anomaly data to orbit collection."""
        if orbit == "asc":
            self.asc_anomalies = anomalies

        elif orbit == "des":
            self.des_anomalies = anomalies

        else:
            raise AttributeError(f"The provided orbit {orbit} is not supported.")

    def get_data(
        self: OrbitCollection,
    ) -> Generator[[SubsetCollection, Anomalies, str, bool], list]:
        """Retrieve data fpr specific orbit."""
        for orbit in self.orbits:
            if orbit == "asc":
                yield self.asc_subsets, self.asc_anomalies, orbit, True  # True for left axis

            elif orbit == "des" and len(self.orbits) == ORBIT_COUNT:
                yield self.des_subsets, self.des_anomalies, orbit, False  # False, to plot DES on right axis

            else:
                yield self.des_subsets, self.des_anomalies, orbit, True  # True for left axis
