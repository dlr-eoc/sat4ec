import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.dates as mdates
from source.system.helper_functions import get_monthly_keyword
from datetime import datetime, timedelta
from pathlib import Path


class PlotData:
    def __init__(
        self,
        name=None,
        raw_data=None,
        reg_data=None,
        linear_data=None,
        anomaly_data=None,
        out_dir=None,
        orbit="asc",
        pol="VH",
        monthly=False,
    ):
        self.name = name
        self.out_dir = out_dir
        self.orbit = orbit
        self.pol = pol
        self.monthly = monthly

        self.raw_dataframe = self._get_data(data=raw_data)
        self.reg_dataframe = self._get_data(data=reg_data)
        self.linear_dataframe = self._get_data(data=linear_data)
        self.anomaly_dataframe = self._get_data(data=anomaly_data)
        self._get_subplots()
        self._get_long_orbit()

    def _get_data(self, data):
        if isinstance(data, Path):
            return self._load_df(data)

        elif isinstance(data, str):
            if Path(data).exists():
                return self._load_df(Path(data))

        elif isinstance(data, pd.DataFrame):
            return data

        else:
            return None

    @staticmethod
    def _load_df(filename):
        df = pd.read_csv(filename)
        df["interval_from"] = pd.to_datetime(df["interval_from"])
        df = df.set_index("interval_from")

        return df

    def _get_subplots(self):
        self.fig, self.axs = plt.subplots(1, 1, figsize=(20, 10))

    def _get_long_orbit(self):
        self.long_orbit = "ascending" if self.orbit == "asc" else "descending"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        plt.close()

    def plot_rawdata_range(self):
        plusminus = u"\u00B1"
        upper_boundary = self.raw_dataframe["mean"] + self.raw_dataframe["std"]
        lower_boundary = self.raw_dataframe["mean"] - self.raw_dataframe["std"]

        # plot of baundaries
        for boundary in [upper_boundary, lower_boundary]:
            sns.lineplot(
                data=self.raw_dataframe,
                x=self.raw_dataframe.index,
                y=boundary,
                color="#d3d3d3",
                alpha=0,
                legend=False,
            )

        # fill space between boundaries
        self.axs.fill_between(
            self.raw_dataframe.index,
            lower_boundary,
            upper_boundary,
            color="#ebebeb",
            label=f"mean {plusminus} std"
        )

    def plot_rawdata(self):
        # plot of main line
        sns.lineplot(
            data=self.raw_dataframe,
            x=self.raw_dataframe.index,
            y=self.raw_dataframe["mean"],
            legend=False,
            color="#bbbbbb",
            label="raw mean",
            zorder=1,
            ax=self.axs,
        )

    def plot_regression(self):
        sns.lineplot(
            data=self.reg_dataframe,
            x=self.reg_dataframe.index,
            y=self.reg_dataframe["mean"],
            label="mean",
            legend=False,
            zorder=2,
            ax=self.axs,
        )

    def plot_mean_range(self, factor=0.2):
        """
        Plot a range of mean + std that defines an insensitive area where anomalies are less likely.
        """

        upper_boundary = (
            self.linear_dataframe["mean"]
            + factor * self.linear_dataframe["std"]
        )
        lower_boundary = (
            self.linear_dataframe["mean"]
            - factor * self.linear_dataframe["std"]
        )

        self.axs.fill_between(
            self.linear_dataframe.index,
            lower_boundary,
            upper_boundary,
            color="#dba8e5",
            alpha=0.25
        )

        sns.lineplot(
            data=self.linear_dataframe,
            x=self.linear_dataframe.index,
            y=self.linear_dataframe["mean"],
            linestyle="--",
            color="#ab84b3",
            legend=False,
        )

    def plot_anomalies(self):
        sns.scatterplot(
            data=self.anomaly_dataframe.loc[self.anomaly_dataframe["anomaly"]],
            x=self.anomaly_dataframe.loc[self.anomaly_dataframe["anomaly"]].index,
            y=self.anomaly_dataframe.loc[self.anomaly_dataframe["anomaly"]]["mean"],
            marker="o",
            s=25,
            zorder=3,
            color="red",
            label="anomaly",
            legend=False,
            ax=self.axs,
        )

    def plot_finalize(self, show=False):
        plt.title(f"{self.name} {self.pol} polarization, {self.long_orbit} orbit")
        plt.ylabel("Sentinel-1 backscatter [dB]")
        plt.xlabel("Timestamp")

        plt.ylim(
            (self.raw_dataframe["mean"] - self.raw_dataframe["std"]).min() - 1,
            (self.raw_dataframe["mean"] + self.raw_dataframe["std"]).max() + 1,
        )

        if not self.monthly:
            plt.xlim(
                datetime.date(self.raw_dataframe.index[0]) - timedelta(days=7),
                datetime.date(pd.to_datetime(self.raw_dataframe["interval_to"][-1]))
                + timedelta(days=7),
            )

        self.axs.xaxis.set_minor_locator(mdates.MonthLocator())  # minor ticks display months
        self.axs.xaxis.set_minor_formatter(mdates.DateFormatter(""))  # minor ticks are not labelled

        self.fig.legend(loc="outside lower center", ncols=2, bbox_to_anchor=(0.5, 0))
        plt.tight_layout(pad=2.5)

        if show:  # for development
            plt.show()

    def correct_name(self):
        self.name = self.name.lower()

        if " " in self.name:
            self.name = "_".join(self.name.split(" "))

    def save_regression(self, dpi=96):
        self.correct_name()

        out_file = self.out_dir.joinpath(
            "plot",
            f"indicator_1_{self.name}_interpolated_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.png",
        )

        self.fig.savefig(out_file, dpi=dpi)

    def save_raw(self, dpi=96):
        self.correct_name()

        out_file = self.out_dir.joinpath(
            "plot",
            f"indicator_1_{self.name}_rawdata_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.png",
        )

        self.fig.savefig(out_file, dpi=dpi)
