import unittest
from fiona.collection import Collection
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely import errors
from source.aoi_check import AOI
from pathlib import Path


class TestAOI(unittest.TestCase):
    def test_open_aoi_file(self):
        # provide as pathlib.Path
        with AOI(data=Path.cwd().joinpath("testdata", "gent_parking_lot.geojson")) as aoi:
            self.assertTrue(isinstance(aoi.filename, Path))
            self.assertTrue(isinstance(aoi.aoi, Collection))

        # provide as string
        with AOI(data=str(Path.cwd().joinpath("testdata", "gent_parking_lot.geojson").absolute())) as aoi:
            self.assertTrue(isinstance(aoi.filename, Path))
            self.assertTrue(isinstance(aoi.aoi, Collection))

    def test_get_aoi_features(self):
        # provide as pathlib.Path
        with AOI(data=Path.cwd().joinpath("testdata", "munich_ikea.geojson")) as aoi:
            aoi.get_features()

            self.assertTrue(isinstance(aoi.features, list))

            if len(aoi.features) > 1:
                self.assertTrue(isinstance(aoi.geometry, MultiPolygon))

            elif len(aoi.features) == 1:
                self.assertTrue(isinstance(aoi.geometry, Polygon))

    def test_get_aoi_no_features(self):
        # provide as pathlib.Path
        with AOI(data=Path.cwd().joinpath("testdata", "empty.geojson")) as aoi:
            with self.assertRaises(AttributeError):
                aoi.get_features()

    def test_aoi_from_polygon(self):
        pol = Polygon(((11, 48), (12, 48), (12, 49), (11, 49), (11, 48)))

        with AOI(data=pol) as aoi:
            self.assertTrue(isinstance(aoi.geometry, Polygon))
            self.assertTrue(isinstance(aoi.record, dict))

    def test_aoi_from_wkt(self):
        pol = "POLYGON((11 48, 12 48, 12 49, 11 49, 11 48))"

        with AOI(data=pol) as aoi:
            self.assertTrue(isinstance(aoi.geometry, Polygon))
            self.assertTrue(isinstance(aoi.record, dict))

    def test_aoi_from_wkt_errors(self):
        pol = "POLYGON((11, 48), (12, 48), (12, 49), (11, 49), (11, 48))"

        with self.assertRaises(errors.GEOSException):
            with AOI(data=pol) as aoi:
                self.assertTrue(isinstance(aoi.record, dict))

        pol = "polygon((11, 48), (12, 48), (12, 49), (11, 49), (11, 48))"

        with self.assertRaises(AttributeError):
            with AOI(data=pol) as aoi:
                self.assertTrue(isinstance(aoi.record, dict))
