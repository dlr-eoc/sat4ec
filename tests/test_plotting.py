import unittest

from sat4ec.aoi_check import AOI
from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.plot_data import PlotData
from sat4ec.system import helper_functions
from pathlib import Path

TEST_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")


class TestPlotting(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPlotting, self).__init__(*args, **kwargs)

        aoi = AOI(TEST_DIR.joinpath("AOIs", "bmw_regensburg.geojson"))
        aoi.get_features()
        self.aoi = aoi.geometry
        self.out_dir = TEST_DIR.joinpath("bmw_regensburg")
        self.name = "BMW Regensburg"
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
        self.anomaly_spline_file = self.indicator.out_dir.joinpath(
            "product", f"indicator_1_anomalies_spline_{self.orbit}_{self.pol}.csv"
        )

    def test_raw_plot(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            raw_columns=helper_functions.get_anomaly_columns(
                self.indicator.columns_map
            ),
            orbit="asc",
        ) as plotting:
            plotting.plot_rawdata(show=True)

    def test_spline_plot(self):
        with PlotData(
            spline_data=self.indicator_spline_file,
            raw_columns=helper_functions.get_anomaly_columns(
                self.indicator.columns_map
            ),
            orbit="asc",
        ) as plotting:
            plotting.plot_splinedata(show=False)
            plotting.plot_finalize()

    def test_raw_spline_overlay(self):
        with PlotData(
            raw_data=self.indicator_raw_file,
            raw_columns=helper_functions.get_anomaly_columns(
                self.indicator.columns_map
            ),
            spline_data=self.indicator_spline_file,
            orbit="asc",
        ) as plotting:
            plotting.plot_rawdata(show=False, background=True)
            plotting.plot_splinedata(show=False)
            plotting.plot_finalize(show=True)

    def test_save_plot(self):
        with PlotData(
            out_dir=self.out_dir,
            name=self.name,
            raw_data=self.indicator_raw_file,
            raw_columns=helper_functions.get_anomaly_columns(
                self.indicator.columns_map
            ),
            spline_data=self.indicator_spline_file,
            anomaly_data=self.anomaly_spline_file,
            orbit="asc",
        ) as plotting:
            plotting.plot_rawdata(show=False, background=True)
            plotting.plot_splinedata(show=False)
            plotting.plot_anomalies()
            plotting.plot_finalize(show=True)
            plotting.save()
