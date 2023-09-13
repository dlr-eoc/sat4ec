import shutil
import subprocess
import pandas as pd
from pathlib import Path

from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.aoi_check import AOI
from anomaly_detection import Anomaly
from plot_data import PlotData
from system.helper_functions import get_anomaly_columns


class Config:
    def __init__(self,
                 orbits=None,
                 pols=None,
                 aois=None,
                 aoi_dir=Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata/AOIs"),
                 start="2020-01-01",
                 end="2020-12-31",
                 ):
        self.orbits = orbits
        self.pols = pols
        self.aoi_dir = aoi_dir
        self.aois = aois
        self.start = start
        self.end = end
        self.working_dir = None

    def get_loop(self):
        for key in self.aois.keys():
            for orbit in self.orbits:
                for pol in self.pols:
                    yield key, orbit, pol

    def check_working_dir(self):
        if not self.working_dir.exists():
            self.working_dir.mkdir(parents=True)


class Facility:
    def __init__(self, aoi_data=None,
                 out_dir=None,
                 start_date=None,
                 end_date=None,
                 pol="VH",
                 orbit="asc",
                 name="Unkown Brand",
                 columns="mean",
                 ):
        self.orbit = orbit
        self.pol = pol
        self.aoi_data = aoi_data
        self.aoi = None
        self.start_date = start_date
        self.end_date = end_date
        self.out_dir = out_dir
        self.columns = columns
        self.name = name
        self.indicator = None
        self.raw_anomalies = None
        self.spline_anomalies = None

    def get_aoi(self):
        self.aoi = AOI(data=self.aoi_data)
        self.aoi.get_features()

    def get_indicator(self):
        self.indicator = IData(
            aoi=self.aoi.geometry,
            out_dir=self.out_dir,
            start_date=self.start_date,
            end_date=self.end_date,
            orbit=self.orbit,
            pol=self.pol,
        )
        self.indicator.dataframe = pd.read_csv(
            self.out_dir.joinpath("raw", f"indicator_1_rawdata_{self.orbit}_VH.csv")
        )
        self.indicator.dataframe["interval_from"] = pd.to_datetime(
            self.indicator.dataframe["interval_from"]
        )
        self.indicator.dataframe = self.indicator.dataframe.set_index("interval_from")

        self.indicator.apply_regression()
        self.indicator.save(spline=True)

    def compute_anomaly(
        self,
        anomaly_column="mean",
        spline=False,
    ):
        if spline:
            data = self.indicator.spline_dataframe

        else:
            data = self.indicator.dataframe

        anomaly = Anomaly(
            data=data,
            df_columns=self.indicator.columns_map,
            anomaly_column=anomaly_column,
            out_dir=self.out_dir,
            orbit=self.orbit,
            pol=self.pol,
        )

        anomaly.find_extrema()
        anomaly.save(spline=spline)

        return anomaly

    def plot_data(self, dpi=96, spline=False, anomaly_data=None):
        if spline:
            with PlotData(
                    out_dir=self.out_dir,
                    name=self.name,
                    raw_data=self.indicator.dataframe,
                    raw_columns=get_anomaly_columns(self.indicator.columns_map, dst_cols=["mean"]),
                    spline_data=self.indicator.spline_dataframe,
                    anomaly_data=anomaly_data.dataframe,
                    orbit=self.orbit,
            ) as plotting:
                plotting.plot_rawdata(background=True)
                plotting.plot_splinedata()
                plotting.plot_anomalies()
                plotting.plot_finalize()
                plotting.save(spline=spline, dpi=dpi)

        else:
            with PlotData(
                    out_dir=self.out_dir,
                    name=self.name,
                    raw_data=self.indicator.dataframe,
                    raw_columns=get_anomaly_columns(self.indicator.columns_map, dst_cols=["mean"]),
                    anomaly_data=anomaly_data.dataframe,
                    orbit=self.orbit,
            ) as plotting:
                plotting.plot_rawdata(background=False)
                plotting.plot_anomalies()
                plotting.plot_finalize()
                plotting.save(spline=spline, dpi=dpi)


class Production:
    def __init__(self, config=None):
        self.config = config

    def entire_workflow(self):
        for aoi_name, orbit, pol in self.config.get_loop():
            self.config.working_dir = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata").joinpath(aoi_name)
            self.config.check_working_dir()
            shutil.copy(self.config.aois[aoi_name], self.config.working_dir)

            response = subprocess.run(
                [
                    "python3",
                    "../sat4ec/main.py",
                    "--aoi_data",
                    self.config.working_dir.joinpath(self.config.aois[aoi_name].name),
                    "--out_dir",
                    self.config.working_dir,
                    "--start_date",
                    f"{self.config.start}",
                    "--end_date",
                    f"{self.config.end}",
                    "--orbit",
                    orbit,
                    "--polarization",
                    pol,
                    "--name",
                    get_name(aoi_name)
                ],
                capture_output=False,
            )

    def from_raw_data(self):
        for aoi_name, orbit, pol in self.config.get_loop():
            self.config.working_dir = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata").joinpath(aoi_name)
            self.config.check_working_dir()
            shutil.copy(self.config.aois[aoi_name], self.config.working_dir)
            facility = Facility(
                orbit=orbit,
                pol=pol,
                aoi_data=self.config.working_dir.joinpath(self.config.aois[aoi_name].name),
                start_date=self.config.start,
                end_date=self.config.end,
                out_dir=self.config.working_dir,
                name=get_name(aoi_name)
            )
            facility.get_aoi()
            facility.get_indicator()
            raw_anomalies = facility.compute_anomaly(spline=False)
            spline_anomalies = facility.compute_anomaly(spline=True)
            facility.plot_data(spline=False, anomaly_data=raw_anomalies)
            facility.plot_data(spline=True, anomaly_data=spline_anomalies)


def get_name(name=None):
    brand = name.split("_")[0]
    location = name.split("_")[1]

    if len(name.split("_")) > 2:
        raise ValueError(f"The name of the AOI {name} does not follow scheme BRAND_LOCATION.")

    else:
        return f"{brand.upper()} {location.title()}"


if __name__ == "__main__":
    aoi_dir = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata/AOIs")
    orbits = ["asc", "des"]

    pols = [
        # "VV",
        "VH"
    ]

    aois = {
        # "volvo_gent": aoi_dir.joinpath("volvo_gent.geojson"),
        # "munich_airport": aoi_dir.joinpath("munich_airport.geojson"),
        # "munich_ikea": aoi_dir.joinpath("munich_ikea.geojson"),
        # "bmw_leipzig": aoi_dir.joinpath("bmw_leipzig.geojson"),
        # "vw_emden": aoi_dir.joinpath("vw_emden.geojson"),
        # "bmw_regensburg": aoi_dir.joinpath("bmw_regensburg.geojson"),
        # "opel_ruesselsheim": aoi_dir.joinpath("opel_ruesselsheim.geojson"),
        "vw_wolfsburg": aoi_dir.joinpath("vw_wolfsburg.geojson"),
        # "porsche_leipzig": aoi_dir.joinpath("porsche_leipzig.geojson"),
    }

    conf = Config(orbits=orbits, pols=pols, aois=aois, start="2020-01-01", end="2022-12-31")
    prod = Production(config=conf)
    # prod.entire_workflow()
    prod.from_raw_data()
