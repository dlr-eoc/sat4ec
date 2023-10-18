import unittest
import matplotlib.pyplot as plt

from source.plot_data import PlotCollection, PlotData
from source.aoi_check import Feature
from test_helper_functions import prepare_test_dataframes
from pathlib import Path

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestPlotting(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPlotting, self).__init__(*args, **kwargs)
        self.data_dir = TEST_DIR.joinpath("vw_wolfsburg2subfeatures")
        (
            self.raw_data,
            self.raw_monthly_data,
            self.reg_data,
            self.reg_anomaly_data,
            self.raw_anomaly_data,
            self.linear_data,
            self.linear_monthly_data,
        ) = prepare_test_dataframes(data_dir=self.data_dir)

        self.collection = PlotCollection(
            out_dir=TEST_DIR.joinpath("vw_wolfsburg2subfeatures"),
            name="VW Wolfsburg",
            raw_data=self.raw_data,
            reg_data=self.reg_data,
            anomaly_data=self.reg_anomaly_data,
            linear_data=self.linear_data,
            orbit="asc",
            monthly=False,
            linear=True,
            features=[Feature(fid="1"), Feature(fid="2"), Feature(fid="total")],
        )

    def test_raw_plot(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata()

        self.collection.finalize()
        plt.show()

    def test_raw_range_plot(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata_range()

        self.collection.finalize()
        plt.show()

    def test_regression_plot(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                reg_data=self.collection.reg_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_regression()

        self.collection.finalize()
        plt.show()

    def test_raw_regression_overlay(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_regression()

        self.collection.finalize()
        plt.show()

    def test_raw_regression_linear_overlay(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                linear_data=self.collection.linear_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_mean_range()
            plotting.plot_regression()

        self.collection.finalize()
        plt.show()

    def test_plot_anomalies_regression(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata()
            plotting.plot_regression()
            plotting.plot_anomalies()

        self.collection.finalize()
        plt.show()

    def test_plot_anomalies_reg_std(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                linear_data=self.collection.linear_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_regression()
            plotting.plot_mean_range()
            plotting.plot_anomalies()

        self.collection.finalize()
        plt.show()

    def test_plot_anomalies_monthly_raw(self):
        self.collection.raw_dataframe = self.raw_monthly_data
        self.collection.anomaly_data = self.raw_anomaly_data
        self.collection.monthly = True

        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata()
            plotting.plot_anomalies()

        self.collection.finalize()
        plt.show()

    def test_save_plot_spline(self):
        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                reg_data=self.collection.reg_dataframe,
                linear_data=self.collection.linear_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_mean_range()
            plotting.plot_regression()
            plotting.plot_anomalies()

        self.collection.finalize()
        self.collection.save_regression()
        # plt.show()

    def test_save_plot_monthly(self):
        self.collection.raw_dataframe = self.raw_monthly_data
        self.collection.anomaly_data = self.raw_anomaly_data
        self.collection.monthly = True

        for index, feature in enumerate(self.collection.features):
            plotting = PlotData(
                raw_data=self.collection.raw_dataframe,
                linear_data=self.collection.linear_dataframe,
                anomaly_data=self.collection.anomaly_dataframe,
                ax=self.collection._get_plot_axis(index=index),
            )
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_mean_range()
            plotting.plot_anomalies()

        self.collection.finalize()
        # self.collection.save_raw()
        plt.show()
