import shutil
import subprocess
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.aoi_check import AOI
from anomaly_detection import Anomaly
from plot_data import PlotData
from stac import StacItems
from system.helper_functions import get_anomaly_columns, get_monthly_keyword


class Config:
    def __init__(
        self,
        orbits=None,
        pols=None,
        aois=None,
        aoi_dir=Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata/AOIs"),
        start="2020-01-01",
        end="2020-12-31",
        monthly=False,
    ):
        self.orbits = orbits
        self.pols = pols
        self.aoi_dir = aoi_dir
        self.aois = aois
        self.start = start
        self.end = end
        self.working_dir = None
        self.monthly = monthly

    def get_loop(self):
        for index, key in enumerate(self.aois.keys()):
            for orbit in self.orbits:
                for pol in self.pols:
                    yield index, key, orbit, pol

    def check_working_dir(self):
        if not self.working_dir.exists():
            self.working_dir.mkdir(parents=True)


class Facility:
    def __init__(
        self,
        aoi_data=None,
        out_dir=None,
        start_date=None,
        end_date=None,
        pol="VH",
        orbit="asc",
        name="Unkown Brand",
        columns="mean",
        monthly=False,
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
        self.monthly = monthly

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
            monthly=self.monthly,
        )
        self.indicator.dataframe = pd.read_csv(
            self.out_dir.joinpath("raw", f"indicator_1_rawdata_{self.orbit}_VH.csv")
        )
        self.indicator.dataframe["interval_from"] = pd.to_datetime(
            self.indicator.dataframe["interval_from"]
        )
        self.indicator.dataframe = self.indicator.dataframe.set_index("interval_from")

        if self.monthly:
            self.indicator.monthly_aggregate()
            self.indicator.save_raw()

        self.indicator.apply_regression()
        self.indicator.save_spline()

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
            monthly=self.monthly,
        )

        anomaly.find_extrema()

        if spline:
            anomaly.save_spline()

        else:
            anomaly.save_raw()

        return anomaly

    def get_scenes(self, anomaly_data=None):
        stac = StacItems(
            data=anomaly_data.dataframe,
            geometry=self.indicator.geometry,
            orbit=self.orbit,
            pol=self.pol,
            out_dir=self.out_dir,
        )

        stac.scenes_to_df()
        stac.join_with_anomalies()
        stac.save()

    def plot_data(self, dpi=96, spline=False, anomaly_data=None):
        if spline:
            with PlotData(
                out_dir=self.out_dir,
                name=self.name,
                raw_data=self.indicator.dataframe,
                raw_columns=get_anomaly_columns(
                    self.indicator.columns_map, dst_cols=["mean"]
                ),
                spline_data=self.indicator.spline_dataframe,
                anomaly_data=anomaly_data.dataframe,
                orbit=self.orbit,
                monthly=self.monthly,
            ) as plotting:
                plotting.plot_rawdata(background=True)
                plotting.plot_splinedata()
                plotting.plot_anomalies()
                plotting.plot_finalize()
                plotting.save_spline(dpi=dpi)

        else:
            with PlotData(
                out_dir=self.out_dir,
                name=self.name,
                raw_data=self.indicator.dataframe,
                raw_columns=get_anomaly_columns(
                    self.indicator.columns_map, dst_cols=["mean"]
                ),
                anomaly_data=anomaly_data.dataframe,
                orbit=self.orbit,
                monthly=self.monthly,
            ) as plotting:
                plotting.plot_rawdata(background=False)
                plotting.plot_anomalies()
                plotting.plot_finalize()
                plotting.save_raw(dpi=dpi)


