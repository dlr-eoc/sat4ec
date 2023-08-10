import pandas as pd
import matplotlib.pyplot as plt
from adtk.visualization import plot
from adtk.detector import InterQuartileRangeAD


class Anomaly:
    def __init__(self, df=None, parameters=(10, 1.5), column=None, out_dir=None, out_name=None):
        self.parameters = parameters
        self.df = df
        self.column = column  # dataframe column containing the anomaly data
        self.ad = None
        self.anomalies = None
        self.out_dir = out_dir
        self.out_name = out_name

    def _prepare_df(self):
        self.df = self.df.set_index("start_date")

    def plot_df(self):
        # plot timeseries
        plot(self.df, ts_linewidth=1, ts_markersize=3)
        plt.show()
        plt.close()

    def plot_anomaly(self):
        fig, ax = plt.subplots()
        # plot timeseries and detected anomalies
        plot(
            self.df.loc[:, [self.column]],
            anomaly=self.anomalies.loc[:, [self.column]],
            ts_linewidth=1,
            ts_markersize=3,
            axes=ax,
            anomaly_markersize=5,
            anomaly_color="red",
            anomaly_tag="marker",
        )

        plt.title("InterQuartileRangeAD")
        fig.savefig(self.out_dir.joinpath(f"aoi_anomalies_{self.out_name}.png"))
        # plt.show()
        plt.close()

    def apply_anomaly_detection(self, normalize=True):
        # fit anomaly detection criterion on historic timeseries
        # compare time series values with 1st and 3rd quartiles of historic data and identify time points as anomalous
        # when differences are beyond the inter-quartile range (IQR) times factor c (lower, upper).
        # setting c1 to a large value basically ignores lower bound anomalies (here would be droughts)
        self.ad = InterQuartileRangeAD(c=self.parameters)
        self.df = self.df.sort_index()

        if normalize:
            self._normalize_df()

        self.ad.fit(self.df.loc[:, [self.column]])
        self.anomalies = self.ad.detect(self.df.loc[:, [self.column]])  # predict if a flood is present

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
