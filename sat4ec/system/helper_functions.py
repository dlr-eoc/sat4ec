"""Perform linear and non-linear regression on the raw data."""
from datetime import datetime, time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from dateutil.relativedelta import relativedelta
from scipy.interpolate import BSpline, splrep
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from system.subset_collections import OrbitCollection as Orbits

ORBIT_COUNT = 2


class Regression:
    """Perform linear and non-linear regression on the raw data."""

    def __init__(self: "Regression", fid: str, df: pd.DataFrame, mode: str = "spline", monthly: bool = False) -> None:
        """Initialize Regression class."""
        self.mode = mode
        self.monthly = monthly
        self.fid = fid
        self.dataframe = df.copy(deep=True)
        self.regression_dataframe = None
        self.linear_dataframe = None

    def apply_feature_regression(self: "Regression") -> None:
        """Encapsulate regression calls."""
        self.prepare_regression()
        self.linear_regression()

        if self.monthly:
            self.regression_dataframe[f"{self.fid}_mean"] = self.dataframe[f"{self.fid}_mean"]

        elif not self.monthly and self.mode == "rolling":
            self.regression_dataframe[f"{self.fid}_mean"] = self.apply_pandas_rolling()

        elif not self.monthly and self.mode == "spline":
            self.regression_dataframe[f"{self.fid}_mean"] = self.apply_spline()

        elif not self.monthly and self.mode == "poly":
            self.regression_dataframe[f"{self.fid}_mean"] = self.apply_polynomial()

        else:
            raise ValueError(
                f"The provided mode {self.mode} is not supported. Please choose from [rolling, spline, poly]."
            )

        self.dataframe = self.dataframe.drop("interval_diff", axis=1, inplace=False)

    def apply_pandas_rolling(self: "Regression") -> pd.DataFrame:
        """Apply pandas rolling mean."""
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

    def prepare_regression(self: "Regression") -> None:
        """Prepare dataframes for regression."""
        time_diff = (self.dataframe.index[0] - self.dataframe.index).days * (-1)  # date difference
        date_range = pd.date_range(freq="1D", start=self.dataframe.index[0], end=self.dataframe.index[-1])

        self.regression_dataframe = pd.DataFrame({"interval_from": self.dataframe.index}, index=self.dataframe.index)
        self.dataframe.loc[:, "interval_diff"] = time_diff  # temporary
        self.linear_dataframe = pd.DataFrame({"interval_diff": np.arange(time_diff[-1] + 1)}, index=date_range)

    def apply_polynomial(self: "Regression") -> LinearRegression:
        """Apply polynomial regression."""
        poly_reg_model = LinearRegression()
        poly = PolynomialFeatures(degree=5, include_bias=False)
        poly_features = poly.fit_transform(self.dataframe["interval_diff"].values.reshape(-1, 1))
        poly_reg_model.fit(poly_features, self.dataframe[f"{self.fid}_mean"])

        return poly_reg_model.predict(poly_features)

    def apply_linear(self: "Regression", column: str = "mean") -> LinearRegression:
        """Fit linear regression model."""
        model = LinearRegression(fit_intercept=True)
        model.fit(self.dataframe[["interval_diff"]], self.dataframe[column])

        return model.predict(self.linear_dataframe.loc[self.linear_dataframe.index.intersection(self.dataframe.index)])

    def apply_spline(self: "Regression") -> np.array:
        """Apply spline regression."""
        # apply spline with weights: data point mean / global mean
        # where datapoint mean == global mean, weight equals 1 which is the default method weight
        # where datapoint mean > global mean, weight > 1 and indicates higher significance
        # where datapoint mean < global mean, weight < 1 and indicates lower significance
        tck = splrep(
            np.arange(len(self.dataframe)),  # numerical index on dataframe.index
            self.dataframe[f"{self.fid}_mean"].to_numpy(),  # variable to interpolate
            w=(self.dataframe[f"{self.fid}_mean"] / self.linear_dataframe[f"{self.fid}_mean"]).to_numpy(),  # weights
            s=0.25 * len(self.dataframe),
        )

        return BSpline(*tck)(np.arange(len(self.dataframe)))

    def linear_regression(self: "Regression") -> None:
        """Apply linear regression."""
        for col in [f"{self.fid}_mean", f"{self.fid}_std"]:
            predictions = self.apply_linear(column=col)
            self.regression_dataframe[col] = predictions

        self.linear_dataframe = self.regression_dataframe.copy()

        self.regression_dataframe.drop(f"{self.fid}_mean", axis=1)
        self.regression_dataframe.drop(f"{self.fid}_std", axis=1)


