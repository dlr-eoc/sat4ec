import unittest
from pathlib import Path

import pandas as pd

from source.data_retrieval import IndicatorData as IData
from source.aoi_check import AOI

from sentinelhub import (
    Geometry,
    DataCollection,
    SentinelHubStatistical,
)


TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestGetData(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGetData, self).__init__(*args, **kwargs)
        self.data_dir = TEST_DIR.joinpath("vw_wolfsburg2subfeatures")
        self.aoi_collection = AOI(data=TEST_DIR.joinpath("AOIs", "vw_wolfsburg2subfeatures.geojson"))
        self.feature = [feature for feature in self.aoi_collection.get_feature()][0]
        self.start_date = "2020-01-01"
        self.end_date = "2022-12-31"
        self.orbit = "asc"
        self.pol = "VH"
        self.monthly = False

    def test_class_init(self):
        indicator = IData(
            aoi=self.feature.geometry,
            fid=self.feature.fid,
            out_dir=self.data_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
            monthly=self.monthly,
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

    def test_monthly_aggregate(self):
        indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
            monthly=True
        )

        indicator.get_request_grd()
        indicator.get_data()
        indicator.stats_to_df()
        daily_dataframe = indicator.dataframe.copy()
        indicator.monthly_aggregate()

        self.assertTrue(indicator.dataframe.index.inferred_type, pd.DatetimeIndex)
        self.assertTrue(len(indicator.dataframe) < len(daily_dataframe))

    def test_regression(self):
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

        indicator.apply_regression(mode="spline")
        indicator.save_regression(mode="spline")
        self.assertTrue(
            indicator.out_dir.joinpath(
                "regression", f"indicator_1_spline_{self.orbit}_{self.pol}.csv"
            ).exists()
        )

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
        indicator.save_regression()
        self.assertTrue(
            indicator.out_dir.joinpath(
                "raw", f"indicator_1_rawdata_{self.orbit}_{self.pol}.csv"
            ).exists()
        )
