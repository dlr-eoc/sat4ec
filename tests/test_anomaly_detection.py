import unittest

import pandas as pd
from sat4ec.aoi_check import AOI
from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.anomaly_detection import Anomaly
from sat4ec.system import helper_functions
from pathlib import Path

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestAD(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestAD, self).__init__(*args, **kwargs)

        aoi = AOI(TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson"))
        aoi.get_features()
        self.aoi = aoi.geometry
        self.out_dir = TEST_DIR.joinpath("bmw_regensburg")
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
            "raw", f"indicator_1_rawdata_{self.orbit}_{self.pol}.csv"
        )
        self.indicator_spline_file = self.indicator.out_dir.joinpath(
            "spline", f"indicator_1_splinedata_{self.orbit}_{self.pol}.csv"
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

    def test_anomaly_columns(self):
        columns = helper_functions.get_anomaly_columns(self.indicator.columns_map)
        self.assertEqual(columns, ["min", "max", "mean", "std"])

    def test_find_maxima_spline(self):
        anomaly = Anomaly(
            data=self.indicator_spline_file,
            df_columns=helper_functions.get_anomaly_columns(self.indicator.columns_map),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_maxima()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 18)

    def test_find_minima_spline(self):
        anomaly = Anomaly(
            data=self.indicator_spline_file,
            df_columns=helper_functions.get_anomaly_columns(self.indicator.columns_map),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_minima()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 17)

    def test_find_extrema_spline(self):
        anomaly = Anomaly(
            data=self.indicator_spline_file,
            df_columns=helper_functions.get_anomaly_columns(self.indicator.columns_map),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 35)

    def test_find_extrema_raw(self):
        anomaly = Anomaly(
            data=self.indicator_raw_file,
            df_columns=helper_functions.get_anomaly_columns(self.indicator.columns_map),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["anomaly"]]), 104)

    def test_anomaly_save(self):
        anomaly = Anomaly(
            data=self.indicator_raw_file,
            df_columns=helper_functions.get_anomaly_columns(self.indicator.columns_map),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        anomaly.save()

        self.assertTrue(
            anomaly.out_dir.joinpath(
                "anomalies", f"indicator_1_anomalies_raw_{self.orbit}_{self.pol}.csv"
            ).exists()
        )

    def test_anomaly_save_spline(self):
        anomaly = Anomaly(
            data=self.indicator_raw_file,
            df_columns=helper_functions.get_anomaly_columns(self.indicator.columns_map),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        anomaly.save(spline=True)

        self.assertTrue(
            anomaly.out_dir.joinpath(
                "anomalies", f"indicator_1_anomalies_spline_{self.orbit}_{self.pol}.csv"
            ).exists()
        )
