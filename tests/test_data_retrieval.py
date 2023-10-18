import unittest
from pathlib import Path

import pandas as pd

from source.data_retrieval import IndicatorData as IData
from data_retrieval import SubsetCollection as Subsets
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
        self.aoi_collection = AOI(
            data=TEST_DIR.joinpath("AOIs", "vw_wolfsburg2subfeatures.geojson")
        )
        self.features = [feature for feature in self.aoi_collection.get_feature()]
        self.feature = self.features[0]

        self.indicator = IData(
            aoi=self.feature.geometry,
            fid=self.feature.fid,
            out_dir=self.data_dir,
            start_date="2020-01-01",
            end_date="2022-12-31",
            orbit="asc",
            pol="VH",
        )

        self.subsets = Subsets(
            out_dir=self.indicator.out_dir,
            monthly=False,
            orbit=self.indicator.orbit,
            pol=self.indicator.pol,
        )

    def test_class_init(self):
        self.assertTrue(isinstance(self.indicator.geometry, Geometry))
        self.assertTrue(isinstance(self.indicator.size, tuple))
        self.assertEqual(len(self.indicator.size), 2)
        self.assertTrue(isinstance(self.indicator.collection, DataCollection))
        self.assertTrue(self.indicator.out_dir.exists())

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
            self.data_dir.joinpath("raw", "indicator_1_rawdata_asc_VH.csv")
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
            self.data_dir.joinpath("raw", "indicator_1_rawdata_asc_VH.csv")
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
        self.subsets.save_monthly_raw()

        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "raw",
                f"indicator_1_rawdata_monthly_{self.indicator.orbit}_{self.indicator.pol}.csv",
            ).exists()
        )
