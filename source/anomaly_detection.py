import pandas as pd
from system.helper_functions import get_monthly_keyword
from scipy.signal import find_peaks
from pathlib import Path


class Anomalies:
    def __init__(
        self,
        data=None,
        linear_data=None,
        anomaly_column=None,
        out_dir=None,
        pol="VH",
        orbit="asc",
        monthly=False,
        features=None,
    ):
        self.indicator_df = self._get_data(data)
        self.linear_regression_df = self._get_data(linear_data)
        self.column = anomaly_column  # dataframe column containing the anomaly data
        self.features = features
        self.out_dir = out_dir
        self.orbit = orbit
        self.pol = pol
        self.monthly = monthly

        self._prepare_dataframe()

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

    def _prepare_dataframe(self):
        if self.indicator_df is not None:
            self.dataframe = self.indicator_df.copy()  # create target dataframe

            for feature in self.features:
                self.dataframe[
                    f"{feature.fid}_anomaly"
                ] = False  # create new column storing anomaly state [boolean]

            self.dataframe = self.dataframe[sorted(self.dataframe.columns)]

    def find_extrema(self):
        for feature in self.features:
            anomaly = Anomaly(
                data=self.dataframe.loc[
                    :, self.dataframe.columns.str.startswith(f"{feature.fid}_")
                ],
                linear_data=self.linear_regression_df.loc[
                    :,
                    self.linear_regression_df.columns.str.startswith(f"{feature.fid}_"),
                ],
                fid=feature.fid,
                anomaly_column=self.column,
            )
            anomaly.find_feature_extrema()

            # set general anomaly dataframe to True where smaller feature anomaly dataframes have anomalies
            self.dataframe.loc[
                anomaly.dataframe.index[anomaly.dataframe[f"{feature.fid}_anomaly"]],
                f"{feature.fid}_anomaly",
            ] = True

    def save_anomalies(self):
        if self.monthly:
            self.save_raw()

        else:
            self.save_regression()

    def save_raw(self):
        out_file = self.out_dir.joinpath(
            "anomalies",
            f"indicator_1_anomalies_raw_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.dataframe.to_csv(out_file, decimal=".")

    def save_regression(self):
        out_file = self.out_dir.joinpath(
            "anomalies",
            f"indicator_1_anomalies_regression_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.dataframe.to_csv(out_file, decimal=".")

    def cleanup(self):
        del self.indicator_df
        del self.features
        del self.linear_regression_df


class Anomaly:
    def __init__(
        self,
        data=None,
        linear_data=None,
        parameters=(10, 1.5),
        fid=None,
        anomaly_column=None,
        factor=0.2,
    ):
        self.parameters = parameters
        self.fid = fid
        self.column = f"{self.fid}_{anomaly_column}"  # dataframe column containing the anomaly data
        self.ad = None
        self.dataframe = data
        self.dataframe_bak = self.dataframe.copy()
        self.linear_regression_df = linear_data
        self.factor = (
            factor  # factor representing sensitive/insensitive standard deviation
        )
        self._get_global_statistics()

    def _get_global_statistics(self):
        self.global_mean = self.dataframe[self.column].mean()  # global mean
        self.global_std = self.dataframe[
            f"{self.fid}_std"
        ].mean()  # global standard deviation

    def find_feature_extrema(self):
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

        adjacent_backscatter = (
            self.get_adjacent_backscatter()
        )  # get adjacent anomaly values
        self.dataframe = self.dataframe.drop(  # delete anomaly values based on date and backscatter value
            self.dataframe.iloc[adjacent_dates].index
            # ].index.intersection(  # indices from date and backscatter must be euqal
            #     self.dataframe.iloc[adjacent_backscatter].index
            # )
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
            self.dataframe.loc[self.dataframe[f"{self.fid}_anomaly"]]
            .index.to_series()
            .diff()
        )  # get difference in days between observations

        cond_df = self.dataframe.loc[
            (time_diff < f"{date_diff} days") & (self.dataframe[f"{self.fid}_anomaly"])
        ]  # difference in days must be less than date_diff

        adjacent_indices = list(
            self.dataframe.index.searchsorted(cond_df.index) - 1
        )  # adjacent anomalies in self.dataframe

        if len(adjacent_indices) > 0:
            adjacent_indices.insert(len(adjacent_indices), adjacent_indices[-1] + 1)

        return adjacent_indices

    def correct_insensitive(self):
        # -16.08
        # -16.34
        # 3.04 * 0.2 = 0.608
        # delete extrema if not significantly deviating from the global mean
        upper_df = self.dataframe.loc[
            (
                self.dataframe[self.column]
                < (
                    self.linear_regression_df[f"{self.fid}_mean"]
                    + self.factor
                    * self.linear_regression_df[
                        f"{self.fid}_std"
                    ]  # less than mean + std
                )
            )
            & (
                self.dataframe[self.column]
                > self.linear_regression_df[f"{self.fid}_mean"]
            )  # greater than linear mean
        ].loc[
            self.dataframe[f"{self.fid}_anomaly"]
        ]  # only include indices where anomaly is present

        lower_lower = self.dataframe.loc[
            (
                self.dataframe[self.column]
                > (
                    self.linear_regression_df[f"{self.fid}_mean"]
                    - self.factor
                    * self.linear_regression_df[
                        f"{self.fid}_std"
                    ]  # greater than mean - std
                )
            )
            & (
                self.dataframe[self.column]
                < self.linear_regression_df[f"{self.fid}_mean"]
            )  # less than linear mean
        ].loc[
            self.dataframe[f"{self.fid}_anomaly"]
        ]  # only include indices where anomaly is present

        self.dataframe = self.dataframe.drop(  # delete insensitive anomalies at index
            index=pd.concat(
                [upper_df, lower_lower], axis=0
            ).index  # combine upper and lower dataframe
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
        init_bloolean = self.dataframe.loc[self.dataframe[f"{self.fid}_anomaly"]]

        self.dataframe.loc[positive.index, self.column] = self.dataframe.loc[
            positive.index, self.column
        ].subtract(positive[self.column].subtract(self.global_mean).abs().mul(2))
        self.dataframe.loc[negative.index, self.column] = self.dataframe.loc[
            negative.index, self.column
        ].add(negative[self.column].subtract(self.global_mean).abs().mul(2))

        self.dataframe.loc[
            :, f"{self.fid}_anomaly"  # all rows  # index of column
        ] = False  # boolean values were overwritten before and must be reset
        self.dataframe.loc[
            init_bloolean.index, f"{self.fid}_anomaly"
        ] = True  # restore initial boolean valuesself.save(spline=True)

    def find_maxima(self):
        peaks, _ = find_peaks(self.dataframe[self.column].to_numpy(), distance=10)
        self.dataframe.iloc[
            peaks, [self.dataframe.columns.get_loc(f"{self.fid}_anomaly")]
        ] = True  # index -1 equals anomaly column

    def find_minima(self):
        self.flip_data()  # flip data to make original minima to maximas that can be detected
        self.find_maxima()  # find maxima (originally minima) on dataframe
        self.dataframe.loc[:, self.column] = self.dataframe_bak.loc[
            :, self.column
        ]  # revert flipped data column to original state
