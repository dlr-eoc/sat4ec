import unittest
import matplotlib.pyplot as plt
import shutil

import numpy as np

from source.plot_data import PlotCollection, PlotData
from source.aoi_check import Feature
from test_helper_functions import prepare_test_dataframes
from pathlib import Path

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestPlotting(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPlotting, self).__init__(*args, **kwargs)
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

        self.collection = PlotCollection(
            out_dir=self.out_dir,
            name="VW Wolfsburg",
            raw_data=self.raw_data,
            reg_data=self.reg_data,
            anomaly_data=self.reg_anomaly_data,
            linear_data=self.linear_data,
            orbit="asc",
            monthly=False,
            linear=True,
            features=[Feature(fid="0")],
        )

    def create_output_dir(self):
        if not self.out_dir.joinpath("plot").exists():
            self.out_dir.joinpath("plot").mkdir(parents=True)

    def tearDown(self):
        if self.out_dir.exists():
            shutil.rmtree(self.out_dir)

    def test_raw_plot(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_raw_range_plot(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata_range()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_regression_plot(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                reg_data=self.collection.reg_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_regression()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_raw_regression_overlay(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_regression()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_raw_regression_linear_overlay(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                linear_data=self.collection.linear_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_mean_range()
            plotting.plot_regression()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_plot_anomalies_regression(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata()
            plotting.plot_regression()
            plotting.plot_anomalies()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_plot_anomalies_reg_std(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                linear_data=self.collection.linear_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_regression()
            plotting.plot_mean_range()
            plotting.plot_anomalies()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_plot_aoi_split_anomalies_reg_std(self):
        (
            self.raw_data,
            self.raw_monthly_data,
            self.reg_data,
            self.reg_anomaly_data,
            self.raw_monthly_anomaly_data,
            self.linear_data,
            self.linear_monthly_data,
        ) = prepare_test_dataframes(data_dir=TEST_DIR.joinpath("input"), aoi_split=True)

        self.collection = PlotCollection(
            name="VW Wolfsburg",
            raw_data=self.raw_data,
            reg_data=self.reg_data,
            anomaly_data=self.reg_anomaly_data,
            linear_data=self.linear_data,
            orbit="asc",
            linear=True,
            features=[Feature(fid="0"), Feature(fid="1"), Feature(fid="total")],
        )

        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.raw_data.loc[:, self.raw_data.columns.str.startswith(f"{feature.fid}_")],
                reg_data=self.reg_data.loc[:, self.reg_data.columns.str.startswith(f"{feature.fid}_")],
                linear_data=self.linear_data.loc[:, self.linear_data.columns.str.startswith(f"{feature.fid}_")],
                anomaly_data=self.reg_anomaly_data.loc[:, self.reg_anomaly_data.columns.str.startswith(f"{feature.fid}_")],
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata_range()
            plotting.plot_regression()
            plotting.plot_mean_range()
            plotting.plot_anomalies()

        self.collection.finalize()
        self.collection.show_plot()

        self.assertTrue(isinstance(self.collection.axs, np.ndarray))
        self.assertTrue(isinstance(self.collection.axs.flatten()[0], plt.Axes))
        self.assertEqual(len(self.collection.axs.flatten()), 4)

    def test_plot_monthly_aoi_split_anomalies_reg_std(self):
        (
            self.raw_data,
            self.raw_monthly_data,
            self.reg_data,
            self.reg_anomaly_data,
            self.raw_monthly_anomaly_data,
            self.linear_data,
            self.linear_monthly_data,
        ) = prepare_test_dataframes(data_dir=TEST_DIR.joinpath("input"), aoi_split=True)

        self.collection = PlotCollection(
            name="VW Wolfsburg",
            raw_data=self.raw_monthly_data,
            anomaly_data=self.raw_monthly_anomaly_data,
            linear_data=self.linear_monthly_data,
            orbit="asc",
            linear=True,
            monthly=True,
            features=[Feature(fid="0"), Feature(fid="1"), Feature(fid="total")],
        )

        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.raw_monthly_data.loc[:, self.raw_monthly_data.columns.str.startswith(f"{feature.fid}_")],
                linear_data=self.linear_monthly_data.loc[:, self.linear_monthly_data.columns.str.startswith(f"{feature.fid}_")],
                anomaly_data=self.raw_monthly_anomaly_data.loc[:, self.raw_monthly_anomaly_data.columns.str.startswith(f"{feature.fid}_")],
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_mean_range()
            plotting.plot_anomalies()

        self.collection.finalize()
        self.collection.show_plot()

        self.assertTrue(isinstance(self.collection.axs, np.ndarray))
        self.assertTrue(isinstance(self.collection.axs.flatten()[0], plt.Axes))
        self.assertEqual(len(self.collection.axs.flatten()), 4)

    def test_plot_anomalies_monthly_raw(self):
        self.collection.raw_dataframe = self.raw_monthly_data
        self.collection.anomaly_dataframe = self.raw_monthly_anomaly_data
        self.collection.monthly = True

        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata()
            plotting.plot_anomalies()

        self.collection.finalize()
        self.assertTrue(isinstance(self.collection.axs, plt.Axes))
        plt.show()

    def test_save_plot_regression(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                linear_data=self.collection.linear_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_mean_range()
            plotting.plot_regression()
            plotting.plot_anomalies()

        self.create_output_dir()
        self.collection.finalize()
        self.collection.save_regression()

        self.assertTrue(self.out_dir.joinpath("plot", "indicator_1_vw_wolfsburg_regression_asc_VH.png").exists())
        # plt.show()

    def test_save_plot_monthly(self):
        self.collection.raw_dataframe = self.raw_monthly_data
        self.collection.anomaly_dataframe = self.raw_monthly_anomaly_data
        self.collection.monthly = True

        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                linear_data=self.collection.linear_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
                fid=feature.fid
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_mean_range()
            plotting.plot_anomalies()

        self.create_output_dir()
        self.collection.finalize()
        self.collection.save_raw()

        self.assertTrue(self.out_dir.joinpath("plot", "indicator_1_vw_wolfsburg_rawdata_monthly_asc_VH.png").exists())
        # plt.show()
