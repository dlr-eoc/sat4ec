"""Test Sentinel-1 scene retrieval."""
from __future__ import annotations

import shutil
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd
from sentinelhub import CRS, Geometry, SentinelHubCatalog
from test_helper_functions import prepare_test_dataframes

from sat4ec.aoi_check import AOI
from sat4ec.stac import StacCollection, StacItems

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestGetData(unittest.TestCase):
    """Encapsulates testing methods."""

    def __init__(self: TestGetData, *args: int, **kwargs: int) -> None:
        """Initialize TestGetData class."""
        super().__init__(*args, **kwargs)
        self.tear_down = True
        self.out_dir = TEST_DIR.joinpath("output", "bmw_regensburg")
        self.orbit = "asc"
        self.aoi_split = True
        self.pol = "VH"
        self.crs = CRS.WGS84
        self.aoi_collection = AOI(
            data=TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson"),
            aoi_split=self.aoi_split,
        )
        (
            self.raw_data,
            self.raw_monthly_data,
            self.reg_data,
            self.reg_anomaly_data,
            self.raw_monthly_anomaly_data,
            self.linear_data,
            self.linear_monthly_data,
        ) = prepare_test_dataframes(data_dir=TEST_DIR.joinpath("bmw_regensburg"), aoi_split=True)
        self._get_features()
        self._get_geometries()
        self.create_output_dir()

        self.stac_collection = StacCollection(
            data=self.reg_anomaly_data.copy(),
            features=self.features,
            geometries=self.geometries,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.out_dir,
        )

    def _get_features(self: TestGetData) -> None:
        self.features = list(self.aoi_collection.get_feature())

    def _get_geometries(self: TestGetData) -> None:
        self.geometries = [Geometry(feature.geometry, crs=self.crs) for feature in self.features]

    def create_output_dir(self: TestGetData) -> None:
        """Create output directory if not existing."""
        if not self.out_dir.joinpath("scenes").exists():
            self.out_dir.joinpath("scenes").mkdir(parents=True)

    def tearDown(self: TestGetData) -> None:
        """Delete output test data."""
        if self.tear_down and self.out_dir.exists():
            shutil.rmtree(self.out_dir)

    def test_dataframe_from_file(self: TestGetData) -> None:
        """Test read dataframe from Path."""
        stac_collection = StacCollection(
            data=TEST_DIR.joinpath("bmw_regensburg").joinpath(
                "anomalies",
                f"indicator_1_anomalies_regression_split_aoi_{self.orbit}_VH.csv",
            ),
        )

        self.assertTrue(isinstance(stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_dataframe(self: TestGetData) -> None:
        """Test get dataframe from dataframe."""
        stac_collection = StacCollection(
            data=self.reg_anomaly_data,
        )

        self.assertTrue(isinstance(stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_dataframe_from_filestring(self: TestGetData) -> None:
        """Test read dataframe from file string."""
        stac_collection = StacCollection(
            data=str(
                TEST_DIR.joinpath("bmw_regensburg")
                .joinpath(
                    "anomalies",
                    f"indicator_1_anomalies_regression_split_aoi_{self.orbit}_VH.csv",
                )
                .absolute()
            ),
        )

        self.assertTrue(isinstance(stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_collection_class_init(self: TestGetData) -> None:
        """Test initialization of StacCollection class."""
        self.assertTrue(isinstance(self.stac_collection.anomalies_df, pd.DataFrame))
        self.assertTrue(self.stac_collection.anomalies_df.index.inferred_type, pd.DatetimeIndex)

    def test_stac_items_class_init(self: TestGetData) -> None:
        """Test initialization of StacItems class."""
        feature = self.features[0]
        geometry = self.geometries[0]
        stac = StacItems(
            anomalies_df=self.reg_anomaly_data.loc[:, self.reg_anomaly_data.columns.str.startswith(f"{feature.fid}_")],
            fid=feature.fid,
            geometry=geometry,
        )

        self.assertTrue(isinstance(stac.catalog, SentinelHubCatalog))

    def test_search_catalog(self: TestGetData) -> None:
        """Test search Sentinel Hub catalog."""
        feature = self.features[0]
        geometry = self.geometries[0]
        stac = StacItems(
            anomalies_df=self.stac_collection.anomalies_df.loc[
                self.stac_collection.anomalies_df[f"{feature.fid}_anomaly"]
            ],
            fid=feature.fid,
            geometry=geometry,
        )
        catalog = stac.search_catalog(row=0)
        timestamp = datetime.strptime(catalog["properties"]["datetime"], "%Y-%m-%dT%H:%M:%SZ")

        self.assertTrue(isinstance(catalog["id"], str))
        self.assertEqual(len(catalog["id"]), 67)
        self.assertEqual(catalog["id"][:2], "S1")
        self.assertTrue(isinstance(timestamp, datetime))

    def test_scenes_to_df(self: TestGetData) -> None:
        """Test transfer scenes to dataframe."""
        feature = self.features[0]
        geometry = self.geometries[0]
        stac = StacItems(
            anomalies_df=self.stac_collection.anomalies_df.loc[
                self.stac_collection.anomalies_df[f"{feature.fid}_anomaly"]
            ],
            fid=feature.fid,
            geometry=geometry,
        )
        stac.scenes_to_df()

        self.assertEqual(list(stac.dataframe.columns), ["interval_from", "0_scene"])
        self.assertEqual(len(stac.dataframe.iloc[1]["0_scene"]), 67)
        self.assertEqual(stac.dataframe.iloc[1]["0_scene"][:2], "S1")

    def test_scenes_to_df_multiple_features(self: TestGetData) -> None:
        """Test transfer scenes to dataframe for multiple features."""
        for _, (feature, geometry) in enumerate(zip(self.features, self.geometries, strict=False)):
            stac = StacItems(
                anomalies_df=self.stac_collection.anomalies_df.loc[
                    :,
                    self.stac_collection.anomalies_df.columns.str.startswith(f"{feature.fid}_"),
                ],
                fid=feature.fid,
                geometry=geometry,
            )
            stac.scenes_to_df()
            stac.join_with_anomalies()
            self.assertEqual(
                list(stac.dataframe.columns),
                [
                    "interval_from",
                    f"{feature.fid}_scene",
                    f"{feature.fid}_mean",
                    f"{feature.fid}_std",
                ],
            )
            self.assertEqual(len(stac.dataframe.iloc[1][f"{feature.fid}_scene"]), 67)
            self.assertEqual(stac.dataframe.iloc[1][f"{feature.fid}_scene"][:2], "S1")

    def test_get_stac_collection(self: TestGetData) -> None:
        """Test get STAC collection for the selected AOIs."""
        self.stac_collection.get_stac_collection()

        self.assertEqual(self.stac_collection.dataframe.columns[0], "interval_from")
        self.assertEqual(
            self.stac_collection.dataframe.loc[:, self.stac_collection.dataframe.columns.str.endswith("scene")].shape[
                1
            ],
            len(self.features),
        )

    def test_save(self: TestGetData) -> None:
        """Test saving scenes dataframe."""
        self.tear_down = False
        self.stac_collection.get_stac_collection()

        self.assertTrue(self.out_dir.joinpath("scenes", f"indicator_1_scenes_{self.orbit}_{self.pol}.csv").exists())
