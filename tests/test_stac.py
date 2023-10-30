import unittest
from pathlib import Path
import pandas as pd
import shutil

from source.stac import StacItems, StacCollection
from source.aoi_check import AOI
from test_helper_functions import prepare_test_dataframes

from sentinelhub import SentinelHubCatalog, Geometry, CRS
from datetime import datetime


TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestGetData(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGetData, self).__init__(*args, **kwargs)
        self.out_dir = TEST_DIR.joinpath("output", "vw_wolfsburg")
        self.data_dir = TEST_DIR.joinpath("orbit_input")
        self.orbit = "asc"
        self.aoi_split = True
        self.pol = "VH"
        self.crs = CRS.WGS84
        self.aoi_collection = AOI(
            data=TEST_DIR.joinpath("input", "AOIs", "vw_wolfsburg2subfeatures.geojson"),
            aoi_split=self.aoi_split
        )
        (
            self.raw_data,
            self.raw_monthly_data,
            self.reg_data,
            self.reg_anomaly_data,
            self.raw_monthly_anomaly_data,
            self.linear_data,
            self.linear_monthly_data,
        ) = prepare_test_dataframes(self.data_dir, aoi_split=True)
        self._get_features()
        self._get_geometries()
        self.create_output_dir()

        self.stac_collection = StacCollection(
            data=self.reg_anomaly_data,
            features=self.features,
            geometries=self.geometries,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.out_dir,
        )

    def _get_features(self):
        self.features = [feature for feature in self.aoi_collection.get_feature()]

    def _get_geometries(self):
        self.geometries = [Geometry(feature.geometry, crs=self.crs) for feature in self.features]

    def create_output_dir(self):
        if not self.out_dir.joinpath("scenes").exists():
            self.out_dir.joinpath("scenes").mkdir(parents=True)

    # def tearDown(self):
    #     if self.out_dir.exists():
    #         shutil.rmtree(self.out_dir)

    def test_dataframe_from_file(self):
        stac_collection = StacCollection(
            data=self.data_dir.joinpath("anomalies", f"indicator_1_anomalies_regression_daily_aoi_split_{self.orbit}_VH.csv"),
        )

        self.assertTrue(isinstance(stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_dataframe(self):
        stac_collection = StacCollection(
            data=self.reg_anomaly_data,
        )

        self.assertTrue(isinstance(stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_filestring(self):
        stac_collection = StacCollection(
            data=str(self.data_dir.joinpath("anomalies", f"indicator_1_anomalies_regression_daily_aoi_split_{self.orbit}_VH.csv").absolute()),
        )

        self.assertTrue(isinstance(stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_collection_class_init(self):
        self.assertTrue(isinstance(self.stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(self.stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_stac_items_class_init(self):
        feature = self.features[0]
        geometry = self.geometries[0]
        stac = StacItems(
            anomalies_df=self.reg_anomaly_data.loc[
                         :, self.reg_anomaly_data.columns.str.startswith(f"{feature.fid}_")
                         ],
            fid=feature.fid,
            geometry=geometry,
        )

        self.assertTrue(isinstance(stac.catalog, SentinelHubCatalog))

    def test_search_catalog(self):
        feature = self.features[0]
        geometry = self.geometries[0]
        stac = StacItems(
            anomalies_df=self.reg_anomaly_data.loc[
                         :, self.reg_anomaly_data.columns.str.startswith(f"{feature.fid}_")
                         ],
            fid=feature.fid,
            geometry=geometry,
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
        feature = self.features[0]
        geometry = self.geometries[0]
        stac = StacItems(
            anomalies_df=self.reg_anomaly_data.loc[
                         :, self.reg_anomaly_data.columns.str.startswith(f"{feature.fid}_")
                         ],
            fid=feature.fid,
            geometry=geometry,
        )
        stac.scenes_to_df()

        self.assertEqual(list(stac.dataframe.columns), ["0_scene"])
        self.assertEqual(len(stac.dataframe.iloc[0]["0_scene"]), 67)
        self.assertEqual(stac.dataframe.iloc[0]["0_scene"][:2], "S1")

    def test_scenes_to_df_multiple_features(self):
        for feature, geometry in zip(self.features, self.geometries):
            stac = StacItems(
                anomalies_df=self.reg_anomaly_data.loc[
                             :, self.reg_anomaly_data.columns.str.startswith(f"{feature.fid}_")
                             ],
                fid=feature.fid,
                geometry=geometry,
            )
            stac.scenes_to_df()
            self.stac_collection.add_stac_item(df=stac.dataframe)
        self.stac_collection.save()

    def test_join_with_anomalies(self):
        for index, (feature, geometry) in enumerate(zip(self.features, self.geometries)):
            stac = StacItems(
                anomalies_df=self.reg_anomaly_data.loc[
                             :, self.reg_anomaly_data.columns.str.startswith(f"{feature.fid}_")
                             ],
                fid=feature.fid,
                geometry=geometry,
            )
            stac.scenes_to_df()
            stac.join_with_anomalies()

            if index == 0:
                self.stac_collection.init_dataframe(df=stac.dataframe)

            else:
                self.stac_collection.add_stac_item(df=stac.dataframe)

        self.stac_collection.save()
        # self.assertEqual(list(stac.dataframe.columns), ["scene", "anomaly"])
        # self.assertEqual(len(stac.dataframe.iloc[0]["scene"]), 67)
        # self.assertEqual(stac.dataframe.iloc[0]["scene"][:2], "S1")
        # self.assertEqual(stac.dataframe["anomaly"].dtypes.name, "bool")

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
