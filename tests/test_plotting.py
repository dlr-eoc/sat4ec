import unittest

from source.aoi_check import AOI
from source.data_retrieval import IndicatorData as IData
from source.plot_data import PlotData
from pathlib import Path

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestPlotting(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPlotting, self).__init__(*args, **kwargs)

        aoi = AOI(TEST_DIR.joinpath("AOIs", "vw_wolfsburg.geojson"))
        aoi.get_features()
        self.aoi = aoi.geometry
        self.out_dir = TEST_DIR.joinpath("vw_wolfsburg")
        self.name = "VW Wolfsburg"
        self.start_date = "2016-01-01"
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

        self.indicator_raw_file = self.indicator.out_dir.joinpath(
            "raw", f"indicator_1_rawdata_{self.orbit}_{self.pol}.csv"
        )
        self.indicator_reg_file = self.indicator.out_dir.joinpath(
            "regression", f"indicator_1_spline_{self.orbit}_{self.pol}.csv"
        )
        self.indicator_linear_file = self.indicator.out_dir.joinpath(
            "regression", f"indicator_1_linear_{self.orbit}_{self.pol}.csv"
        )
        self.anomaly_spline_file = self.indicator.out_dir.joinpath(
            "anomalies", f"indicator_1_anomalies_spline_{self.orbit}_{self.pol}.csv"
        )
        self.anomaly_raw_file = self.indicator.out_dir.joinpath(
            "anomalies", f"indicator_1_anomalies_raw_{self.orbit}_{self.pol}.csv"
        )

    def test_raw_plot(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_rawdata()
            plotting.plot_finalize(show=True)

    def test_raw_range_plot(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_rawdata_range()
            plotting.plot_finalize(show=True)

    def test_regression_plot(self):
        with PlotData(
            # raw_data=self.indicator_raw_file,
            reg_data=self.indicator_reg_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_regression()
            plotting.plot_finalize(show=True)

    def test_raw_regression_overlay(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            reg_data=self.indicator_reg_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_rawdata_range()
            plotting.plot_rawdata()
            plotting.plot_regression()
            plotting.plot_finalize(show=True)

    def test_raw_regression_linear_overlay(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            reg_data=self.indicator_reg_file,
            linear_data=self.indicator_linear_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_rawdata_range()
            plotting.plot_mean_range()
            plotting.plot_rawdata()
            plotting.plot_regression()
            plotting.plot_finalize(show=True)

    def test_plot_anomalies_regression(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            reg_data=self.indicator_reg_file,
            anomaly_data=self.anomaly_spline_file,
            orbit=self.orbit,
            name=self.name
        ) as plotting:
            plotting.plot_rawdata()
            plotting.plot_regression()
            plotting.plot_anomalies()
            plotting.plot_finalize(show=True)

    def test_plot_anomalies_reg_std(self):
        with PlotData(
            raw_data=self.indicator_reg_file,
            reg_data=self.indicator_reg_file,
            anomaly_data=self.anomaly_spline_file,
            orbit=self.orbit,
            name=self.name
        ) as plotting:
            plotting.plot_regression()
            plotting.plot_anomalies()
            plotting.plot_mean_range()
            plotting.plot_finalize(show=True)

    def test_plot_anomalies_raw(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            anomaly_data=self.anomaly_raw_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_rawdata()
            plotting.plot_anomalies()
            plotting.plot_finalize(show=True)

    def test_save_plot_spline(self):
        with PlotData(
            out_dir=self.out_dir,
            name=self.name,
            raw_data=self.indicator_raw_file,
            reg_data=self.indicator_reg_file,
            anomaly_data=self.anomaly_spline_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_rawdata()
            plotting.plot_regression()
            plotting.plot_anomalies()
            plotting.plot_finalize(show=True)
            plotting.save_regression()

    def test_save_plot_raw(self):
        with PlotData(
            out_dir=self.out_dir,
            name=self.name,
            raw_data=self.indicator_raw_file,
            anomaly_data=self.anomaly_raw_file,
            orbit=self.orbit,
        ) as plotting:
            plotting.plot_rawdata()
            plotting.plot_anomalies()
            plotting.plot_finalize(show=True)
            plotting.save_raw()
