"""Prepare input data."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import TracebackType

from pathlib import Path

import fiona
from shapely import from_wkt
from shapely.geometry import mapping, shape
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon


class Feature:
    """Encapsulate AOI feature."""

    def __init__(self: Feature, fid: str | None = None, feature: fiona.collection | None = None) -> None:
        """Initialize Feature class."""
        self.geometry = None
        self.feature = feature
        self.fid = fid
        self.azimuth_group = None

        if self.feature is not None:
            self._get_geometry()
            self._get_fid()
            self._get_azimuth_group()

    def _get_geometry(self: Feature) -> None:
        self.geometry = shape(self.feature["geometry"])

    def _get_fid(self: Feature) -> None:
        if self.feature["properties"].get("id"):  # check if feature holds column with name id
            self.fid = self.feature["properties"]["id"]

        else:
            self.fid = self.feature["id"]

    def _get_azimuth_group(self: Feature) -> None:
        if self.feature["properties"].get("group"):
            self.azimuth_group = self.feature["properties"]["group"]

        else:
            self.azimuth_group = None


class AOI:
    """Encapsulate input operations."""

    def __init__(self: AOI, data: str | Path | Polygon, aoi_split: bool = False, name: str = "aoi") -> None:
        """Initialize AOI class."""
        self.aoi = None
        self.name = name
        self.geometry = None
        self.features = None
        self.schema = None
        self.record = None
        self.aoi_split = aoi_split

        if isinstance(data, str):
            if "POLYGON" in data:  # wkt string
                self.geometry = from_wkt(data)
                self.build_aoi(geometry_type="Polygon", geometry=self.geometry)

            elif Path(data).exists():
                self.filename = Path(data)
                self.load_aoi()
                self.get_features()

            else:
                raise TypeError(f"The provided data {data} cannot be resolved to WKT or to a path.")

        elif isinstance(data, Path):
            self.filename = data
            self.load_aoi()
            self.get_features()

        elif isinstance(data, Polygon):
            self.geometry = data
            self.build_aoi(geometry_type="Polygon", geometry=self.geometry)

        else:
            raise TypeError(f"The provided data {data} is of unsupported type {type(data)}.")

    def __enter__(self: AOI) -> AOI:
        """Get opening handler on context manager."""
        return self

    def __exit__(
        self: AOI,
        exc_type: type(BaseException),
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        """Get closing handler on context manager."""
        self.close()

    def close(self: AOI) -> None:
        """Clode AOI file."""
        if self.aoi is not None:
            self.aoi.close()

    def _build_schema(self: AOI, geometry_type: str = "Polygon") -> None:
        """Write vector file scheme."""
        self.schema = {"geometry": geometry_type, "properties": {"name": "str"}}

    def _build_record(self: AOI, geometry: Polygon) -> None:
        """Build vector file record."""
        self.record = {"geometry": mapping(geometry), "properties": {"name": self.name}}

    def build_aoi(self: AOI, geometry: Polygon, geometry_type: str = "Polygon") -> None:
        """Prepare AOI meta data for vector file output."""
        self._build_schema(geometry_type=geometry_type)
        self._build_record(geometry=geometry)

    def save_aoi(
        self: AOI,
        out_dir: Path,
        driver: str = "GPKG",
        crs: str = "epsg:4326",
        overwrite: bool = True,
    ) -> None:
        """Save AOI vetor file."""
        if not overwrite and out_dir.joinpath(f"{self.name}.{driver.lower()}").exists():
            pass

        else:
            with fiona.open(
                out_dir.joinpath(f"{self.name}.{driver.lower()}"),
                "w",
                driver=driver,
                crs=crs,
                schema=self.schema,
            ) as out:
                out.write(self.record)

    def load_aoi(self: AOI) -> None:
        """Open AOI file."""
        self.aoi = fiona.open(self.filename)

    def get_features(self: AOI) -> None:
        """Get features from opened AOI instance."""
        self.features = list(self.aoi)

    def get_feature(self: AOI) -> Generator[Feature, Feature]:
        """Get AOI feature and its geometry."""
        if self.geometry is not None:
            feature = Feature()
            feature.geometry = self.geometry
            yield feature  # return feature with geometry that has already been computed

        elif self.geometry is None and len(self.features) == 1:
            feature = Feature(feature=self.features[0])
            self.build_aoi(geometry_type="Polygon", geometry=feature.geometry)

            yield feature  # AOI holds a single feature/polygon

        elif self.geometry is None and len(self.features) > 1:
            if self.aoi_split:
                # duplicates functionality self.get_features, but treats features individually
                for f in self.features:
                    feature = Feature(feature=f)
                    yield feature

            else:
                feature = Feature()
                feature.geometry = MultiPolygon([shape(feature["geometry"]) for feature in self.features])
                feature.fid = "0"
                self.build_aoi(geometry_type="MultiPolygon", geometry=feature.geometry)

                yield feature  # AOI holds multiple features/polygons but are merged to a multipolygon

        else:
            raise AttributeError(f"The AOI {self.filename} does not contain any features.")
