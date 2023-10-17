import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.dates as mdates
from system.helper_functions import get_monthly_keyword
from datetime import timedelta
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
        if len(self.features[:-1]) < self.max_cols:
            nrows = 1
            ncols = len(self.features)

        elif (
            len(self.features[:-1]) == self.max_cols
        ):  # features fill first row, total fills next row
            nrows = 2
            ncols = self.max_cols

        else:  # len(self.features) > max_cols
            if len(self.features) % self.max_cols == 0:  # e.g. 8 % 4 = 0
                nrows = len(self.features) / self.max_cols
                ncols = self.max_cols

            else:
                nrows = len(self.features) // self.max_cols
                ncols = self.max_cols

        self.fig, self.axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, 10))

    def _get_long_orbit(self):
        self.long_orbit = "ascending" if self.orbit == "asc" else "descending"

    def _get_plot_axis(self, index=0):
        row = index // self.max_cols
        col = index % self.max_cols

        if self.axs.shape == (self.max_cols,):
            ax = self.axs[col]

        else:
            ax = self.axs[row][col]

        return ax

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        plt.close()

    def plot_rawdata_range(self, fid="total"):
        plusminus = "\u00B1"
        upper_boundary = (
            self.raw_dataframe[f"{fid}_mean"] + self.raw_dataframe[f"{fid}_std"]
        )
        lower_boundary = (
            self.raw_dataframe[f"{fid}_mean"] - self.raw_dataframe[f"{fid}_std"]
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
            label=f"mean {plusminus} std",
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

    def plot_annotations(self):
        plt.title(f"{self.name} {self.pol} polarization, {self.long_orbit} orbit")
        plt.ylabel("Sentinel-1 backscatter [dB]")
        plt.xlabel("Timestamp")

    def axes_limits(self):
        plt.ylim(
            (self.raw_dataframe["total_mean"] - self.raw_dataframe["total_std"]).min()
            - 1,
            (self.raw_dataframe["total_mean"] + self.raw_dataframe["total_std"]).max()
            + 1,
        )

        if not self.monthly:
            plt.xlim(
                self.raw_dataframe.index[0].to_pydatetime() - timedelta(days=7),
                pd.to_datetime(self.raw_dataframe["interval_to"][-1]).to_pydatetime()
                + timedelta(days=7),
            )

    def axes_ticks(self):
        for ax in self.axs.flatten():
            ax.xaxis.set_minor_locator(
                mdates.MonthLocator()
            )  # minor ticks display months
            ax.xaxis.set_minor_formatter(
                mdates.DateFormatter("")
            )  # minor ticks are not labelled

    def unused_subplots(self):
        # delete unused subplots
        for i in range(
            len(self.axs.flatten()) - len(self.features)
        ):  # get count of empty subplots
            self.fig.delaxes(self.axs.flatten()[len(self.axs.flatten()) - 1 - i])

    @staticmethod
    def delete_subplot_legend_items(handles=None, labels=None):
        """
        Figure legend has subplot labels like ["0_mean", "1_mean", "total_mean", "raw mean"].
        Make general labels like ["mean", "raw mean"], i.e. truncate "0", "1" and "total".
        """

        label_candidates = [item for item in labels if "_" in item]  # get labels with _ sign
        label_indices = [i for i, item in enumerate(labels) if "_" in item]  # get indices of labels with _ sign
        labels[label_indices[-1]] = "interpol."  # alter last element to draw it in the legend
        del label_candidates[-1]  # remove last element from list
        del label_indices[-1]  # remove last element from list

        # delete remaining handles and labels with _ sign
        for i in reversed(label_indices):
            handles = np.delete(handles, i)
            labels = np.delete(labels, i)

        return handles, labels

    def plot_legend(self):
        # get handles and labels from each subplot
        handles = [ax.get_legend_handles_labels()[0] for ax in self.fig.axes]
        labels = [ax.get_legend_handles_labels()[1] for ax in self.fig.axes]

        # merge into broader lists, originals were like [[handle 1, handle 2], [handle 3, handle 4]]
        handles = [item for sub in handles for item in sub]
        labels = [item for sub in labels for item in sub]

        uniques, indices = np.unique(labels, return_index=True)  # get unique labels and their indices
        handles = np.array(handles)[np.array(indices)]  # get handles at unique indices
        labels = np.array(labels)[np.array(indices)]  # get labels at unique indices
        handles, labels = self.delete_subplot_legend_items(handles=handles, labels=labels)
        uniques = [(h, l) for i, (h, l) in enumerate(zip(handles, labels))]  # arrange handles and labels as pairs

        self.fig.legend(*zip(*uniques), loc="outside lower center", ncols=2, bbox_to_anchor=(0.5, 0))

    def finalize(self, show=False):
        self.unused_subplots()
        self.plot_annotations()
        self.axes_limits()
        self.axes_ticks()
        self.plot_legend()

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
        plusminus = "\u00B1"
        upper_boundary = (
            self.raw_dataframe[f"{self.fid}_mean"]
            + self.raw_dataframe[f"{self.fid}_std"]
        )
        lower_boundary = (
            self.raw_dataframe[f"{self.fid}_mean"]
            - self.raw_dataframe[f"{self.fid}_std"]
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
        self.ax.fill_between(
            self.raw_dataframe.index,
            lower_boundary.tolist(),  # pandas series to list
            upper_boundary.tolist(),  # pandas series to list
            color="#ebebeb",
            label=f"mean {plusminus} std",
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

        upper_boundary = (
            self.linear_dataframe[f"{self.fid}_mean"]
            + factor * self.linear_dataframe[f"{self.fid}_std"]
        )
        lower_boundary = (
            self.linear_dataframe[f"{self.fid}_mean"]
            - factor * self.linear_dataframe[f"{self.fid}_std"]
        )

        self.ax.fill_between(
            x=self.linear_dataframe.index,
            y1=lower_boundary.tolist(),  # pandas series to list
            y2=upper_boundary.tolist(),  # pandas series to list
            color="#dba8e5",
            alpha=0.25,
        )

        sns.lineplot(
            data=self.linear_dataframe,
            x=self.linear_dataframe.index,
            y=self.linear_dataframe[f"{self.fid}_mean"],
            linestyle="--",
            color="#ab84b3",
            legend=False,
            ax=self.ax,
        )

    def plot_anomalies(self):
        sns.scatterplot(
            data=self.anomaly_dataframe.loc[
                self.anomaly_dataframe[f"{self.fid}_anomaly"]
            ],
            x=self.anomaly_dataframe.loc[
                self.anomaly_dataframe[f"{self.fid}_anomaly"]
            ].index,
            y=self.anomaly_dataframe.loc[self.anomaly_dataframe[f"{self.fid}_anomaly"]][
                f"{self.fid}_mean"
            ],
            marker="o",
            s=25,
            zorder=3,
            color="red",
            label="anomaly",
            legend=False,
            ax=self.ax,
        )
