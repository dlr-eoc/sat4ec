import unittest

import pandas as pd
from source.aoi_check import AOI
from source.data_retrieval import IndicatorData as IData
from source.anomaly_detection import Anomaly
from pathlib import Path

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestAD(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestAD, self).__init__(*args, **kwargs)

        aoi = AOI(TEST_DIR.joinpath("AOIs", "vw_wolfsburg.geojson"))
        aoi.get_features()
        self.aoi = aoi.geometry
        self.out_dir = TEST_DIR.joinpath("vw_wolfsburg")
        self.start_date = "2022-01-01"
        self.end_date = "2022-12-31"
        self.orbit = "asc"
        self.pol = "VH"
        self.anomaly_options = {
            "invert": False,
            "normalize": False,
            "plot": False,
        }

        self.indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        self.indicator_raw_file = self.indicator.out_dir.joinpath(
            "raw", f"indicator_1_rawdata_monthly_{self.orbit}_{self.pol}.csv"
        )
        self.indicator_regression_file = self.indicator.out_dir.joinpath(
            "regression", f"indicator_1_spline_monthly_{self.orbit}_{self.pol}.csv"
        )

    def test_dataframe_from_file(self):
        anomaly = Anomaly(
            data=self.indicator_raw_file,
        )

        self.assertTrue(isinstance(anomaly.indicator_df, pd.DataFrame))
        self.assertTrue(anomaly.indicator_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_dataframe(self):
        anomaly = Anomaly(
            data=pd.read_csv(self.indicator_raw_file),
        )

        self.assertTrue(isinstance(anomaly.indicator_df, pd.DataFrame))
        self.assertTrue(anomaly.indicator_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_filestring(self):
        anomaly = Anomaly(
            data=str(self.indicator_raw_file),
        )

        self.assertTrue(isinstance(anomaly.indicator_df, pd.DataFrame))
        self.assertTrue(anomaly.indicator_df.index.inferred_type, pd.DatetimeIndex)

    def test_prepare_dataframe(self):
        anomaly = Anomaly(
            data=self.indicator_raw_file,
        )

        self.assertTrue(anomaly.dataframe.columns[-1], "anomaly")

        anomaly.dataframe = anomaly.dataframe.drop(["anomaly"], axis=1)
        self.assertIsNone(
            pd.testing.assert_frame_equal(anomaly.dataframe, anomaly.indicator_df)
        )

    def test_find_maxima_regression(self):
        anomaly = Anomaly(
            data=self.indicator_regression_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_maxima()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 7)

    def test_find_minima_regression(self):
        anomaly = Anomaly(
            data=self.indicator_regression_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_minima()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 5)

    def test_find_extrema_spline(self):
        anomaly = Anomaly(
            data=self.indicator_regression_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 7)

    def test_find_uncorrected_extrema(self):
        anomaly = Anomaly(
            data=self.indicator_regression_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_maxima()  # find maxima on dataframe
        anomaly.find_minima()  # find minima on dataframe
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 12)

    def test_delete_adjacent_anomalies(self):
        aoi = AOI(TEST_DIR.joinpath("AOIs", "vw_wolfsburg.geojson"))
        aoi.get_features()
        self.aoi = aoi.geometry
        self.out_dir = TEST_DIR.joinpath("vw_wolfsburg")

        self.indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        self.indicator_raw_file = self.indicator.out_dir.joinpath(
            "raw", f"indicator_1_rawdata_monthly_{self.orbit}_{self.pol}.csv"
        )
        self.indicator_regression_file = self.indicator.out_dir.joinpath(
            "regression", f"indicator_1_spline_monthly_{self.orbit}_{self.pol}.csv"
        )
        self.indicator_linear_regression_file = self.indicator.out_dir.joinpath(
            "regression", f"indicator_1_linear_monthly_{self.orbit}_{self.pol}.csv"
        )

        anomaly = Anomaly(
            data=self.indicator_regression_file,
            linear_data=self.indicator_linear_regression_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 12)

    def test_find_extrema_raw(self):
        anomaly = Anomaly(
            data=self.indicator_raw_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 8)

    def test_anomaly_save_raw(self):
        anomaly = Anomaly(
            data=self.indicator_raw_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        anomaly.save_raw()

        self.assertTrue(
            anomaly.out_dir.joinpath(
                "anomalies", f"indicator_1_anomalies_raw_{self.orbit}_{self.pol}.csv"
            ).exists()
        )

    def test_anomaly_save_regression(self):
        anomaly = Anomaly(
            data=self.indicator_regression_file,
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        anomaly.save_regression()

        self.assertTrue(
            anomaly.out_dir.joinpath(
                "anomalies", f"indicator_1_anomalies_spline_{self.orbit}_{self.pol}.csv"
            ).exists()
        )
