import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from system.helper_functions import get_monthly_keyword
from pathlib import Path
from datetime import datetime, timedelta


class PlotData:
    def __init__(
        self,
        name=None,
        raw_data=None,
        spline_data=None,
        anomaly_data=None,
        raw_columns=None,
        out_dir=None,
        orbit="asc",
        pol="VH",
        monthly=False
    ):
        self.name = name
        self.out_dir = out_dir
        self.orbit = orbit
        self.pol = pol
        self.raw_columns = raw_columns
        self.monthly = monthly

        self.raw_dataframe = self._get_data(data=raw_data)
        self.spline_dataframe = self._get_data(data=spline_data)
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

    def plot_rawdata(self, background=False):
        upper_boundary = self.raw_dataframe["mean"] + self.raw_dataframe["std"]
        lower_boundary = self.raw_dataframe["mean"] - self.raw_dataframe["std"]

        if background:
            color = "#d3d3d3"
            label = None

        else:
            color = "#000000"
            label = "mean"

        # plot of main line
        sns.lineplot(
            data=self.raw_dataframe,
            x=self.raw_dataframe.index,
            y=self.raw_dataframe["mean"],
            legend=False,
            color=color,
            label=label,
            zorder=1,
            ax=self.axs,
        )

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
        )

    def plot_splinedata(self):
        for col in self.raw_columns:
            sns.lineplot(
                data=self.spline_dataframe,
                x=self.spline_dataframe.index,
                y=self.spline_dataframe[col],
                label=col,
                legend=False,
                zorder=2,
                ax=self.axs,
            )

    def plot_mean_range(self, columns=None, factor=0.25):
        """
        Plot a range of mean + std that defines an insensitive area where anomalies are less likely.
        """

        if not columns:
            columns = self.raw_columns

        for col in columns:
            sns.lineplot(
                data=self.spline_dataframe,
                x=self.spline_dataframe.index,
                y=self.spline_dataframe[col].mean(),
                linestyle="--",
                color="#d3d3d3",
                legend=False,
            )

            upper_boundary = (
                self.spline_dataframe[col].mean()
                + factor * self.spline_dataframe["std"].mean()
            )
            lower_boundary = (
                self.spline_dataframe[col].mean()
                - factor * self.spline_dataframe["std"].mean()
            )

            # plot of baundaries
            for boundary in [upper_boundary, lower_boundary]:
                sns.lineplot(
                    data=self.raw_dataframe,
                    x=self.raw_dataframe.index,
                    y=boundary,
                    linestyle="--",
                    color="#d3d3d3",
                    legend=False,
                )

            self.axs.fill_between(
                self.spline_dataframe.index,
                lower_boundary,
                upper_boundary,
                color="#ebebeb",
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
            (self.raw_dataframe["mean"] + self.raw_dataframe["std"]).max() + 1
        )

        if not self.monthly:
            plt.xlim(
                datetime.date(self.raw_dataframe.index[0]) - timedelta(days=7),
                datetime.date(pd.to_datetime(self.raw_dataframe["interval_to"][-1])) + timedelta(days=7)
            )

        self.fig.legend(
            loc="outside lower center",
            ncols=len(self.raw_columns) + 1,
            bbox_to_anchor=(0.5, 0)
        )
        plt.tight_layout(pad=2.5)

        if show:  # for development
            plt.show()

    def correct_name(self):
        self.name = self.name.lower()

        if " " in self.name:
            self.name = "_".join(self.name.split(" "))

    def save_spline(self, dpi=96):
        self.correct_name()

        out_file = self.out_dir.joinpath(
            "plot",
            f"indicator_1_{self.name}_splinedata_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.png",
        )

        self.fig.savefig(out_file, dpi=dpi)

    def save_raw(self, dpi=96):
        self.correct_name()

        out_file = self.out_dir.joinpath(
            "plot",
            f"indicator_1_{self.name}_rawdata_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.png",
        )

        self.fig.savefig(out_file, dpi=dpi)
