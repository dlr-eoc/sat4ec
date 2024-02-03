"""Test anomaly detection."""
from __future__ import annotations

import unittest
from pathlib import Path

from fiona import errors as ferrors
from fiona.collection import Collection
from shapely import errors
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon

from sat4ec.aoi_check import AOI

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestAOI(unittest.TestCase):
    """Encapsulates testing methods."""

    def __init__(self: TestAOI, *args: int, **kwargs: int) -> None:
        """Initialize TestAOI class."""
        super().__init__(*args, **kwargs)

    def test_open_aoi_file(self: TestAOI) -> None:
        """Test open AOI file."""
        # provide as pathlib.Path
        with AOI(data=TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson")) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.filename, Path))
            self.assertTrue(isinstance(aoi_collection.aoi, Collection))

        # provide as string
        with AOI(data=str(TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson").absolute())) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.filename, Path))
            self.assertTrue(isinstance(aoi_collection.aoi, Collection))

    def test_fail_open_aoi_file(self: TestAOI) -> None:
        """Test open missing AOI file."""
        # provide as pathlib.Path
        with self.assertRaises(ferrors.DriverError):
            aoi_collection = AOI(data=TEST_DIR.joinpath("AOIs", "MISSING.geojson"))
            aoi_collection.close()

        with self.assertRaises(TypeError):
            aoi_collection = AOI(data=str(TEST_DIR.joinpath("AOIs", "MISSING.geojson").absolute()))
            aoi_collection.close()

    def test_get_aoi_features(self: TestAOI) -> None:
        """Test AOI with features."""
        # provide as pathlib.Path
        with AOI(data=TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson")) as aoi_collection:
            features = list(aoi_collection.get_feature())
            feature = features[0]

            self.assertTrue(isinstance(features, list))

            if len(features) > 1:
                self.assertTrue(isinstance(feature.geometry, MultiPolygon))

            elif len(features) == 1:
                if aoi_collection.aoi_split:
                    self.assertTrue(isinstance(feature.geometry, Polygon))

                else:
                    self.assertTrue(isinstance(feature.geometry, MultiPolygon))

    def test_get_aoi_no_features(self: TestAOI) -> None:
        """Test empty AOI."""
        # provide as pathlib.Path
        with AOI(data=TEST_DIR.joinpath("AOIs", "empty.geojson")) as aoi_collection:
            self.assertEqual(len(aoi_collection.features), 0)

    def test_aoi_from_polygon(self: TestAOI) -> None:
        """Test AOI from polygon."""
        pol = Polygon(((11, 48), (12, 48), (12, 49), (11, 49), (11, 48)))

        with AOI(data=pol) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.geometry, Polygon))
            self.assertTrue(isinstance(aoi_collection.record, dict))

    def test_aoi_from_wkt(self: TestAOI) -> None:
        """Test AOI from WKT."""
        pol = "POLYGON((11 48, 12 48, 12 49, 11 49, 11 48))"

        with AOI(data=pol) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.geometry, Polygon))
            self.assertTrue(isinstance(aoi_collection.record, dict))

    def test_aoi_from_wkt_errors(self: TestAOI) -> None:
        """Test AOI from errorness WKT string."""
        pol = "POLYGON((11, 48), (12, 48), (12, 49), (11, 49), (11, 48))"

        with self.assertRaises(errors.GEOSException):
            aoi_collection = AOI(data=pol)
            aoi_collection.close()

        pol = "polygon((11, 48), (12, 48), (12, 49), (11, 49), (11, 48))"

        with self.assertRaises(TypeError):
            aoi_collection = AOI(data=pol)
            aoi_collection.close()
