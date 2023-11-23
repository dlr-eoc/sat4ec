import logging
import sys
import yaml
import pandas as pd
import numpy as np
import copy

from scipy.interpolate import splrep, BSpline
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from dateutil.relativedelta import relativedelta
from datetime import datetime, time
from jsonformatter import JsonFormatter
from pathlib import Path


class Regression:
    def __init__(self, fid=None, df=None, mode="spline", monthly=False):
        self.mode = mode
        self.monthly = monthly
        self.fid = fid
        self.dataframe = df.copy(deep=True)
        self.regression_dataframe = None

    def apply_feature_regression(self):
        self.prepare_regression()
        self.linear_regression()

        if self.monthly:
            self.regression_dataframe[f"{self.fid}_mean"] = self.dataframe[
                f"{self.fid}_mean"
            ]

        else:  # apply regression on daily data, not monthly
            if self.mode == "rolling":
                self.regression_dataframe[
                    f"{self.fid}_mean"
                ] = self.apply_pandas_rolling()

            elif self.mode == "spline":
                self.regression_dataframe[f"{self.fid}_mean"] = self.apply_spline()

            elif self.mode == "poly":
                self.regression_dataframe[f"{self.fid}_mean"] = self.apply_polynomial()

            else:
                raise ValueError(
                    f"The provided mode {self.mode} is not supported. Please choose from [rolling, spline, poly]."
                )

        self.dataframe = self.dataframe.drop("interval_diff", axis=1, inplace=False)

    def apply_pandas_rolling(self):
        return (
            self.dataframe[f"{self.fid}_mean"]
            .rolling(
                5,
                center=True,
                closed="both",
                win_type="cosine",
            )
            .mean(5)
        )  # cosine

    def prepare_regression(self):
        time_diff = (self.dataframe.index[0] - self.dataframe.index).days * (
            -1
        )  # date difference
        date_range = pd.date_range(
            freq="1D", start=self.dataframe.index[0], end=self.dataframe.index[-1]
        )

        self.regression_dataframe = pd.DataFrame(
            {"interval_from": self.dataframe.index}, index=self.dataframe.index
        )
        self.dataframe.loc[:, "interval_diff"] = time_diff  # temporary
        self.linear_dataframe = pd.DataFrame(
            {"interval_diff": np.arange(time_diff[-1] + 1)}, index=date_range
        )

    def apply_polynomial(self):
        poly_reg_model = LinearRegression()
        poly = PolynomialFeatures(degree=5, include_bias=False)
        poly_features = poly.fit_transform(
            self.dataframe["interval_diff"].values.reshape(-1, 1)
        )
        poly_reg_model.fit(poly_features, self.dataframe[f"{self.fid}_mean"])

        return poly_reg_model.predict(poly_features)

    def apply_linear(self, column="mean"):
        model = LinearRegression(fit_intercept=True)
        model.fit(self.dataframe[["interval_diff"]], self.dataframe[column])

        return model.predict(
            self.linear_dataframe.loc[
                self.linear_dataframe.index.intersection(self.dataframe.index)
            ]
        )

    def apply_spline(self):
        # apply spline with weights: data point mean / global mean
        # where datapoint mean == global mean, weight equals 1 which is the default method weight
        # where datapoint mean > global mean, weight > 1 and indicates higher significance
        # where datapoint mean < global mean, weight < 1 and indicates lower significance
        tck = splrep(
            np.arange(len(self.dataframe)),  # numerical index on dataframe.index
            self.dataframe[f"{self.fid}_mean"].to_numpy(),  # variable to interpolate
            w=(
                self.dataframe[f"{self.fid}_mean"]
                / self.linear_dataframe[f"{self.fid}_mean"]
            ).to_numpy(),  # weights
            s=0.25 * len(self.dataframe),
        )

        return BSpline(*tck)(np.arange(len(self.dataframe)))

    def linear_regression(self):
        for col in [f"{self.fid}_mean", f"{self.fid}_std"]:
            predictions = self.apply_linear(column=col)
            self.regression_dataframe[col] = predictions

        # self.save_regression(mode="linear")
        self.linear_dataframe = self.regression_dataframe.copy()

        self.regression_dataframe.drop(f"{self.fid}_mean", axis=1)
        self.regression_dataframe.drop(f"{self.fid}_std", axis=1)