class Development:
    def __init__(self, config=None):
        self.config = config
        self.facility = None
        # self.config.working_dir = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata/collection")

        self._init_plot()

    @staticmethod
    def get_long_orbit(orbit="asc"):
        return "ascending" if orbit == "asc" else "descending"

    def _init_plot(self):
        self.fig, self.axs = plt.subplots(
            len(self.config.aois.keys()), len(self.config.orbits), figsize=(20, 10)
        )

    def _get_axis(self, index=None, orbit=None):
        if len(self.config.orbits) == 1:
            return self.axs[index]

        else:
            if orbit == "asc":
                if len(self.config.aois.keys()) > 1:
                    return self.axs[index][0]

                else:
                    return self.axs[0]

            else:
                if len(self.config.aois.keys()) > 1:
                    return self.axs[index][1]

                else:
                    return self.axs[1]

    def plot_raw_data(self, ax=None):
        sns.lineplot(
            data=self.facility.indicator.dataframe,
            x=self.facility.indicator.dataframe.index,
            y=self.facility.indicator.dataframe["mean"],
            legend=False,
            color="#d3d3d3",
            zorder=1,
            ax=ax,
        )

    def plot_splinedata(self, ax=None):
        sns.lineplot(
            data=self.facility.indicator.spline_dataframe,
            x=self.facility.indicator.spline_dataframe.index,
            y=self.facility.indicator.spline_dataframe["mean"],
            label="mean",
            legend=False,
            zorder=2,
            ax=ax,
        )

    def plot_mean_range(self, factor=0.25, ax=None):
        """
        Plot a range of mean + std that defines an insensitive area where anomalies are less likely.
        """

        sns.lineplot(
            data=self.facility.indicator.spline_dataframe,
            x=self.facility.indicator.spline_dataframe.index,
            y=self.facility.indicator.spline_dataframe["mean"].mean(),
            linestyle="--",
            color="#d3d3d3",
            legend=False,
            ax=ax,
        )

        upper_boundary = (
            self.facility.indicator.spline_dataframe["mean"].mean()
            + factor * self.facility.indicator.spline_dataframe["std"].mean()
        )
        lower_boundary = (
            self.facility.indicator.spline_dataframe["mean"].mean()
            - factor * self.facility.indicator.spline_dataframe["std"].mean()
        )

        sns.lineplot(
            data=self.facility.indicator.spline_dataframe,
            x=self.facility.indicator.spline_dataframe.index,
            y=upper_boundary,
            linestyle="--",
            color="#d3d3d3",
            legend=False,
            ax=ax,
        )

        sns.lineplot(
            data=self.facility.indicator.spline_dataframe,
            x=self.facility.indicator.spline_dataframe.index,
            y=lower_boundary,
            linestyle="--",
            color="#d3d3d3",
            legend=False,
            ax=ax,
        )

        ax.fill_between(
            self.facility.indicator.spline_dataframe.index,
            lower_boundary,
            upper_boundary,
            color="#ebebeb",
        )

    @staticmethod
    def plot_anomalies(ax=None, anomaly_data=None):
        sns.scatterplot(
            data=anomaly_data.dataframe.loc[anomaly_data.dataframe["anomaly"]],
            x=anomaly_data.dataframe.loc[anomaly_data.dataframe["anomaly"]].index,
            y=anomaly_data.dataframe.loc[anomaly_data.dataframe["anomaly"]]["mean"],
            marker="o",
            s=25,
            zorder=3,
            color="red",
            label="anomaly",
            legend=False,
            ax=ax,
        )

    def subplot_settings(self, ax=None, name=None, pol="VH", orbit="ascending"):
        ax.set_title(f"{name} {pol} polarization, {orbit} orbit")
        ax.set_ylim(
            self.facility.indicator.dataframe["mean"].min() - 1,
            self.facility.indicator.dataframe["mean"].max() + 1,
        )

        if not self.config.monthly:
            ax.set_xlim(
                datetime.date(self.facility.indicator.dataframe.index[0])
                - timedelta(days=7),
                datetime.date(
                    pd.to_datetime(self.facility.indicator.dataframe["interval_to"][-1])
                )
                + timedelta(days=7),
            )

        ax.set_ylabel("Sentinel-1 backscatter [dB]")

    def plot_finalize(self, show=False):
        plt.xlabel("Timestamp")

        handles, labels = plt.gca().get_legend_handles_labels()
        unique = [
            (h, l)
            for i, (h, l) in enumerate(zip(handles, labels))
            if l not in labels[:i]
        ]
        self.fig.legend(
            *zip(*unique), loc="outside lower center", ncols=2, bbox_to_anchor=(0.5, 0)
        )

        plt.tight_layout(pad=2.5)

        if show:  # for development
            plt.show()

    def save(self, dpi=96):
        if len(list(self.config.aois.keys())) == 1:
            out_dir = self.config.working_dir.joinpath("plot")

        else:
            out_dir = self.config.working_dir.parent.joinpath("_plots")

        out_file = out_dir.joinpath(
            f"{'_'.join(list(self.config.aois.keys()))}_{get_monthly_keyword(monthly=self.config.monthly)}.png"
        )
        self.fig.savefig(out_file, dpi=dpi)

    def from_raw_data(self):
        for index, aoi_name, orbit, pol in self.config.get_loop():
            ax = self._get_axis(index=index, orbit=orbit)

            self.config.working_dir = Path(
                r"/mnt/data1/gitlab/sat4ec/tests/testdata"
            ).joinpath(aoi_name)
            self.config.check_working_dir()
            shutil.copy(self.config.aois[aoi_name], self.config.working_dir)

            self.facility = Facility(
                orbit=orbit,
                pol=pol,
                aoi_data=self.config.working_dir.joinpath(
                    self.config.aois[aoi_name].name
                ),
                start_date=self.config.start,
                end_date=self.config.end,
                out_dir=self.config.working_dir,
                name=get_name(aoi_name),
                monthly=self.config.monthly,
            )
            self.facility.get_aoi()
            self.facility.get_indicator()
            spline_anomalies = self.facility.compute_anomaly(spline=True)
            self.facility.get_scenes(anomaly_data=spline_anomalies)
            self.plot_mean_range(ax=ax)
            self.plot_raw_data(ax=ax)
            self.plot_splinedata(ax=ax)
            self.plot_anomalies(ax=ax, anomaly_data=spline_anomalies)
            self.subplot_settings(
                ax=ax,
                name=get_name(aoi_name),
                pol=pol,
                orbit=self.get_long_orbit(orbit),
            )

        self.plot_finalize(show=True)
        self.save()


