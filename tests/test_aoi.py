import unittest
from fiona import errors as ferrors
from fiona.collection import Collection
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely import errors
from source.aoi_check import AOI
from pathlib import Path


TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestAOI(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestAOI, self).__init__(*args, **kwargs)
        self.data_dir = TEST_DIR.joinpath("vw_wolfsburg2subfeatures")

    def test_open_aoi_file(self):
        # provide as pathlib.Path
        with AOI(data=TEST_DIR.joinpath("AOIs", "vw_wolfsburg2subfeatures.geojson")) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.filename, Path))
            self.assertTrue(isinstance(aoi_collection.aoi, Collection))

        # provide as string
        with AOI(data=str(TEST_DIR.joinpath("AOIs", "vw_wolfsburg2subfeatures.geojson").absolute())) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.filename, Path))
            self.assertTrue(isinstance(aoi_collection.aoi, Collection))

    def test_fail_open_aoi_file(self):
        # provide as pathlib.Path
        with self.assertRaises(ferrors.DriverError):
            with AOI(data=TEST_DIR.joinpath("AOIs", "MISSING.geojson")) as aoi_collection:
                pass

        with self.assertRaises(TypeError):
            with AOI(data=str(TEST_DIR.joinpath("AOIs", "MISSING.geojson").absolute())) as aoi_collection:
                pass

    def test_get_aoi_features(self):
        # provide as pathlib.Path
        with AOI(data=TEST_DIR.joinpath("AOIs", "vw_wolfsburg2subfeatures.geojson")) as aoi_collection:
            features = [feature for feature in aoi_collection.get_feature()]
            feature = features[0]

            self.assertTrue(isinstance(features, list))

            if len(features) > 1:
                self.assertTrue(isinstance(feature.geometry, MultiPolygon))

            elif len(features) == 1:
                if aoi_collection.aoi_split:
                    self.assertTrue(isinstance(feature.geometry, Polygon))

                else:
                    self.assertTrue(isinstance(feature.geometry, MultiPolygon))

    def test_get_aoi_no_features(self):
        # provide as pathlib.Path
        with AOI(data=TEST_DIR.joinpath("AOIs", "empty.geojson")) as aoi_collection:
            self.assertEqual(len(aoi_collection.features), 0)

    def test_aoi_from_polygon(self):
        pol = Polygon(((11, 48), (12, 48), (12, 49), (11, 49), (11, 48)))

        with AOI(data=pol) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.geometry, Polygon))
            self.assertTrue(isinstance(aoi_collection.record, dict))

    def test_aoi_from_wkt(self):
        pol = "POLYGON((11 48, 12 48, 12 49, 11 49, 11 48))"

        with AOI(data=pol) as aoi_collection:
            self.assertTrue(isinstance(aoi_collection.geometry, Polygon))
            self.assertTrue(isinstance(aoi_collection.record, dict))

    def test_aoi_from_wkt_errors(self):
        pol = "POLYGON((11, 48), (12, 48), (12, 49), (11, 49), (11, 48))"

        with self.assertRaises(errors.GEOSException):
            with AOI(data=pol) as aoi_collection:
                pass

        pol = "polygon((11, 48), (12, 48), (12, 49), (11, 49), (11, 48))"

        with self.assertRaises(TypeError):
            with AOI(data=pol) as aoi_collection:
                pass
