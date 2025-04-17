"""Plot raw and regressed Sentinel-1 data."""
import math
from datetime import timedelta
from pathlib import Path
from types import TracebackType

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from system.helper_functions import (
    create_out_dir,
    get_monthly_keyword,
    get_split_keyword,
    mutliple_orbits_raw_range,
)
from system.orbit_collections import OrbitCollection as Orbits


class Plots:
    """Manage plots, either as single or as multiple plots."""

    def __init__(
        self: "Plots",
        raw_range: pd.DataFrame,
        name: str,
        features: list,
        out_dir: Path,
        orbit: str = "asc",
        pol: str = "VH",
        monthly: bool = False,
        linear: bool = False,
        linear_fill: bool = False,
        aoi_split: bool = False,
        max_cols: int = 2,
    ) -> None:
        """Initialize class Plots."""
        self.features = features
        self.raw_range_dataframe = raw_range
        self.name = name
        self.out_dir = out_dir
        self.orbit = orbit
        self.pol = pol
        self.monthly = monthly
        self.linear = linear  # whether to plot linear regression or not
        self.linear_fill = linear_fill  # whether to plot linear insensitive area or not
        self.aoi_split = aoi_split
        self.max_cols = max_cols
        self._get_subplots()
        self._get_long_orbit()

    def _get_rows_cols(self: "Plots") -> (int, int):
        """Get row and column count."""
        if len(self.features[:-1]) < self.max_cols:  # all plots fit into one row
            nrows = 1
            ncols = len(self.features)

        elif len(self.features[:-1]) == self.max_cols:  # features fill first row, total fills next row
            nrows = 2
            ncols = self.max_cols

        # having more plots than fit into one row
        # e.g. 8 % 4 = 0
        elif len(self.features[:-1]) > self.max_cols and len(self.features) % self.max_cols == 0:
            nrows = int(len(self.features) / self.max_cols)
            ncols = self.max_cols

        else:
            nrows = int(math.ceil(len(self.features) / self.max_cols))
            ncols = self.max_cols

        return nrows, ncols

    def _get_subplots(self: "Plots", width: int = 8, height: float = 4.5) -> None:
        """Get subplots."""
        nrows, ncols = self._get_rows_cols()
        self.fig, self.axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(width * ncols, height * nrows))

    def _get_long_orbit(self: "Plots") -> None:
        """Get long name from orbit keyword."""
        if self.orbit == "both":
            self.long_orbit = "ascending & descending"

        else:
            self.long_orbit = "ascending" if self.orbit == "asc" else "descending"

    def _get_plot_axis(self: "Plots", index: int = 0, single_axis: bool = True) -> plt.Axes:
        """Get the current axis that is used for plotting."""
        row = index // self.max_cols
        col = index % self.max_cols

        if isinstance(self.axs, plt.Axes):
            ax = self.axs

        else:
            ax = self.axs[col] if self.axs.shape == (self.max_cols,) else self.axs[row][col]

        if not single_axis:  # create a secondary y-axis
            ax = ax.twinx()
            ax.set(ylabel="2nd_des")

        return ax

    def __enter__(self: "Plots") -> "Plots":
        """Get opening handler on context manager."""
        return self

    def __exit__(
        self: "Plots",
        exc_type: type(BaseException),
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        """Get closing handler on context manager."""
        plt.close()

    def plot_features(self: "Plots", orbit_collection: Orbits) -> None:
        """Plot one or multiple features."""
        for subsets, anomalies, orbit, single_axis in orbit_collection.get_data():
            for index, feature in enumerate(self.features):
                feature_plot = PlotData(
                    raw_data=subsets.dataframe.loc[:, subsets.dataframe.columns.str.startswith(f"{feature.fid}_")],
                    raw_range=mutliple_orbits_raw_range(fid=feature.fid, orbit_collection=orbit_collection),
                    reg_data=subsets.regression_dataframe.loc[
                        :,
                        subsets.regression_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    anomaly_data=anomalies.dataframe.loc[  # name dataframe applies regardless of monthly or not
                        :, anomalies.dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
                    linear_data=subsets.linear_dataframe.loc[
                        :,
                        subsets.linear_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ],
                    ax=self._get_plot_axis(index=index, single_axis=single_axis),
                    fid=feature.fid,
                    orbit=orbit,
                    pol=self.pol,
                    linear_fill=self.linear_fill,
                    monthly=self.monthly,
                )

                # only plot raw range on left axis
                if feature_plot.ax.get_ylabel() != "2nd_des":
                    feature_plot.plot_rawdata_range()

                if self.linear:
                    feature_plot.plot_mean_range()

                if self.monthly:
                    feature_plot.plot_rawdata()

                else:
                    feature_plot.plot_regression()

                feature_plot.plot_anomalies()

    def plot_annotations(self: "Plots") -> None:
        """Set axes annotations."""
        self.fig.suptitle(f"{self.name}, {self.pol} polarization, {self.long_orbit} orbit")

        for index, ax in enumerate(self.fig.axes):
            if ax.get_ylabel() != "2nd_des":  # apply following annotations to left axis
                ax.set_ylabel("Sentinel-1 backscatter [dB]")
                ax.set_xlabel("")

                if index == (len(self.fig.axes) - 1):
                    ax.set_title("All features")

                else:
                    ax.set_title(f"Feature {self.features[index].fid}")

            else:  # if having secondary axis, do not label it
                ax.set_ylabel("")

            if (index + 1) % 2 == 0:  # 2nd column
                ax.set_ylabel("")

    def axes_limits(self: "Plots") -> None:
        """Set axes limits."""
        if len(self.features) > 1:
            mean_col = "total_mean"
            std_col = "total_std"

        else:
            mean_col = "0_mean"
            std_col = "0_std"

        plt.ylim(
            (self.raw_range_dataframe[mean_col] - self.raw_range_dataframe[std_col]).min() - 1,
            (self.raw_range_dataframe[mean_col] + self.raw_range_dataframe[std_col]).max() + 1,
        )

        if not self.monthly:
            plt.xlim(
                self.raw_range_dataframe.index[0].to_pydatetime() - timedelta(days=7),
                self.raw_range_dataframe.index[-1].to_pydatetime() + timedelta(days=7),
            )

    def axes_ticks(self: "Plots") -> None:
        """Set axes ticks."""
        for ax in self.fig.axes:
            if ax.get_ylabel() == "2nd_des":  # if having secondary axis
                ax.tick_params(
                    colors=sns.color_palette()[3], which="both", axis="y"
                )  # descending orbit red if on secondary y-axis

            else:  # apply following annotations to left axis
                ax.tick_params(colors=sns.color_palette()[0], which="both", axis="y")  # ascending orbit always blue

            ax.xaxis.set_minor_locator(mdates.MonthLocator())  # minor ticks display months
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(""))  # minor ticks are not labelled

    def unused_subplots(self: "Plots") -> None:
        """Delete unused subplots."""
        if isinstance(self.axs, np.ndarray):
            for i in reversed(range(len(self.axs.flatten()) - len(self.features))):  # get count of empty subplots
                self.fig.delaxes(self.axs.flatten()[len(self.axs.flatten()) - 1 - i])

    def plot_legend(self: "Plots") -> None:
        """Plot and adjust the legend."""
        # get handles and labels from each subplot
        handles = [ax.get_legend_handles_labels()[0] for ax in self.fig.axes]
        labels = [ax.get_legend_handles_labels()[1] for ax in self.fig.axes]

        # merge into broader lists, originals were like [[handle 1, handle 2], [handle 3, handle 4]]
        handles = [item for sub in handles for item in sub]
        labels = [item for sub in labels for item in sub]

        uniques, indices = np.unique(labels, return_index=True)  # get unique labels and their indices
        handles = np.array(handles)[np.array(indices)]  # get handles at unique indices
        labels = np.array(labels)[np.array(indices)]  # get labels at unique indices

        uniques = [
            (handle, label) for i, (handle, label) in enumerate(zip(handles, labels, strict=True))
        ]  # arrange handles and labels as pairs

        self.fig.legend(*zip(*uniques, strict=True), loc="outside lower center", ncols=2)

    def layout(self: "Plots") -> None:
        """Define figure layout."""
        self.fig.set_layout_engine(layout="compressed")

    def finalize(self: "Plots") -> None:
        """Post-process the plots."""
        self.unused_subplots()
        self.axes_limits()
        self.axes_ticks()
        self.plot_annotations()
        self.plot_legend()
        self.layout()

    def correct_name(self: "Plots") -> None:
        """Correct facility name to be separated by whitespace, e.g. BMW Regensburg."""
        self.name = self.name.lower()

        if " " in self.name:
            self.name = "_".join(self.name.split(" "))

    def get_save_orbit(self: "Plots") -> None:
        """Get orbit keyword."""
        if self.orbit == "both":
            self.orbit = "asc_des"

    def get_extensions(self: "Plots", svg: bool = False) -> list:
        """Get file extension, either PNG or SVG."""
        exts = ["png"]
        create_out_dir(base_dir=self.out_dir.joinpath("plot"), out_dir="png")

        if svg:
            exts.append("svg")
            create_out_dir(base_dir=self.out_dir.joinpath("plot"), out_dir="svg")

        return exts

    def save_regression(self: "Plots", dpi: int = 150, svg: bool = False) -> None:
        """Save regressed raw data plot."""
        self.correct_name()
        self.get_save_orbit()
        exts = self.get_extensions(svg=svg)

        for ext in exts:
            out_file = self.out_dir.joinpath(
                "plot",
                ext,
                f"indicator_1_{self.name}_regression_{get_split_keyword(aoi_split=self.aoi_split)}_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.{ext}",
            )

            self.fig.savefig(out_file, dpi=dpi)

    def save_raw(self: "Plots", dpi: int = 150, svg: bool = False) -> None:
        """Save unregressed raw data plot."""
        self.correct_name()
        self.get_save_orbit()
        exts = self.get_extensions(svg=svg)

        for ext in exts:
            out_file = self.out_dir.joinpath(
                "plot",
                ext,
                f"indicator_1_{self.name}_rawdata_{get_split_keyword(aoi_split=self.aoi_split)}_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.{ext}",
            )

            self.fig.savefig(out_file, dpi=dpi)

    @staticmethod
    def show_plot() -> None:
        """Show plot."""
        plt.show()


class PlotData:
    """Encapsulate methods for plotting the dataframes."""

    def __init__(
        self: "PlotData",
        ax: plt.Axes,
        raw_data: pd.DataFrame | None = None,
        raw_range: pd.DataFrame | None = None,
        reg_data: pd.DataFrame | None = None,
        linear_data: pd.DataFrame | None = None,
        anomaly_data: pd.DataFrame | None = None,
        orbit: str = "asc",
        pol: str = "VH",
        fid: str = "total",
        linear_fill: bool = False,
        monthly: bool = False,
    ) -> None:
        """Initialize PlotData class."""
        self.raw_dataframe = raw_data
        self.raw_range_dataframe = raw_range
        self.reg_dataframe = reg_data
        self.linear_dataframe = linear_data
        self.anomaly_dataframe = anomaly_data
        self.ax = ax
        self.fid = fid
        self.orbit = orbit
        self.pol = pol
        self.linear_fill = linear_fill
        self.monthly = monthly

    def plot_rawdata(self: "PlotData", zorder: int = 5, alpha: float = 1) -> None:
        """Plot raw data as line."""
        sns.lineplot(
            data=self.raw_dataframe,
            x=self.raw_dataframe.index,
            y=self.raw_dataframe[f"{self.fid}_mean"],
            legend=False,
            label="raw mean",
            linestyle="dotted" if not self.monthly else "solid",
            zorder=zorder,
            alpha=alpha,
            ax=self.ax,
            color=sns.color_palette()[3]
            if self.ax.get_ylabel() == "2nd_des"  # descending orbit in red, if on secondary y-axis
            else sns.color_palette()[0],  # ascending orbit always blue
        )

    def plot_rawdata_range(self: "PlotData", zorder: int = 0) -> None:
        """Plot raw data as range of mean +/- standard deviation."""
        plusminus = "\u00B1"
        upper_boundary = self.raw_range_dataframe[f"{self.fid}_mean"] + self.raw_range_dataframe[f"{self.fid}_std"]
        lower_boundary = self.raw_range_dataframe[f"{self.fid}_mean"] - self.raw_range_dataframe[f"{self.fid}_std"]

        # plot of baundaries
        for boundary in [upper_boundary, lower_boundary]:
            sns.lineplot(
                data=self.raw_range_dataframe,
                x=self.raw_range_dataframe.index,
                y=boundary,
                color="#d3d3d3",
                alpha=0,
                legend=False,
                zorder=zorder,
            )

        # fill space between boundaries
        self.ax.fill_between(
            self.raw_range_dataframe.index,
            lower_boundary.tolist(),  # pandas series to list
            upper_boundary.tolist(),  # pandas series to list
            color="#ebebeb",
            label=f"mean {plusminus} std",
            zorder=zorder,
        )

    def plot_regression(self: "PlotData", zorder: int = 10) -> None:
        """Plot regression curve."""
        sns.lineplot(
            data=self.reg_dataframe,
            x=self.reg_dataframe.index,
            y=self.reg_dataframe[f"{self.fid}_mean"],
            label=f"{self.orbit}_regression",
            legend=False,
            zorder=zorder,
            ax=self.ax,
            color=sns.color_palette()[3]
            if self.ax.get_ylabel() == "2nd_des"  # descending orbit in red, if on secondary y-axis
            else sns.color_palette()[0],  # ascending orbit always blue
        )

    def plot_mean_range(self: "PlotData", factor: float = 0.2, zorder: int = 15) -> None:
        """Plot a range of mean + std that defines an insensitive area where anomalies are less likely."""
        if self.linear_fill:
            upper_boundary = (
                self.linear_dataframe[f"{self.fid}_mean"] + factor * self.linear_dataframe[f"{self.fid}_std"]
            )
            lower_boundary = (
                self.linear_dataframe[f"{self.fid}_mean"] - factor * self.linear_dataframe[f"{self.fid}_std"]
            )

            self.ax.fill_between(
                x=self.linear_dataframe.index,
                y1=lower_boundary.tolist(),  # pandas series to list
                y2=upper_boundary.tolist(),  # pandas series to list
                alpha=0.2,  # use 0.25 if desired to have the +/- std range visible
                zorder=zorder,
                color=sns.color_palette()[3]  # alternate violet "#ab84b3"
                if self.ax.get_ylabel() == "2nd_des"  # descending orbit in red, if on secondary y-axis
                else sns.color_palette()[0],  # ascending orbit always blue
            )

        sns.lineplot(
            data=self.linear_dataframe,
            x=self.linear_dataframe.index,
            y=self.linear_dataframe[f"{self.fid}_mean"],
            linestyle="--",
            legend=False,
            ax=self.ax,
            label=f"{self.orbit}_linear_mean",
            zorder=zorder,
            alpha=0.5,
            color=sns.color_palette()[3]  # alternate violet "#ab84b3"
            if self.ax.get_ylabel() == "2nd_des"  # descending orbit in red, if on secondary y-axis
            else sns.color_palette()[0],  # ascending orbit always blue
        )

    def plot_anomalies(self: "PlotData", zorder: int = 20) -> None:
        """Plot anomalies as scatters."""
        sns.scatterplot(
            data=self.anomaly_dataframe.loc[self.anomaly_dataframe[f"{self.fid}_anomaly"]],
            x=self.anomaly_dataframe.loc[self.anomaly_dataframe[f"{self.fid}_anomaly"]].index,
            y=self.anomaly_dataframe.loc[self.anomaly_dataframe[f"{self.fid}_anomaly"]][f"{self.fid}_mean"],
            marker="v",
            s=40,
            zorder=zorder,
            label=f"{self.orbit}_anomaly",
            legend=False,
            ax=self.ax,
            color=sns.color_palette()[3]  # alternate red
            if self.ax.get_ylabel() == "2nd_des"  # descending orbit in red, if on secondary y-axis
            else sns.color_palette()[0],  # ascending orbit always blue
        )
