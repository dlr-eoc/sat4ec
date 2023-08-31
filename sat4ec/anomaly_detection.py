import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from adtk.detector import InterQuartileRangeAD, PersistAD, QuantileAD, SeasonalAD
from scipy.signal import find_peaks
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

        self.indicator_df = self._get_data(data)

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

    def save(self, spline=False):
        if spline:
            out_file = self.out_dir.joinpath(
                "product", f"indicator_1_anomalies_spline_{self.orbit}_{self.pol}.csv",
            )

        else:
            out_file = self.out_dir.joinpath(
                "product", f"indicator_1_anomalies_raw_{self.orbit}_{self.pol}.csv",
            )

        self.dataframe.to_csv(out_file)

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

    def apply_find_peaks(self):
        peaks, _ = find_peaks(self.indicator_df[self.column].to_numpy(), distance=10)
        plt.plot(self.indicator_df[self.column])
        plt.plot(self.indicator_df.index[peaks], self.indicator_df[self.column][peaks], "x")
        plt.show()

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
