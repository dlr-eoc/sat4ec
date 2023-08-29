import unittest

import numpy as np
import pandas as pd
from fiona.collection import Collection
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely import errors
from sat4ec.aoi_check import AOI
from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.anomaly_detection import Anomaly
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

        self.indicator_df_file = self.indicator.out_dir.joinpath(f"indicator_1_rawdata_{self.orbit}_{self.pol}.csv")

    def test_dataframe_from_file(self):
        anomaly = Anomaly(
            data=self.indicator_df_file,
            options=self.anomaly_options,
        )

        self.assertTrue(isinstance(anomaly.indicator_df, pd.DataFrame))
        self.assertTrue(anomaly.indicator_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_dataframe(self):
        anomaly = Anomaly(
            data=pd.read_csv(self.indicator_df_file),
            options=self.anomaly_options,
        )

        self.assertTrue(isinstance(anomaly.indicator_df, pd.DataFrame))
        self.assertTrue(anomaly.indicator_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_filestring(self):
        anomaly = Anomaly(
            data=str(self.indicator_df_file),
            options=self.anomaly_options,
        )

        self.assertTrue(isinstance(anomaly.indicator_df, pd.DataFrame))
        self.assertTrue(anomaly.indicator_df.index.inferred_type, pd.DatetimeIndex)

    def test_anomaly_detection(self):
        anomaly = Anomaly(
            data=self.indicator_df_file,
            df_columns=self.indicator.columns_map.values(),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
            options=self.anomaly_options,
        )

        anomaly.apply_anomaly_detection()
        self.assertEqual(list(anomaly.dataframe.columns), [anomaly.column])
        self.assertEqual(anomaly.dataframe[anomaly.column].dtypes.name, "bool")

    def test_join_with_indicator(self):
        anomaly = Anomaly(
            data=self.indicator_df_file,
            df_columns=self.indicator.columns_map.values(),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
            options=self.anomaly_options,
        )

        anomaly.apply_anomaly_detection()
        anomaly.join_with_indicator()
        self.assertEqual(list(anomaly.dataframe.columns)[:2], ["interval_to", "anomaly"])
        self.assertEqual(anomaly.dataframe["anomaly"].dtypes.name, "bool")

    def test_anomaly_save(self):
        anomaly = Anomaly(
            data=self.indicator_df_file,
            df_columns=self.indicator.columns_map.values(),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
            options=self.anomaly_options,
        )

        anomaly.apply_anomaly_detection()
        anomaly.join_with_indicator()
        anomaly.save()

        self.assertTrue(
            anomaly.out_dir.joinpath(
                f"indicator_1_anomalies_{self.orbit}_{self.pol}.csv"
            ).exists()
        )