class Production:
    def __init__(self, config=None):
        self.config = config

    def entire_workflow(self):
        for index, aoi_name, orbit, pol in self.config.get_loop():
            self.config.working_dir = Path(
                r"/mnt/data1/gitlab/sat4ec/tests/testdata"
            ).joinpath(aoi_name)
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
                    get_name(aoi_name),
                    "--aggregate",
                    "monthly" if self.config.monthly else "daily",
                ],
                capture_output=False,
            )

    def from_raw_data(self):
        for index, aoi_name, orbit, pol in self.config.get_loop():
            self.config.working_dir = Path(
                r"/mnt/data1/gitlab/sat4ec/tests/testdata"
            ).joinpath(aoi_name)
            self.config.check_working_dir()
            shutil.copy(self.config.aois[aoi_name], self.config.working_dir)
            facility = Facility(
                orbit=orbit,
                pol=pol,
                aoi_data=self.config.working_dir.joinpath(
                    self.config.aois[aoi_name].name
                ),
                start_date=self.config.start,
                end_date=self.config.end,
                out_dir=self.config.working_dir,
                name=get_name(aoi_name),
                monthly=self.config.monthly,
            )
            facility.get_aoi()
            facility.get_indicator()
            raw_anomalies = facility.compute_anomaly(spline=False)
            spline_anomalies = facility.compute_anomaly(spline=True)
            facility.get_scenes(anomaly_data=spline_anomalies)
            facility.plot_data(spline=False, anomaly_data=raw_anomalies)
            facility.plot_data(spline=True, anomaly_data=spline_anomalies)


def get_name(name=None):
    brand = name.split("_")[0]
    location = name.split("_")[1]

    if len(name.split("_")) > 2:
        raise ValueError(
            f"The name of the AOI {name} does not follow scheme BRAND_LOCATION."
        )

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
        # "munich_airport": aoi_dir.joinpath("munich_airport.geojson"),
        # "munich_ikea": aoi_dir.joinpath("munich_ikea.geojson"),
        "volvo_gent": aoi_dir.joinpath("volvo_gent.geojson"),
        # "bmw_leipzig": aoi_dir.joinpath("bmw_leipzig.geojson"),
        # "vw_emden": aoi_dir.joinpath("vw_emden.geojson"),
        # "bmw_regensburg": aoi_dir.joinpath("bmw_regensburg.geojson"),
        # "opel_ruesselsheim": aoi_dir.joinpath("opel_ruesselsheim.geojson"),
        # "vw_wolfsburg": aoi_dir.joinpath("vw_wolfsburg.geojson"),
        # "porsche_leipzig": aoi_dir.joinpath("porsche_leipzig.geojson"),
    }

    conf = Config(
        orbits=orbits,
        pols=pols,
        aois=aois,
        start="2016-01-01",
        end="2022-12-31",
        monthly=True,
    )
    prod = Production(config=conf)
    prod.entire_workflow()
    # prod.from_raw_data()
    # dev = Development(config=conf)
    # dev.from_raw_data()
