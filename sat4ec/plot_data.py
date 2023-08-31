import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path


class PlotData:
    def __init__(self, raw_data=None, spline_data=None, anomaly_data=None, raw_columns=None, orbit="asc"):
        self.orbit = orbit
        self.raw_columns = raw_columns

        self.raw_dataframe = self._get_data(data=raw_data)
        self.spline_dataframe = self._get_data(data=spline_data)
        self.anomaly_dataframe = self._get_data(data=anomaly_data)
        self._get_subplot()
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

    def _get_subplot(self):
        self.fig, self.ax = plt.subplots(1, 1, figsize=(20, 10))

    def _get_long_orbit(self):
        self.long_orbit = "ascending" if self.orbit == "asc" else "descending"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        plt.close()

    def plot_rawdata(self, show=False):
        for col in self.raw_columns:
            sns.lineplot(
                data=self.raw_dataframe,
                x=self.raw_dataframe.index,
                y=self.raw_dataframe[col],
                # marker="o",
                # markersize=5,
                label=col,
                legend=False,
                zorder=1,
                ax=self.ax,
            )

        if show:  # for development
            plt.show()

    def plot_splinedata(self, show=False):
        for col in self.raw_columns:
            sns.lineplot(
                data=self.spline_dataframe,
                x=self.spline_dataframe.index,
                y=self.spline_dataframe[col],
                # marker="o",
                # markersize=5,
                label=col,
                legend=False,
                zorder=1,
                ax=self.ax,
            )

        if show:  # for development
            plt.show()

    def plot_anomalies(self):
        sns.scatterplot(
            data=self.anomaly_dataframe.loc[self.anomaly_dataframe["anomaly"]],
            x=self.anomaly_dataframe.loc[self.anomaly_dataframe["anomaly"]].index,
            y=self.anomaly_dataframe.loc[self.anomaly_dataframe["anomaly"]]["mean"],
            marker="o",
            s=25,
            zorder=2,
            color="red",
            label="anomaly",
            ax=self.ax
        )

        # plt.title(f"Anomalies {self.pol} polarization, {orbit} orbit")
        # plt.ylabel("Sentinel-1 backscatter [dB]")
        # plt.xlabel("Timestamp")
        # fig.legend(loc="outside lower center", ncols=len(self.df_columns) + 1)
        # fig.savefig(
        #     self.out_dir.joinpath(
        #         "plot", f"indicator_1_anomalies_{self.orbit}_{self.pol}.png",
        #     )
        # )
