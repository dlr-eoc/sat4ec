import unittest
import shutil

import pandas as pd
from source.anomaly_detection import Anomaly, Anomalies
from source.aoi_check import Feature
from test_helper_functions import prepare_test_dataframes
from pathlib import Path

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestAD(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestAD, self).__init__(*args, **kwargs)
        self.out_dir = TEST_DIR.joinpath("output", "vw_wolfsburg")
        (
            self.raw_data,
            self.raw_monthly_data,
            self.reg_data,
            self.reg_anomaly_data,
            self.raw_monthly_anomaly_data,
            self.linear_data,
            self.linear_monthly_data,
        ) = prepare_test_dataframes(data_dir=TEST_DIR.joinpath("input"))

    def create_output_dir(self):
        if not self.out_dir.joinpath("anomalies").exists():
            self.out_dir.joinpath("anomalies").mkdir(parents=True)

    def tearDown(self):
        if self.out_dir.exists():
            shutil.rmtree(self.out_dir)

    def test_dataframe_from_file(self):
        anomaly_collection = Anomalies(
            data=TEST_DIR.joinpath("input", "raw", "indicator_1_rawdata_daily_asc_VH.csv"),
            features=[Feature(fid="0")],
        )

        self.assertTrue(isinstance(anomaly_collection.indicator_df, pd.DataFrame))
        self.assertTrue(
            anomaly_collection.indicator_df.index.inferred_type, pd.DatetimeIndex
        )

    def test_dataframe_from_dataframe(self):
        anomaly_collection = Anomalies(
            data=self.raw_data,
            features=[Feature(fid="0")],
        )

        self.assertTrue(isinstance(anomaly_collection.indicator_df, pd.DataFrame))
        self.assertTrue(
            anomaly_collection.indicator_df.index.inferred_type, pd.DatetimeIndex
        )

    def test_dataframe_from_filestring(self):
        anomaly_collection = Anomalies(
            data=str(
                TEST_DIR.joinpath(
                    "input", "raw", "indicator_1_rawdata_daily_asc_VH.csv"
                ).absolute()
            ),
            features=[Feature(fid="0")],
        )

        self.assertTrue(isinstance(anomaly_collection.indicator_df, pd.DataFrame))
        self.assertTrue(
            anomaly_collection.indicator_df.index.inferred_type, pd.DatetimeIndex
        )

    def test_prepare_dataframe(self):
        anomaly_collection = Anomalies(
            data=self.raw_data,
            features=[Feature(fid="0")],
        )

        self.assertTrue("0_anomaly" in anomaly_collection.dataframe.columns)

        anomaly_collection.dataframe = anomaly_collection.dataframe.drop(
            ["0_anomaly"], axis=1
        )
        anomaly_collection.dataframe = anomaly_collection.dataframe[
            sorted(anomaly_collection.dataframe.columns)
        ]
        anomaly_collection.indicator_df = anomaly_collection.indicator_df[
            sorted(anomaly_collection.indicator_df.columns)
        ]

        self.assertIsNone(
            pd.testing.assert_frame_equal(
                anomaly_collection.dataframe, anomaly_collection.indicator_df
            )
        )

    def test_find_maxima_regression(self):
        anomaly_collection = Anomalies(
            data=self.reg_data,
            linear_data=self.linear_data,
            features=[Feature(fid="0")],
            anomaly_column="mean",
        )
        feature = anomaly_collection.features[0]

        anomaly = Anomaly(
            data=anomaly_collection.dataframe.loc[
                :,
                anomaly_collection.dataframe.columns.str.startswith(f"{feature.fid}_"),
            ],
            linear_data=anomaly_collection.linear_regression_df.loc[
                :,
                anomaly_collection.linear_regression_df.columns.str.startswith(
                    f"{feature.fid}_"
                ),
            ],
            fid=feature.fid,
            anomaly_column=anomaly_collection.column,
        )

        anomaly.find_maxima()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["0_anomaly"]]), 25)

    def test_find_minima_regression(self):
        anomaly_collection = Anomalies(
            data=self.reg_data,
            linear_data=self.linear_data,
            features=[Feature(fid="0")],
            anomaly_column="mean",
        )
        feature = anomaly_collection.features[0]

        anomaly = Anomaly(
            data=anomaly_collection.dataframe.loc[
                :,
                anomaly_collection.dataframe.columns.str.startswith(f"{feature.fid}_"),
            ],
            linear_data=anomaly_collection.linear_regression_df.loc[
                :,
                anomaly_collection.linear_regression_df.columns.str.startswith(
                    f"{feature.fid}_"
                ),
            ],
            fid=feature.fid,
            anomaly_column=anomaly_collection.column,
        )

        anomaly.find_minima()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["0_anomaly"]]), 24)

    def test_find_extrema_regression(self):
        anomaly_collection = Anomalies(
            data=self.reg_data,
            linear_data=self.linear_data,
            features=[Feature(fid="0")],
            anomaly_column="mean",
        )
        feature = anomaly_collection.features[0]

        anomaly = Anomaly(
            data=anomaly_collection.dataframe.loc[
                :,
                anomaly_collection.dataframe.columns.str.startswith(f"{feature.fid}_"),
            ],
            linear_data=anomaly_collection.linear_regression_df.loc[
                :,
                anomaly_collection.linear_regression_df.columns.str.startswith(
                    f"{feature.fid}_"
                ),
            ],
            fid=feature.fid,
            anomaly_column=anomaly_collection.column,
        )

        anomaly.find_feature_extrema()
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["0_anomaly"]]), 43)

    def test_find_uncorrected_extrema(self):
        anomaly_collection = Anomalies(
            data=self.reg_data,
            linear_data=self.linear_data,
            features=[Feature(fid="0")],
            anomaly_column="mean",
        )
        feature = anomaly_collection.features[0]

        anomaly = Anomaly(
            data=anomaly_collection.dataframe.loc[
                :,
                anomaly_collection.dataframe.columns.str.startswith(f"{feature.fid}_"),
            ],
            linear_data=anomaly_collection.linear_regression_df.loc[
                :,
                anomaly_collection.linear_regression_df.columns.str.startswith(
                    f"{feature.fid}_"
                ),
            ],
            fid=feature.fid,
            anomaly_column=anomaly_collection.column,
        )

        anomaly.find_maxima()  # find maxima on dataframe
        anomaly.find_minima()  # find minima on dataframe
        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["0_anomaly"]]), 49)

    def test_find_extrema_monthly(self):
        anomaly_collection = Anomalies(
            data=self.raw_monthly_data,
            linear_data=self.linear_monthly_data,
            features=[Feature(fid="0")],
            anomaly_column="mean",
        )
        feature = anomaly_collection.features[0]

        anomaly = Anomaly(
            data=anomaly_collection.dataframe.loc[
                :,
                anomaly_collection.dataframe.columns.str.startswith(f"{feature.fid}_"),
            ],
            linear_data=anomaly_collection.linear_regression_df.loc[
                :,
                anomaly_collection.linear_regression_df.columns.str.startswith(
                    f"{feature.fid}_"
                ),
            ],
            fid=feature.fid,
            anomaly_column=anomaly_collection.column,
        )

        anomaly.find_feature_extrema()

        self.assertEqual(len(anomaly.dataframe[anomaly.dataframe["0_anomaly"]]), 6)

    def test_anomaly_save_monthly(self):
        anomaly_collection = Anomalies(
            data=self.raw_monthly_data,
            linear_data=self.linear_monthly_data,
            features=[Feature(fid="0")],
            anomaly_column="mean",
            out_dir=self.out_dir,
            monthly=True
        )
        feature = anomaly_collection.features[0]
        self.create_output_dir()

        anomaly = Anomaly(
            data=anomaly_collection.dataframe.loc[
                :,
                anomaly_collection.dataframe.columns.str.startswith(f"{feature.fid}_"),
            ],
            linear_data=anomaly_collection.linear_regression_df.loc[
                :,
                anomaly_collection.linear_regression_df.columns.str.startswith(
                    f"{feature.fid}_"
                ),
            ],
            fid=feature.fid,
            anomaly_column=anomaly_collection.column,
        )

        anomaly.find_feature_extrema()
        anomaly_collection.save_raw()

        self.assertTrue(
            anomaly_collection.out_dir.joinpath(
                "anomalies",
                f"indicator_1_anomalies_raw_monthly_{anomaly_collection.orbit}_{anomaly_collection.pol}.csv",
            ).exists()
        )

    def test_anomaly_save_regression(self):
        anomaly_collection = Anomalies(
            data=self.reg_data,
            linear_data=self.linear_data,
            features=[Feature(fid="0")],
            anomaly_column="mean",
            out_dir=self.out_dir,
        )
        feature = anomaly_collection.features[0]
        self.create_output_dir()

        anomaly = Anomaly(
            data=anomaly_collection.dataframe.loc[
                :,
                anomaly_collection.dataframe.columns.str.startswith(f"{feature.fid}_"),
            ],
            linear_data=anomaly_collection.linear_regression_df.loc[
                :,
                anomaly_collection.linear_regression_df.columns.str.startswith(
                    f"{feature.fid}_"
                ),
            ],
            fid=feature.fid,
            anomaly_column=anomaly_collection.column,
        )

        anomaly.find_feature_extrema()
        anomaly_collection.save_regression()

        self.assertTrue(
            anomaly_collection.out_dir.joinpath(
                "anomalies",
                f"indicator_1_anomalies_regression_{anomaly_collection.orbit}_{anomaly_collection.pol}.csv",
            ).exists()
        )
