import pandas as pd
import matplotlib.pyplot as plt
from adtk.visualization import plot
from adtk.detector import InterQuartileRangeAD, PersistAD, QuantileAD, SeasonalAD
from datetime import datetime


class Anomaly:
    def __init__(self, df=None, parameters=(10, 1.5), column=None, out_dir=None, out_name=None, options=None, orbit="asc"):
        self.parameters = parameters
        self.df = df
        self.column = column  # dataframe column containing the anomaly data
        self.ad = None
        self.anomalies_df = None
        self.out_dir = out_dir
        self.out_name = out_name
        self.orbit = orbit
        self.normalize = options["normalize"]
        self.invert = options["invert"]
        self.plot = options["plot"]

    def _prepare_df(self):
        self.df = self.df.set_index("start_date")

    def save(self, pol="VH"):
        out_file = self.out_dir.joinpath(
            datetime.now().strftime("%Y_%m_%d"),
            f"indicator_1{self.orbit}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv",
        )

        if not out_file.parent.exists():
            out_file.parent.mkdir(parents=True, exist_ok=True)

        self.anomalies_df.to_csv(out_file)

        if self.plot:
            self.plot_anomaly(pol=pol)

    def plot_anomaly(self, pol="VH"):
        fig, ax = plt.subplots()
        # plot timeseries and detected anomalies
        plot(
            self.anomalies_df.loc[:, [self.column]],
            anomaly=self.anomalies_df.loc[:, [self.column]],
            ts_linewidth=1,
            ts_markersize=3,
            axes=ax,
            anomaly_markersize=5,
            anomaly_color="red",
            anomaly_tag="marker",
        )

        plt.title(f"InterQuartileRangeAD {pol} polarization")
        fig.savefig(self.out_dir.joinpath(f"aoi_anomalies_{self.out_name}.png"))
        # plt.show()
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
        self.anomalies_df = self.ad.detect(self.df.loc[:, [self.column]])  # predict if an anomaly is present

        if self.invert:
            mask = self.anomalies_df[self.column].to_numpy()
            self.anomalies_df[self.column] = ~mask

    def rename_column(self):
        self.anomalies_df.rename(columns={self.column: "anomaly"}, inplace=True)
        self.column = "anomaly"

    def join_with_indicator(self, indicator_df):
        self.rename_column()
        self.anomalies_df = pd.concat([self.anomalies_df, indicator_df], axis=1)
        self.anomalies_df.insert(0, "interval_to", self.anomalies_df.pop("interval_to"))

    def _normalize_df(self):
        self.df.loc[:, self.column] = (self.df.loc[:, [self.column]] - self.df.loc[:,
                                                                       [self.column]].mean()) \
                                      / self.df.loc[:, [self.column]].std()  # standardize timeseries

    @staticmethod
    def _parse_date(filename=None):
        return pd.to_datetime(filename.split("_")[4])

    # def get_s1_flood_status(self):
    #     # get status if significatly flooded of current S1 scene
    #     self.flooded = self.anomalies.loc[self._parse_date(filename=self.s1), self.column]
    #     result = {
    #         "s1_scene": self.s1,
    #         "flood_anomaly": bool(self.flooded)
    #     }
