import unittest
from pathlib import Path
from datetime import datetime

import pandas as pd
import shutil

from source.data_retrieval import IndicatorData as IData
from source.system.collections import SubsetCollection as Subsets
from source.aoi_check import AOI
from source.system.helper_functions import get_last_month
from source.main import run_indicator

from sentinelhub import (
    Geometry,
    DataCollection,
    SentinelHubStatistical,
)


TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestGetData(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGetData, self).__init__(*args, **kwargs)
        self.tear_down = True  # delete output data per default, switch to False in test methods if required
        self.out_dir = TEST_DIR.joinpath("output", "vw_wolfsburg")
        self.daily_out_file = TEST_DIR.joinpath(
            "orbit_input", "raw", "indicator_1_rawdata_daily_aoi_split_asc_VH.csv"
        )
        self.aoi_collection = AOI(
            data=TEST_DIR.joinpath("input", "AOIs", "vw_wolfsburg_aoi_split.geojson")
        )
        self.features = [feature for feature in self.aoi_collection.get_feature()]
        self.feature = self.features[0]

        self.indicator = IData(
            aoi=self.feature.geometry,
            fid=self.feature.fid,
            out_dir=self.out_dir,
            start_date="2020-01-01",
            end_date="2020-12-31",
            orbit="asc",
            pol="VH",
        )

        self.subsets = Subsets(
            out_dir=self.indicator.out_dir,
            monthly=False,
            orbit=self.indicator.orbit,
            pol=self.indicator.pol,
        )

    def tearDown(self):
        if self.tear_down:
            if self.out_dir.exists():
                shutil.rmtree(self.out_dir)

    def test_class_init(self):
        self.assertTrue(isinstance(self.indicator.geometry, Geometry))
        self.assertTrue(isinstance(self.indicator.size, tuple))
        self.assertEqual(len(self.indicator.size), 2)
        self.assertTrue(isinstance(self.indicator.collection, DataCollection))
        self.assertTrue(self.indicator.out_dir.exists())

    def test_no_dates_provided(self):
        indicator = IData(
            aoi=self.feature.geometry,
            fid=self.feature.fid,
            out_dir=self.out_dir,
        )

        self.assertEqual(indicator.start_date, "2014-05-01")
        self.assertEqual(indicator.end_date, get_last_month())

    def test_existing_data_new_past_dates(self):
        self.subsets.daily_out_file = self.daily_out_file
        self.subsets.check_existing_raw()

        # archive start: 2020-01-3
        # archive end: 2023-09-27

        indicator = IData(
            archive_data=self.subsets.archive_dataframe,
            aoi=self.feature.geometry,
            fid=self.feature.fid,
            out_dir=self.out_dir,
            start_date="2019-12-20",
            end_date="2020-01-31",
        )

        self.assertTrue(indicator.check_dates(start=True) == "past")
        self.assertEqual(
            datetime.strftime(indicator.end_date, "%Y-%m-%d"), "2020-01-03"
        )

        run_indicator(indicator)
        past_df = indicator.dataframe
        indicator.concat_dataframes(past_df=past_df)
        self.assertEqual(
            len(indicator.dataframe), len(self.subsets.archive_dataframe) + 4
        )

    def test_existing_data_new_future_dates(self):
        self.subsets.daily_out_file = self.daily_out_file
        self.subsets.check_existing_raw()

        # archive start: 2020-01-3
        # archive end: 2023-09-27

        indicator = IData(
            archive_data=self.subsets.archive_dataframe,
            aoi=self.feature.geometry,
            fid=self.feature.fid,
            out_dir=self.out_dir,
            start_date="2023-09-01",
            end_date="2023-10-31",
        )

        self.assertTrue(indicator.check_dates(end=True) == "future")
        self.assertEqual(
            datetime.strftime(indicator.start_date, "%Y-%m-%d"), "2023-09-27"
        )

        run_indicator(indicator)
        future_df = indicator.dataframe
        indicator.concat_dataframes(future_df=future_df)
        self.assertEqual(
            len(indicator.dataframe), len(self.subsets.archive_dataframe) + 5
        )

    def test_existing_data_non_existing_column(self):
        self.subsets.archive_dataframe = pd.read_csv(self.daily_out_file)
        self.subsets.archive_dataframe = self.subsets.archive_dataframe.set_index(
            "interval_from"
        )
        self.indicator.archive_data = self.subsets.archive_dataframe
        self.indicator.fid = "11"
        existing_keyword, column_keyword = self.indicator.check_existing_data()

        self.assertTrue(existing_keyword)
        self.assertFalse(column_keyword)

    def test_non_existing_data(self):
        existing_keyword, column_keyword = self.indicator.check_existing_data()

        self.assertFalse(existing_keyword)
        self.assertIsNone(column_keyword)

    def test_request_grd(self):
        self.indicator.get_request_grd()
        self.assertTrue(isinstance(self.indicator.request, SentinelHubStatistical))

    def test_get_data(self):
        self.indicator.get_request_grd()
        self.indicator.get_data()
        self.assertEqual(list(self.indicator.stats.keys()), ["data", "status"])
        self.assertEqual(self.indicator.stats["status"], "OK")

    def test_stats_to_df(self):
        self.indicator.get_request_grd()
        self.indicator.get_data()
        self.indicator.stats_to_df()

        self.assertTrue(
            self.indicator.dataframe.dtypes["interval_to"], pd.DatetimeTZDtype
        )
        self.assertTrue(
            self.indicator.dataframe.dtypes[f"{self.feature.fid}_min"], "float32"
        )
        self.assertTrue(
            self.indicator.dataframe.dtypes[f"{self.feature.fid}_max"], "float32"
        )
        self.assertTrue(
            self.indicator.dataframe.dtypes[f"{self.feature.fid}_mean"], "float32"
        )
        self.assertTrue(
            self.indicator.dataframe.dtypes[f"{self.feature.fid}_std"], "float32"
        )
        self.assertTrue(self.indicator.dataframe.index.inferred_type, pd.DatetimeIndex)

    def test_monthly_aggregate(self):
        self.indicator.monthly = True
        self.indicator.get_request_grd()
        self.indicator.get_data()
        self.indicator.stats_to_df()
        daily_dataframe = self.indicator.dataframe.copy()

        self.subsets.monthly = True
        self.subsets.dataframe = self.indicator.dataframe
        self.subsets.monthly_aggregate()

        self.assertTrue(self.subsets.dataframe.index.inferred_type, pd.DatetimeIndex)
        self.assertTrue(len(self.subsets.dataframe) < len(daily_dataframe))

    def test_regression_raw(self):
        self.indicator.dataframe = pd.read_csv(
            self.out_dir.joinpath("raw", "indicator_1_rawdata_asc_VH.csv")
        )
        self.indicator.dataframe["interval_from"] = pd.to_datetime(
            self.indicator.dataframe["interval_from"]
        )
        self.indicator.dataframe = self.indicator.dataframe.set_index("interval_from")
        self.subsets.dataframe = self.indicator.dataframe
        self.subsets.features = self.features

        self.subsets.apply_regression(mode="spline")
        self.subsets.save_regression(mode="spline")

        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "regression",
                f"indicator_1_spline_{self.indicator.orbit}_{self.indicator.pol}.csv",
            ).exists()
        )
        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "regression",
                f"indicator_1_linear_{self.indicator.orbit}_{self.indicator.pol}.csv",
            ).exists()
        )

    def test_regression_monthly(self):
        self.indicator.dataframe = pd.read_csv(
            self.out_dir.joinpath("raw", "indicator_1_rawdata_asc_VH.csv")
        )
        self.indicator.dataframe["interval_from"] = pd.to_datetime(
            self.indicator.dataframe["interval_from"]
        )
        self.indicator.dataframe = self.indicator.dataframe.set_index("interval_from")
        self.subsets.dataframe = self.indicator.dataframe
        self.subsets.features = self.features
        self.subsets.monthly = True

        self.subsets.monthly_aggregate()
        self.subsets.apply_regression(mode="spline")
        self.subsets.save_regression(mode="spline")

        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "regression",
                f"indicator_1_spline_{self.indicator.orbit}_{self.indicator.pol}.csv",
            ).exists()
        )
        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "regression",
                f"indicator_1_linear_{self.indicator.orbit}_{self.indicator.pol}.csv",
            ).exists()
        )

    def test_save_df_raw(self):  # pure raw data
        self.tear_down = False
        self.indicator.get_request_grd()
        self.indicator.get_data()
        self.indicator.stats_to_df()
        self.subsets.dataframe = self.indicator.dataframe
        self.subsets.save_raw()

        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "raw",
                f"indicator_1_rawdata_{self.indicator.orbit}_{self.indicator.pol}.csv",
            ).exists()
        )

    def test_save_df_monthly(self):  # monthly raw data
        self.indicator.get_request_grd()
        self.indicator.get_data()
        self.indicator.stats_to_df()
        self.subsets.dataframe = self.indicator.dataframe
        self.subsets.monthly = True
        self.subsets.monthly_aggregate()
        self.subsets.save_raw()

        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "raw",
                f"indicator_1_rawdata_monthly_{self.indicator.orbit}_{self.indicator.pol}.csv",
            ).exists()
        )
