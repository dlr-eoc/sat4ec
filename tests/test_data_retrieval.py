import unittest
from pathlib import Path

import pandas as pd

from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.aoi_check import AOI

from sentinelhub import (
    Geometry,
    DataCollection,
    SentinelHubStatistical,
)


TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestGetData(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGetData, self).__init__(*args, **kwargs)
        aoi = AOI(TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson"))
        aoi.get_features()
        self.aoi = aoi.geometry
        self.out_dir = TEST_DIR.joinpath("bmw_regensburg")
        self.start_date = "2016-01-01"
        self.end_date = "2022-12-31"
        self.orbit = "asc"
        self.pol = "VH"

    def test_class_init(self):
        indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        self.assertTrue(isinstance(indicator.geometry, Geometry))
        self.assertTrue(isinstance(indicator.size, tuple))
        self.assertEqual(len(indicator.size), 2)
        self.assertTrue(isinstance(indicator.collection, DataCollection))
        self.assertTrue(indicator.out_dir.exists())

    def test_request_grd(self):
        indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        indicator.get_request_grd()
        self.assertTrue(isinstance(indicator.request, SentinelHubStatistical))

    def test_get_data(self):
        indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        indicator.get_request_grd()
        indicator.get_data()
        self.assertEqual(list(indicator.stats.keys()), ["data", "status"])
        self.assertEqual(indicator.stats["status"], "OK")

    def test_stats_to_df(self):
        indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        indicator.get_request_grd()
        indicator.get_data()
        indicator.stats_to_df()

        self.assertEqual(
            list(indicator.dataframe.columns[1:]), list(indicator.columns_map.values())
        )  # ignore 1st col
        self.assertTrue(indicator.dataframe.dtypes["interval_to"], pd.DatetimeTZDtype)
        self.assertTrue(indicator.dataframe.dtypes["min"], "float32")
        self.assertTrue(indicator.dataframe.dtypes["max"], "float32")
        self.assertTrue(indicator.dataframe.dtypes["mean"], "float32")
        self.assertTrue(indicator.dataframe.dtypes["std"], "float32")
        self.assertTrue(indicator.dataframe.index.inferred_type, pd.DatetimeIndex)

    def test_spline(self):
        indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        indicator.dataframe = pd.read_csv(self.out_dir.joinpath("raw", "indicator_1_rawdata_asc_VH.csv"))
        indicator.dataframe["interval_from"] = pd.to_datetime(indicator.dataframe["interval_from"])
        indicator.dataframe = indicator.dataframe.set_index("interval_from")

        indicator.apply_regression()
        indicator.save_spline()

    def test_save_df(self):
        indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        indicator.get_request_grd()
        indicator.get_data()
        indicator.stats_to_df()
        indicator.save_raw()
        self.assertTrue(
            indicator.out_dir.joinpath(
                "raw", f"indicator_1_rawdata_{self.orbit}_{self.pol}.csv"
            ).exists()
        )
