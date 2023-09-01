import pandas as pd
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

        self.indicator_df = self._get_data(data)
        self._prepare_dataframe()

    def _prepare_dataframe(self):
        self.dataframe = self.indicator_df.copy()  # create target dataframe
        self.dataframe["anomaly"] = False  # create new column storing anomaly state [boolean]

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
                "anomalies",
                f"indicator_1_anomalies_spline_{self.orbit}_{self.pol}.csv",
            )

        else:
            out_file = self.out_dir.joinpath(
                "anomalies",
                f"indicator_1_anomalies_raw_{self.orbit}_{self.pol}.csv",
            )

        self.dataframe.to_csv(out_file)

    def find_extrema(self):
        self.find_maxima()  # find maxima on dataframe
        self.find_minima()  # find minima on dataframe

    def flip_data(self):
        global_mean = self.dataframe[self.column].mean()  # global mean
        positive = self.dataframe.loc[
            self.dataframe[self.column] > global_mean  # positive part
        ]
        negative = self.dataframe.loc[
            self.dataframe[self.column] < global_mean  # negative part
        ]

        # rows where column initially True
        # flipping the dataframe overwrites the boolean values
        # must be restored later
        init_bloolean = self.dataframe.loc[self.dataframe["anomaly"]]

        self.dataframe.loc[positive.index, self.column] = self.dataframe.loc[
            positive.index, self.column
        ].subtract(positive[self.column].subtract(global_mean).abs().mul(2))
        self.dataframe.loc[negative.index, self.column] = self.dataframe.loc[
            negative.index, self.column
        ].add(negative[self.column].subtract(global_mean).abs().mul(2))

        self.dataframe[
            "anomaly"
        ] = False  # boolean values were overwritten before and must be reset
        self.dataframe.loc[
            init_bloolean.index, "anomaly"
        ] = True  # restore initial boolean valuesself.save(spline=True)

    def find_maxima(self):
        peaks, _ = find_peaks(self.dataframe[self.column].to_numpy(), distance=10)
        self.dataframe.iloc[peaks, [-1]] = True  # index -1 equals anomaly column

    def find_minima(self):
        self.flip_data()  # flip data to make original minima to maximas that can be detected
        self.find_maxima()  # find maxima (originally minima) on dataframe
        self.dataframe[self.column] = self.indicator_df[self.column]  # revert flipped data column to original state
