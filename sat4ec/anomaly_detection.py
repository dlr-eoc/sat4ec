import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from adtk.visualization import plot as ad_plot
from adtk.detector import InterQuartileRangeAD, PersistAD, QuantileAD, SeasonalAD
from pathlib import Path


class Anomaly:
    def __init__(
        self,
        data=None,
        parameters=(10, 1.5),
        anomaly_column=None,
        df_columns=None,
        out_dir=None,
        pol="VH",
        options=None,
        orbit="asc",
    ):
        self.parameters = parameters
        self.column = anomaly_column  # dataframe column containing the anomaly data
        self.df_columns = df_columns  # dataframe columns that should be plotted
        self.ad = None
        self.dataframe = None  # output
        self.out_dir = out_dir
        self.orbit = orbit
        self.pol = pol
        self.normalize = options["normalize"]
        self.invert = options["invert"]
        self.plot = options["plot"]

        if isinstance(data, Path):
            self.filename = data
            self._load_df()

        elif isinstance(data, str):
            if Path(data).exists():
                self.filename = Path(data)
                self._load_df()

        elif isinstance(data, pd.DataFrame):
            self.filename = None
            self.indicator_df = data

    def _load_df(self):
        self.indicator_df = pd.read_csv(self.filename)
        self.indicator_df["interval_from"] = pd.to_datetime(self.indicator_df["interval_from"])
        self.indicator_df = self.indicator_df.set_index("interval_from")

    def save(self):
        out_file = self.out_dir.joinpath(
            f"indicator_1_anomalies_{self.orbit}_{self.pol}.csv",
        )

        self.dataframe.to_csv(out_file)

        if self.plot:
            self.plot_anomaly()

    def plot_anomaly(self):
        orbit = "ascending" if self.orbit == "asc" else "descending"
        fig, ax = plt.subplots(1, 1, figsize=(20, 10))

        for col in self.df_columns:
            sns.lineplot(
                data=self.dataframe,
                x=self.dataframe.index,
                y=self.dataframe[col],
                marker="o",
                markersize=5,
                label=col,
                legend=False,
                zorder=1,
            )

        sns.scatterplot(
            data=self.dataframe.loc[self.dataframe["anomaly"]],
            x=self.dataframe.loc[self.dataframe["anomaly"]].index,
            y=self.dataframe.loc[self.dataframe["anomaly"]]["mean"],
            marker="o",
            s=25,
            zorder=2,
            color="red",
            label="anomaly"
        )

        plt.title(f"Anomalies {self.pol} polarization, {orbit} orbit")
        plt.ylabel("Sentinel-1 backscatter [dB]")
        plt.xlabel("Timestamp")
        fig.legend(loc="outside lower center", ncols=len(self.df_columns)+1)
        fig.savefig(
            self.out_dir.joinpath(
                f"indicator_1_anomalies_{self.orbit}_{self.pol}.png",
            )
        )

        plt.close()

    def apply_anomaly_detection(self):
        # fit anomaly detection criterion on historic timeseries
        # compare time series values with 1st and 3rd quartiles of historic data and identify time points as anomalous
        # when differences are beyond the inter-quartile range (IQR) times factor c (lower, upper).
        # setting c1 to a large value basically ignores lower bound anomalies (here would be droughts)
        self.ad = InterQuartileRangeAD(c=self.parameters)
        # self.ad = PersistAD()
        # self.ad = QuantileAD(low=1)
        # self.ad = SeasonalAD()
        self.indicator_df = self.indicator_df.sort_index()

        if self.normalize:
            self._normalize_df()

        self.ad.fit(self.indicator_df.loc[:, [self.column]])
        self.dataframe = self.ad.detect(
            self.indicator_df.loc[:, [self.column]]
        )  # predict if an anomaly is present

        if self.invert:
            mask = self.dataframe[self.column].to_numpy()
            self.dataframe[self.column] = ~mask

    def rename_column(self):
        self.dataframe.rename(columns={self.column: "anomaly"}, inplace=True)

    def join_with_indicator(self):
        self.rename_column()
        self.dataframe = pd.concat([self.dataframe, self.indicator_df], axis=1)
        self.dataframe.insert(0, "interval_to", self.dataframe.pop("interval_to"))

    def _normalize_df(self):
        self.indicator_df.loc[:, self.column] = (
            self.indicator_df.loc[:, [self.column]] - self.indicator_df.loc[:, [self.column]].mean()
        ) / self.indicator_df.loc[
            :, [self.column]
        ].std()  # standardize timeseries
