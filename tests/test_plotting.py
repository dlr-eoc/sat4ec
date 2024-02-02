"""Test plotting."""
from __future__ import annotations

import shutil
import unittest
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from anomaly_detection import Anomalies
from system.helper_functions import mutliple_orbits_raw_range
from system.subset_collections import OrbitCollection as Orbits
from system.subset_collections import SubsetCollection as Subsets
from test_helper_functions import prepare_test_dataframes

from sat4ec.aoi_check import Feature
from sat4ec.plot_data import PlotData, Plots

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestPlotting(unittest.TestCase):
    """Encapsulates testing methods."""

    def __init__(self: TestPlotting, *args: int, **kwargs: int) -> None:
        """Initialize TestPlotting class."""
        super().__init__(*args, **kwargs)
        self.tear_down = True  # delete output data per default, switch to False in test methods if required
        self.out_dir = TEST_DIR.joinpath("output", "vw_wolfsburg")
        self.monthly = False
        self.orbit_collection = Orbits(orbit="both", monthly=self.monthly)
        self._prepare(data_dir=TEST_DIR.joinpath("orbit_input"))
        self.collection = Plots(
            out_dir=self.out_dir,
            name="VW Wolfsburg",
            orbit=self.orbit_collection.orbit,
            monthly=self.monthly,
            linear=True,
            features=[Feature(fid="0")],
            raw_range=mutliple_orbits_raw_range(fid="0", orbit_collection=self.orbit_collection),
        )

    def _prepare(self: TestPlotting, data_dir: Path | None = None, aoi_split: bool = False) -> None:
        for orbit in self.orbit_collection.orbits:
            (
                self.raw_data,
                self.raw_monthly_data,
                self.reg_data,
                self.reg_anomaly_data,
                self.raw_monthly_anomaly_data,
                self.linear_data,
                self.linear_monthly_data,
            ) = prepare_test_dataframes(
                data_dir=data_dir,
                orbit=orbit,
                aoi_split=aoi_split,
            )

            subsets = Subsets(orbit=orbit)
            anomalies = Anomalies()

            if self.monthly:
                subsets.dataframe = self.raw_monthly_data
                subsets.regression_dataframe = self.reg_data
                subsets.linear_dataframe = self.linear_monthly_data
                anomalies.dataframe = self.raw_monthly_anomaly_data

            else:
                subsets.dataframe = self.raw_data
                subsets.regression_dataframe = self.reg_data
                subsets.linear_dataframe = self.linear_data
                anomalies.dataframe = self.reg_anomaly_data

            self.orbit_collection.add_subsets(subsets=subsets, orbit=orbit)
            self.orbit_collection.add_anomalies(anomalies=anomalies, orbit=orbit)

    def create_output_dir(self: TestPlotting) -> None:
        """Create output directory if not existing."""
        if not self.out_dir.joinpath("plot").exists():
            self.out_dir.joinpath("plot").mkdir(parents=True)

    def tearDown(self: TestPlotting) -> None:
        """Delete test output data."""
        if self.tear_down and self.out_dir.exists():
            shutil.rmtree(self.out_dir)

    def test_raw_plot(self: TestPlotting) -> None:
        """Test plotting raw data."""
        for subsets, _, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    fid=feature.fid,
                    orbit=orbit,
                )
                plotting.plot_rawdata()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_raw_range_plot(self: TestPlotting) -> None:
        """Test plotting raw data range."""
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid,
            )
            # only plot raw range on left axis
            if plotting.ax.get_ylabel() != "2nd_des":
                plotting.plot_rawdata_range()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_monthly_raw_range_plot(self: TestPlotting) -> None:
        """Test plotting monthly data with raw data range."""
        self.monthly = True
        self._prepare()

        self.collection = Plots(
            out_dir=self.out_dir,
            name="VW Wolfsburg",
            orbit=self.orbit_collection.orbit,
            monthly=self.monthly,
            linear=True,
            features=[Feature(fid="0")],
            raw_range=mutliple_orbits_raw_range(fid="0", orbit_collection=self.orbit_collection),
        )

        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid,
                monthly=self.monthly,
            )
            # only plot raw range on left axis
            if plotting.ax.get_ylabel() != "2nd_des":
                plotting.plot_rawdata_range()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_regression_plot(self: TestPlotting) -> None:
        """Test plotting regression data."""
        for subsets, _, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    fid=feature.fid,
                    orbit=orbit,
                )
                plotting.plot_regression()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_raw_regression_overlay(self: TestPlotting) -> None:
        """Test plotting raw data with regression."""
        for subsets, _, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                )

                # only plot raw range on left axis
                if plotting.ax.get_ylabel() != "2nd_des":
                    plotting.plot_rawdata_range()

                plotting.plot_rawdata(alpha=0.5)
                plotting.plot_regression()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_raw_regression_linear_overlay(self: TestPlotting) -> None:
        """Test plotting raw data with linear regression."""
        for subsets, _, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    linear_data=subsets.linear_dataframe.loc[
                        :,
                        subsets.linear_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                )
                # only plot raw range on left axis
                if plotting.ax.get_ylabel() != "2nd_des":
                    plotting.plot_rawdata_range()

                plotting.plot_rawdata()
                plotting.plot_mean_range()
                plotting.plot_regression()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_plot_anomalies_regression(self: TestPlotting) -> None:
        """Test plotting anomalies with regression."""
        for subsets, anomalies, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    anomaly_data=anomalies.dataframe.loc[
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                )
                plotting.plot_rawdata()
                plotting.plot_regression()
                plotting.plot_anomalies()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_plot_anomalies_reg_std(self: TestPlotting) -> None:
        """Test plotting anomalies with regression and standard deviation."""
        for subsets, anomalies, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    linear_data=subsets.linear_dataframe.loc[
                        :,
                        subsets.linear_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    anomaly_data=anomalies.dataframe.loc[
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                )
                plotting.plot_regression()
                plotting.plot_mean_range()
                plotting.plot_anomalies()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_plot_aoi_split_anomalies_reg_std(self: TestPlotting) -> None:
        """Test plotting splitwise with regression and standard deviation."""
        self._prepare(aoi_split=True)

        self.collection = Plots(
            out_dir=self.out_dir,
            name="VW Wolfsburg",
            orbit=self.orbit_collection.orbit,
            monthly=self.monthly,
            linear=True,
            features=[Feature(fid="0"), Feature(fid="1"), Feature(fid="total")],
            raw_range=mutliple_orbits_raw_range(fid="total", orbit_collection=self.orbit_collection),
        )

        for subsets, anomalies, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    linear_data=subsets.linear_dataframe.loc[
                        :,
                        subsets.linear_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    anomaly_data=anomalies.dataframe.loc[
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                )
                # only plot raw range on left axis
                if plotting.ax.get_ylabel() != "2nd_des":
                    plotting.plot_rawdata_range()

                plotting.plot_regression()
                plotting.plot_mean_range()
                plotting.plot_anomalies()

        self.collection.finalize()
        self.collection.show_plot()

        self.assertTrue(isinstance(self.collection.axs, np.ndarray))
        self.assertTrue(isinstance(self.collection.axs.flatten()[0], plt.Axes))
        self.assertEqual(len(self.collection.axs.flatten()), 4)

    def test_plot_monthly_aoi_split_anomalies_reg_std(self: TestPlotting) -> None:
        """Test plotting monthly data splitwise with anomalies."""
        self.monthly = True
        self._prepare(aoi_split=True)

        self.collection = Plots(
            out_dir=self.out_dir,
            name="VW Wolfsburg",
            orbit=self.orbit_collection.orbit,
            monthly=self.monthly,
            linear=True,
            features=[Feature(fid="0"), Feature(fid="1"), Feature(fid="total")],
            raw_range=mutliple_orbits_raw_range(fid="total", orbit_collection=self.orbit_collection),
        )

        for subsets, anomalies, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    linear_data=subsets.linear_dataframe.loc[
                        :,
                        subsets.linear_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    anomaly_data=anomalies.dataframe.loc[
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                    monthly=self.monthly,
                )
                # only plot raw range on left axis
                if plotting.ax.get_ylabel() != "2nd_des":
                    plotting.plot_rawdata_range()

                plotting.plot_rawdata()
                plotting.plot_mean_range()
                plotting.plot_anomalies()

        self.collection.finalize()
        self.collection.show_plot()

        self.assertTrue(isinstance(self.collection.axs, np.ndarray))
        self.assertTrue(isinstance(self.collection.axs.flatten()[0], plt.Axes))
        self.assertEqual(len(self.collection.axs.flatten()), 4)

    def test_plot_anomalies_monthly_raw(self: TestPlotting) -> None:
        """Test plotting monthly data with anomalies."""
        self.monthly = True
        self._prepare()
        self.collection.raw_dataframe = self.raw_monthly_data
        self.collection.anomaly_dataframe = self.raw_monthly_anomaly_data
        self.collection.monthly = True

        for subsets, anomalies, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    anomaly_data=anomalies.dataframe.loc[
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                    monthly=self.monthly,
                )
                plotting.plot_rawdata()
                plotting.plot_anomalies()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_save_plot_regression(self: TestPlotting) -> None:
        """Test saving regression plot."""
        for subsets, anomalies, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    linear_data=subsets.linear_dataframe.loc[
                        :,
                        subsets.linear_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    anomaly_data=anomalies.dataframe.loc[
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                )
                # only plot raw range on left axis
                if plotting.ax.get_ylabel() != "2nd_des":
                    plotting.plot_rawdata_range()

                plotting.plot_rawdata()
                plotting.plot_mean_range()
                plotting.plot_regression()
                plotting.plot_anomalies()

        self.create_output_dir()
        self.collection.finalize()
        self.collection.save_regression()

        if self.orbit_collection.orbit == "both":
            self.assertTrue(
                self.out_dir.joinpath("plot", "indicator_1_vw_wolfsburg_regression_asc_des_VH.png").exists()
            )

        else:
            self.assertTrue(
                self.out_dir.joinpath(
                    "plot",
                    f"indicator_1_vw_wolfsburg_regression_{self.orbit_collection.orbit}_VH.png",
                ).exists()
            )

    def test_save_plot_monthly(self: TestPlotting) -> None:
        """Test plotting monthly data."""
        self.monthly = True
        self._prepare()
        self.collection.raw_dataframe = self.raw_monthly_data
        self.collection.anomaly_dataframe = self.raw_monthly_anomaly_data
        self.collection.monthly = True

        for subsets, anomalies, orbit, single_axis in self.orbit_collection.get_data():
            for index, feature in enumerate(self.collection.features):
                plotting = PlotData(
                    raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=self.orbit_collection),
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    linear_data=subsets.linear_dataframe.loc[
                        :,
                        subsets.linear_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    anomaly_data=anomalies.dataframe.loc[
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    ax=self.collection._get_plot_axis(index=index, single_axis=single_axis),
                    orbit=orbit,
                    fid=feature.fid,
                    monthly=self.monthly,
                )
                # only plot raw range on left axis
                if plotting.ax.get_ylabel() != "2nd_des":
                    plotting.plot_rawdata_range()

                plotting.plot_rawdata()
                plotting.plot_mean_range()
                plotting.plot_anomalies()

        self.create_output_dir()
        self.collection.finalize()
        self.collection.save_raw()

        if self.orbit_collection.orbit == "both":
            self.assertTrue(
                self.out_dir.joinpath("plot", "indicator_1_vw_wolfsburg_rawdata_monthly_asc_des_VH.png").exists()
            )

        else:
            self.assertTrue(
                self.out_dir.joinpath(
                    "plot",
                    f"indicator_1_vw_wolfsburg_rawdata_monthly_{self.orbit_collection.orbit}_VH.png",
                ).exists()
            )