def mutliple_orbits_raw_range(fid="total", orbit_collection=None):
    asc_df = pd.DataFrame()
    des_df = pd.DataFrame()

    for orbit in orbit_collection.orbits:
        if orbit == "asc":
            asc_df["asc_mean"] = orbit_collection.asc_subsets.dataframe.loc[:, f"{fid}_mean"]
            asc_df["asc_std"] = orbit_collection.asc_subsets.dataframe.loc[:, f"{fid}_std"]

        else:
            des_df["des_mean"] = orbit_collection.des_subsets.dataframe.loc[:, f"{fid}_mean"]
            des_df["des_std"] = orbit_collection.des_subsets.dataframe.loc[:, f"{fid}_std"]

    if len(orbit_collection.orbits) == 2:
        subsets_df = pd.concat([asc_df, des_df], axis=1)
        subsets_df[f"{fid}_mean"] = subsets_df[["asc_mean", "des_mean"]].mean(axis=1)
        subsets_df[f"{fid}_std"] = subsets_df[["asc_std", "des_std"]].mean(axis=1)

    else:
        orbit = orbit_collection.orbits[0]

        if orbit == "asc":
            subsets_df = asc_df

        else:
            subsets_df = des_df

        subsets_df[f"{fid}_mean"] = subsets_df.loc[:, f"{orbit}_mean"]
        subsets_df[f"{fid}_std"] = subsets_df.loc[:, f"{orbit}_std"]

    return subsets_df


def get_monthly_keyword(monthly=False):
    if monthly:
        return "monthly_"

    else:
        return ""


def get_split_keyword(aoi_split=False):
    if aoi_split:
        return "split_aoi"

    else:
        return "single_aoi"


def get_last_month():
    current_date = datetime.now()
    last_month = datetime(current_date.year, current_date.month, 1) + relativedelta(
        days=-1
    )

    return datetime.strftime(last_month, "%Y-%m-%d")


def adapt_start_end_time(start=False, end=False, date=None):
    """
    Start date must have time part set to 00:00:00.
    End date must have time part set to 23:59:59.
    """

    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")

    if start:
        date = datetime.combine(date, time(hour=0, minute=0, second=0))

    if end:
        date = datetime.combine(date, time(hour=23, minute=59, second=59))

    return datetime.strftime(date, "%Y-%m-%dT%H:%M:%SZ")


def create_out_dir(base_dir=None, out_dir=None):
    if not base_dir.joinpath(out_dir).exists():
        base_dir.joinpath(out_dir).mkdir(parents=True)


def convert_dataframe_tz(var=None):
    if isinstance(var, pd.DatetimeIndex) or isinstance(var, pd.Timestamp):
        if var.tzinfo is None:
            var = var.tz_localize("UTC")

        else:
            var = var.tz_convert("UTC")

    return var


def load_yaml(yaml_path):
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def get_logger(name, out_dir=None, level=logging.INFO, also_log_to_stdout=True):
    log_file = Path(out_dir).joinpath("log_sat4ec.json")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    string_format = """{
        "Asctime":         "asctime",
        "Levelname":       "levelname",
        "Pathname":        "pathname",
        "Message":         "message"
    }"""

    formatter = JsonFormatter(string_format)

    # create a file handler
    if not Path(out_dir).exists():
        Path(out_dir).mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_file)
    handler.setLevel(level)

    # create a logging format
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    if also_log_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(level)
        logger.addHandler(stdout_handler)

    return logger
