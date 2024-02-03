"""Configure execution parameters."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class Config:
    """Encapsulate configuration to execute main script."""

    def __init__(
        self: Config,
        aoi: str,
        working_dir: Path,
        out_dir: Path,
        aoi_dir: Path,
        orbit: str = "asc",
        ext: str = "geojson",
        start: str | None = None,
        end: str | None = None,
        monthly: bool = False,
        regression: str = "spline",
        linear: bool = False,
        linear_fill: bool = False,
        aoi_split: bool = False,
        overwrite_raw: bool = False,
    ) -> None:
        """Initialize Config class."""
        self.orbit = orbit
        self.pol = "VH"
        self.aoi_dir = aoi_dir
        self.aoi = aoi
        self.ext = ext
        self.start = start
        self.end = end
        self.working_dir = working_dir
        self.out_dir = out_dir
        self.monthly = monthly
        self.regression = regression
        self.linear = linear
        self.linear_fill = linear_fill
        self.aoi_split = aoi_split
        self.overwrite_raw = overwrite_raw

        self._get_out_dir()
        self._get_aoi_dir()
        self._get_aoi()

    def _get_out_dir(self: Config) -> None:
        self.out_dir = self.working_dir.joinpath(self.out_dir, self.aoi)

    def _get_aoi_dir(self: Config) -> None:
        self.aoi_dir = self.working_dir.joinpath(self.aoi_dir)
        self.aoi_dir.exists()

    def _get_aoi(self: Config) -> None:
        self.aoi = self.aoi_dir.joinpath(f"{self.aoi}.{self.ext}")
        self.aoi_name = self.aoi.stem
