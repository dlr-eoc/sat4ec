import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.dates as mdates
from system.helper_functions import get_monthly_keyword
from datetime import datetime, timedelta
from pathlib import Path


class PlotCollection:
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
        features=None,
        max_cols=2,
    ):
        self.name = name
        self.out_dir = out_dir
        self.orbit = orbit
        self.pol = pol
        self.monthly = monthly
        self.features = features
        self.max_cols = max_cols
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
        if len(self.features) <= self.max_cols-1:
            nrows = 1
            ncols = len(self.features) + 1

        else:  # len(self.features) > max_cols-1
            if len(self.features) % self.max_cols == 0:  # e.g. 8 % 4 = 0
                nrows = len(self.features) / self.max_cols + 1
                ncols = self.max_cols

            else:
                nrows = len(self.features) // self.max_cols + 1
                ncols = self.max_cols

        self.fig, self.axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, 10))

    def _get_long_orbit(self):
        self.long_orbit = "ascending" if self.orbit == "asc" else "descending"

    def _get_plot_axis(self, index=0):
        row = index // self.max_cols
        col = index % self.max_cols

        if self.axs.shape == (4,):
            ax = self.axs[col]

        else:
            ax = self.axs[row][col]

        return ax

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        plt.close()

    def plot_rawdata_range(self, fid="total"):
        plusminus = u"\u00B1"
        upper_boundary = self.raw_dataframe[f"{fid}_mean"] + self.raw_dataframe[f"{fid}_std"]
        lower_boundary = self.raw_dataframe[f"{fid}_mean"] - self.raw_dataframe[f"{fid}_std"]

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

    def plot_features(self):
        for index, feature in enumerate(self.features):
            feature_plot = PlotData(
                raw_data=self.raw_dataframe.loc[
                    :, self.raw_dataframe.columns.str.startswith(f"{feature.fid}_")
                ],
                reg_data=self.reg_dataframe.loc[
                    :, self.reg_dataframe.columns.str.startswith(f"{feature.fid}_")
                ],
                anomaly_data=self.anomaly_dataframe.loc[
                    :, self.anomaly_dataframe.columns.str.startswith(f"{feature.fid}_")
                ],
                linear_data=self.linear_dataframe.loc[
                    :, self.linear_dataframe.columns.str.startswith(f"{feature.fid}_")
                ],
                ax=self._get_plot_axis(index=index),
                fid=feature.fid,
                orbit=self.orbit,
                pol=self.pol,
                long_orbit=self.long_orbit,
                monthly=self.monthly,
            )

            feature_plot.plot_rawdata_range()

            if self.linear_dataframe is not None:
                feature_plot.plot_mean_range()

            feature_plot.plot_rawdata()

            if self.reg_dataframe is not None:
                feature_plot.plot_regression()

            feature_plot.plot_anomalies()
            feature_plot.plot_finalize()

        plt.show()


class PlotData:
    def __init__(
        self,
        raw_data=None,
        reg_data=None,
        linear_data=None,
        anomaly_data=None,
        ax=None,
        fid=None,
        orbit=None,
        pol=None,
        long_orbit=None,
        monthly=False,
    ):
        self.raw_dataframe = raw_data
        self.reg_dataframe = reg_data
        self.linear_dataframe = linear_data
        self.anomaly_dataframe = anomaly_data
        self.ax = ax
        self.fid = fid
        self.orbit = orbit
        self.pol = pol
        self.long_orbit = long_orbit
        self.monthly = monthly

    def plot_rawdata(self):
        # plot of main line
        sns.lineplot(
            data=self.raw_dataframe,
            x=self.raw_dataframe.index,
            y=self.raw_dataframe[f"{self.fid}_mean"],
            legend=False,
            color="#bbbbbb",
            label="raw mean",
            zorder=1,
            ax=self.ax,
        )

    def plot_rawdata_range(self):
        plusminus = u"\u00B1"
        upper_boundary = self.raw_dataframe[f"{self.fid}_mean"] + self.raw_dataframe[f"{self.fid}_std"]
        lower_boundary = self.raw_dataframe[f"{self.fid}_mean"] - self.raw_dataframe[f"{self.fid}_std"]

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
        self.ax.fill_between(
            self.raw_dataframe.index,
            lower_boundary,
            upper_boundary,
            color="#ebebeb",
            label=f"mean {plusminus} std"
        )

    def plot_regression(self):
        sns.lineplot(
            data=self.reg_dataframe,
            x=self.reg_dataframe.index,
            y=self.reg_dataframe[f"{self.fid}_mean"],
            label=f"{self.fid}_mean",
            legend=False,
            zorder=2,
            ax=self.ax,
        )

    def plot_mean_range(self, factor=0.2):
        """
        Plot a range of mean + std that defines an insensitive area where anomalies are less likely.
        """

        upper_boundary = self.linear_dataframe[f"{self.fid}_mean"] + factor * self.linear_dataframe[f"{self.fid}_std"]
        lower_boundary = self.linear_dataframe[f"{self.fid}_mean"] - factor * self.linear_dataframe[f"{self.fid}_std"]

        self.ax.fill_between(
            x=self.linear_dataframe.index,
            y1=lower_boundary.tolist(),  # pandas series to list
            y2=upper_boundary.tolist(),  # pandas series to list
            color="#dba8e5",
            alpha=0.25
        )

        sns.lineplot(
            data=self.linear_dataframe,
            x=self.linear_dataframe.index,
            y=self.linear_dataframe[f"{self.fid}_mean"],
            linestyle="--",
            color="#ab84b3",
            legend=False,
        )

    def plot_anomalies(self):
        sns.scatterplot(
            data=self.anomaly_dataframe.loc[self.anomaly_dataframe[f"{self.fid}_anomaly"]],
            x=self.anomaly_dataframe.loc[self.anomaly_dataframe[f"{self.fid}_anomaly"]].index,
            y=self.anomaly_dataframe.loc[self.anomaly_dataframe[f"{self.fid}_anomaly"]][f"{self.fid}_mean"],
            marker="o",
            s=25,
            zorder=3,
            color="red",
            label="anomaly",
            legend=False,
            ax=self.ax,
        )

    def plot_finalize(self, show=False):
        plt.title(f"{self.pol} polarization, {self.long_orbit} orbit")
        plt.ylabel("Sentinel-1 backscatter [dB]")
        plt.xlabel("Timestamp")

        plt.ylim(
            (self.raw_dataframe[f"{self.fid}_mean"] - self.raw_dataframe[f"{self.fid}_std"]).min() - 1,
            (self.raw_dataframe[f"{self.fid}_mean"] + self.raw_dataframe[f"{self.fid}_std"]).max() + 1,
        )

        # if not self.monthly:
        #     plt.xlim(
        #         datetime.date(self.raw_dataframe.index[0]) - timedelta(days=7),
        #         datetime.date(pd.to_datetime(self.raw_dataframe["interval_to"][-1]))
        #         + timedelta(days=7),
        #     )

        self.ax.xaxis.set_minor_locator(mdates.MonthLocator())  # minor ticks display months
        self.ax.xaxis.set_minor_formatter(mdates.DateFormatter(""))  # minor ticks are not labelled

        # self.fig.legend(loc="outside lower center", ncols=2, bbox_to_anchor=(0.5, 0))
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
