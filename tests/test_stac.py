import unittest
from pathlib import Path
import pandas as pd

from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.aoi_check import AOI
from sat4ec.stac import StacItems
from sat4ec.anomaly_detection import Anomaly
from sat4ec.system import helper_functions

from sentinelhub import SentinelHubCatalog
from datetime import datetime


TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestGetData(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGetData, self).__init__(*args, **kwargs)
        aoi = AOI(TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson"))
        aoi.get_features()
        self.aoi = aoi.geometry
        self.out_dir = TEST_DIR.joinpath("bmw_regensburg")
        self.start_date = "2022-01-01"
        self.end_date = "2022-12-31"
        self.orbit = "asc"
        self.pol = "VH"

        self.indicator = IData(
            aoi=self.aoi,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )

        self.anomaly_options = {
            "invert": False,
            "normalize": False,
            "plot": False,
        }

        self.anomaly = Anomaly(
            data=self.indicator.out_dir.joinpath(
                "raw",
                f"indicator_1_rawdata_{self.orbit}_{self.pol}.csv"
            ),
            df_columns=helper_functions.get_anomaly_columns(self.indicator.columns_map),
            anomaly_column="mean",
            out_dir=self.indicator.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        self.anomaly_spline_file = self.indicator.out_dir.joinpath(
            "anomalies",
            f"indicator_1_anomalies_spline_{self.orbit}_{self.pol}.csv"
        )

    def test_dataframe_from_file(self):
        stac = StacItems(
            data=self.anomaly_spline_file,
        )

        self.assertTrue(isinstance(stac.anomalies_df, pd.DataFrame))
        self.assertTrue(stac.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_dataframe(self):
        self.anomaly.find_extrema()

        stac = StacItems(
            data=self.anomaly.dataframe,
        )

        self.assertTrue(isinstance(stac.anomalies_df, pd.DataFrame))
        self.assertTrue(stac.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_filestring(self):
        stac = StacItems(
            data=str(self.anomaly_spline_file),
        )

        self.assertTrue(isinstance(stac.anomalies_df, pd.DataFrame))
        self.assertTrue(stac.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_class_init(self):
        stac = StacItems(
            data=self.anomaly_spline_file,
            geometry=self.indicator.geometry,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.indicator.out_dir,
        )

        self.assertTrue(isinstance(stac.catalog, SentinelHubCatalog))

    def test_search_catalog(self):
        stac = StacItems(
            data=self.anomaly_spline_file,
            geometry=self.indicator.geometry,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.indicator.out_dir,
        )

        search = stac.search_catalog(stac.anomalies_df.iloc[0])
        timestamp = datetime.strptime(
            search[0]["properties"]["datetime"], "%Y-%m-%dT%H:%M:%SZ"
        )

        self.assertTrue(isinstance(search[0]["id"], str))
        self.assertEqual(len(search[0]["id"]), 67)
        self.assertEqual(search[0]["id"][:2], "S1")
        self.assertTrue(isinstance(timestamp, datetime))

    def test_scenes_to_df(self):
        stac = StacItems(
            data=self.anomaly_spline_file,
            geometry=self.indicator.geometry,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.indicator.out_dir,
        )

        stac.scenes_to_df()
        self.assertEqual(list(stac.dataframe.columns), ["interval_from", "scene"])
        self.assertEqual(len(stac.dataframe.iloc[0]["scene"]), 67)
        self.assertEqual(stac.dataframe.iloc[0]["scene"][:2], "S1")

    def test_join_with_anomalies(self):
        stac = StacItems(
            data=self.anomaly_spline_file,
            geometry=self.indicator.geometry,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.indicator.out_dir,
        )

        stac.scenes_to_df()
        stac.join_with_anomalies()
        self.assertEqual(list(stac.dataframe.columns), ["scene", "anomaly"])
        self.assertEqual(len(stac.dataframe.iloc[0]["scene"]), 67)
        self.assertEqual(stac.dataframe.iloc[0]["scene"][:2], "S1")
        self.assertEqual(stac.dataframe["anomaly"].dtypes.name, "bool")

    def test_save(self):
        stac = StacItems(
            data=self.anomaly_spline_file,
            geometry=self.indicator.geometry,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.indicator.out_dir,
        )

        stac.scenes_to_df()
        stac.join_with_anomalies()
        stac.save()

        self.assertTrue(
            self.indicator.out_dir.joinpath(
                "scenes", f"indicator_1_scenes_{self.orbit}_{self.pol}.csv"
            ).exists()
        )
