import pandas as pd
from system.helper_functions import get_monthly_keyword
from scipy.signal import find_peaks
from pathlib import Path


class Anomaly:
    def __init__(
        self,
        data=None,
        parameters=(10, 1.5),
        anomaly_column=None,
        out_dir=None,
        pol="VH",
        orbit="asc",
        factor=0.25,
        monthly=False
    ):
        self.parameters = parameters
        self.column = anomaly_column  # dataframe column containing the anomaly data
        self.ad = None
        self.dataframe = None  # output
        self.out_dir = out_dir
        self.orbit = orbit
        self.pol = pol
        self.factor = (
            factor  # factor representing sensitive/insensitive standard deviation
        )
        self.monthly = monthly

        self.indicator_df = self._get_data(data)
        self._prepare_dataframe()
        self._get_global_statistics()

    def _get_global_statistics(self):
        self.global_mean = self.dataframe[self.column].mean()  # global mean
        self.global_std = self.dataframe["std"].mean()  # global standard deviation

    def _prepare_dataframe(self):
        self.dataframe = self.indicator_df.copy()  # create target dataframe
        self.dataframe[
            "anomaly"
        ] = False  # create new column storing anomaly state [boolean]

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

    def save_raw(self):
        out_file = self.out_dir.joinpath(
            "anomalies",
            f"indicator_1_anomalies_raw_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.dataframe.to_csv(out_file)

    def save_spline(self):
        out_file = self.out_dir.joinpath(
            "anomalies",
            f"indicator_1_anomalies_spline_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.dataframe.to_csv(out_file)

    def find_extrema(self):
        self.find_maxima()  # find maxima on dataframe
        self.find_minima()  # find minima on dataframe
        self.correct_insensitive()  # drop indices not significantly deviating from the global mean
        self.delete_adjacent()  # drop indices of anomalies in close neighboorhood

    def delete_adjacent(self):
        """
        Delete anomalies that are in close neighboorhood as these represent saddle points.
        Anomalies on saddle points were selected as the find extrema method is executed twice on minima and maxima.
        """
        adjacent_dates = self.get_adjacent_dates()  # get adjacent anomaly dates
        adjacent_backscatter = self.get_adjacent_backscatter()  # get adjacent anomaly values
        self.dataframe = self.dataframe.drop(  # delete anomaly values based on date and backscatter value
            self.dataframe.iloc[adjacent_dates].index.intersection(  # indices from date and backscatter must be euqal
                self.dataframe.iloc[adjacent_backscatter].index
            )
        )

    def get_adjacent_backscatter(self):
        backscatter_diff = self.dataframe[
            self.column
        ].diff()  # get difference in backscatter between observations
        cond_df = self.dataframe.loc[
            backscatter_diff.abs() < (2 * self.factor * self.global_std)
        ]  # difference in backscatter must be less than part of standard deviation

        adjacent_indices = list(
            self.dataframe.index.searchsorted(cond_df.index) - 1
        )  # adjacent anomalies in self.dataframe

        if len(adjacent_indices) > 0:
            adjacent_indices.insert(len(adjacent_indices), adjacent_indices[-1] + 1)

        return adjacent_indices

    def get_adjacent_dates(self, date_diff=31):
        time_diff = (
            self.dataframe.index.to_series().diff()
        )  # get difference in days between observations
        cond_df = self.dataframe.loc[
            time_diff < f"{date_diff} days"
        ]  # difference in days must be less than date_diff

        adjacent_indices = list(
            self.dataframe.index.searchsorted(cond_df.index) - 1
        )  # adjacent anomalies in self.dataframe

        if len(adjacent_indices) > 0:
            adjacent_indices.insert(len(adjacent_indices), adjacent_indices[-1] + 1)

        return adjacent_indices

    def correct_insensitive(self):
        # correct extrema if not significantly deviating from the global mean
        upper_df = self.dataframe.loc[
            self.dataframe[self.column]
            > (
                self.global_mean + self.factor * self.global_std
            )  # greater than mean + std
        ].loc[
            self.dataframe["anomaly"]
        ]  # only include indices where anomaly is present
        lower_lower = self.dataframe.loc[
            self.dataframe[self.column]
            < (self.global_mean - self.factor * self.global_std)  # less than mean + std
        ].loc[
            self.dataframe["anomaly"]
        ]  # only include indices where anomaly is present

        self.dataframe = self.dataframe.drop(  # delete insensitive anomalies at index
            index=self.dataframe.index.difference(  # compute difference to original dataframe, i.e. drop indices
                pd.concat(
                    [upper_df, lower_lower], axis=0
                ).index  # combine upper and lower dataframe
            )
        )

    def flip_data(self):
        positive = self.dataframe.loc[
            self.dataframe[self.column] > self.global_mean  # positive part
        ]
        negative = self.dataframe.loc[
            self.dataframe[self.column] < self.global_mean  # negative part
        ]

        # rows where column initially True
        # flipping the dataframe overwrites the boolean values
        # must be restored later
        init_bloolean = self.dataframe.loc[self.dataframe["anomaly"]]

        self.dataframe.loc[positive.index, self.column] = self.dataframe.loc[
            positive.index, self.column
        ].subtract(positive[self.column].subtract(self.global_mean).abs().mul(2))
        self.dataframe.loc[negative.index, self.column] = self.dataframe.loc[
            negative.index, self.column
        ].add(negative[self.column].subtract(self.global_mean).abs().mul(2))

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
        self.dataframe[self.column] = self.indicator_df[
            self.column
        ]  # revert flipped data column to original state
