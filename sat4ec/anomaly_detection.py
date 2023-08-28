import pandas as pd
import matplotlib.pyplot as plt
from adtk.visualization import plot as ad_plot
from adtk.detector import InterQuartileRangeAD, PersistAD, QuantileAD, SeasonalAD


class Anomaly:
    def __init__(
        self,
        df=None,
        parameters=(10, 1.5),
        anomaly_column=None,
        df_columns=None,
        out_dir=None,
        pol="VH",
        timestamp=None,
        options=None,
        outlier_thresholds=None,
        outliers=None,
        orbit="asc",
    ):
        self.parameters = parameters
        self.df = df  # input
        self.column = anomaly_column  # dataframe column containing the anomaly data
        self.df_columns = df_columns  # dataframe columns that should be plotted
        self.ad = None
        self.dataframe = None  # output
        self.out_dir = out_dir
        self.orbit = orbit
        self.timestamp = timestamp
        self.pol = pol
        self.normalize = options["normalize"]
        self.invert = options["invert"]
        self.plot = options["plot"]

        self._get_outliers(options=options, outlier_thresholds=outlier_thresholds, outliers=outliers)

    def _get_outliers(self, options, outlier_thresholds, outliers):
        if options["minmax"]:
            self.minmax = outlier_thresholds

        if options["outliers"]:
            self.outliers = outliers

    def save(self):
        out_file = self.out_dir.joinpath(
            f"indicator_1_{self.orbit}_{self.pol}_{self.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        )

        self.dataframe.to_csv(out_file)

        if self.plot:
            self.plot_anomaly()

    def plot_anomaly(self):
        orbit = "ascending" if self.orbit == "asc" else "descending"
        fig, ax = plt.subplots(1, 1, figsize=(20, 10))
        cmap = plt.cm.get_cmap("tab20")

        # plot timeseries and detected anomalies
        axis = ad_plot(
            self.df.loc[:, ["mean"]],
            anomaly=self.dataframe.loc[:, ["anomaly"]],
            ts_linewidth=1,
            ts_markersize=2,
            ts_color=cmap(0),
            axes=ax,
            anomaly_markersize=5,
            anomaly_color="red",
            anomaly_tag="marker",
            legend=False,
            )

        plt.fill_between(self.df.index, self.df["mean"].min(), self.minmax["min"], color="grey", alpha=0.25)
        plt.fill_between(self.df.index, self.df["mean"].max(), self.minmax["max"], color="grey", alpha=0.25)

        plt.title(f"Anomalies {self.pol} polarization, {orbit} orbit")
        plt.ylabel("Sentinel-1 backscatter [dB]")
        fig.legend(loc="outside lower center", ncols=len(self.df_columns)+1)
        fig.savefig(
            self.out_dir.joinpath(
                f"anomalies_indicator_1_{self.orbit}_{self.pol}_{self.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.png",
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
        self.df = self.df.sort_index()

        if self.normalize:
            self._normalize_df()

        self.ad.fit(self.df.loc[:, [self.column]])
        self.dataframe = self.ad.detect(
            self.df.loc[:, [self.column]]
        )  # predict if an anomaly is present

        if self.invert:
            mask = self.dataframe[self.column].to_numpy()
            self.dataframe[self.column] = ~mask

    def rename_column(self):
        self.dataframe.rename(columns={self.column: "anomaly"}, inplace=True)

    def join_with_indicator(self, indicator_df):
        self.rename_column()
        self.dataframe = pd.concat([self.dataframe, indicator_df], axis=1)
        self.dataframe.insert(0, "interval_to", self.dataframe.pop("interval_to"))

    def _normalize_df(self):
        self.df.loc[:, self.column] = (
            self.df.loc[:, [self.column]] - self.df.loc[:, [self.column]].mean()
        ) / self.df.loc[
            :, [self.column]
        ].std()  # standardize timeseries