def mutliple_orbits_raw_range(orbit_collection: Orbits, fid: str = "total") -> pd.DataFrame:
    """Define the plottable range of the raw data."""
    asc_df = pd.DataFrame()
    des_df = pd.DataFrame()

    for orbit in orbit_collection.orbits:
        if orbit == "asc":
            asc_df["asc_mean"] = orbit_collection.asc_subsets.dataframe.loc[:, f"{fid}_mean"]
            asc_df["asc_std"] = orbit_collection.asc_subsets.dataframe.loc[:, f"{fid}_std"]

        else:
            des_df["des_mean"] = orbit_collection.des_subsets.dataframe.loc[:, f"{fid}_mean"]
            des_df["des_std"] = orbit_collection.des_subsets.dataframe.loc[:, f"{fid}_std"]

    if len(orbit_collection.orbits) == ORBIT_COUNT:
        subsets_df = pd.concat([asc_df, des_df], axis=1)
        subsets_df[f"{fid}_mean"] = subsets_df[["asc_mean", "des_mean"]].mean(axis=1)
        subsets_df[f"{fid}_std"] = subsets_df[["asc_std", "des_std"]].mean(axis=1)

    else:
        orbit = orbit_collection.orbits[0]

        subsets_df = asc_df if orbit == "asc" else des_df
        subsets_df[f"{fid}_mean"] = subsets_df.loc[:, f"{orbit}_mean"]
        subsets_df[f"{fid}_std"] = subsets_df.loc[:, f"{orbit}_std"]

    return subsets_df


def get_monthly_keyword(monthly: bool = False) -> str:
    """Determine if computing on semi-daily or monthly data."""
    if monthly:
        return "monthly_"

    return ""


def get_split_keyword(aoi_split: bool = False) -> str:
    """Determine if computing on split or aggregated AOIs."""
    if aoi_split:
        return "split_aoi"

    return "single_aoi"


def get_last_month() -> str:
    """Get last day of last month, e.g. 2024-01-31 if triggering in February 2024."""
    current_date = datetime.now()
    last_month = datetime(current_date.year, current_date.month, 1) + relativedelta(days=-1)

    return datetime.strftime(last_month, "%Y-%m-%d")


def adapt_start_end_time(date: str, start: bool = False, end: bool = False) -> str:
    """Attach hours, minutes and seconds to date.

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


def date_to_string(date: pd.Timestamp, remove_isoformat_t: bool = True) -> str:
    """Interval dates are in format YYYY-MM-DDT00:00:00Z. Convert to string with YYYY-MM-DD 00:00:00."""
    date = date.isoformat()

    if remove_isoformat_t:
        date = date.replace("T", " ")

    return date


def create_out_dir(base_dir: Path, out_dir: str = "") -> None:
    """Create output directory if not existing."""
    if not base_dir.joinpath(out_dir).exists():
        base_dir.joinpath(out_dir).mkdir(parents=True)


def convert_dataframe_tz(var: pd.DatetimeIndex | pd.Timestamp) -> pd.DatetimeIndex:
    """Set timezone info."""
    if isinstance(var, pd.DatetimeIndex | pd.Timestamp):
        var = var.tz_localize("UTC") if var.tzinfo is None else var.tz_convert("UTC")

    return var


def remove_dataframe_nan_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove NaN rows from dataframe."""
    return df[np.isfinite(df).all(1)]


def load_yaml(yaml_path: Path) -> dict:
    """Load a YAML file."""
    with Path.open(yaml_path, "r") as f:
        return yaml.safe_load(f)
