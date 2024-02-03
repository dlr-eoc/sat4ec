"""Compute regression functions on raw data."""
import numpy as np
import pandas as pd
from scipy.interpolate import BSpline, splrep
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


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
