"""Handle sub AOIs."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from anomaly_detection import Anomalies
    from sentinelhub import Geometry

import pandas as pd
from aoi_check import Feature
from system.helper_functions import (
    Regression,
    create_out_dir,
    get_monthly_keyword,
    get_split_keyword,
    remove_dataframe_nan_rows,
)

ORBIT_COUNT = 2


class SubsetCollection:
    """Encapsulate methods to handle sub AOIS."""

    def __init__(
        self: SubsetCollection,
        out_dir: Path | None = None,
        monthly: bool = False,
        orbit: str = "asc",
        pol: str = "VH",
        overwrite_raw: bool = False,
        aoi_split: bool = False,
    ) -> None:
        """Initialize SubsetCollection class."""
        self.dataframe = None
        self.archive_dataframe = None  # dataframe that might has been saved before, for comparison with new data
        self.regression_dataframe = None
        self.linear_dataframe = None  # dataframe for default linear regression
        self.out_dir = out_dir
        self.monthly = monthly
        self.orbit = orbit
        self.pol = pol
        self.features = []
        self.geometries = []
        self.overwrite_raw = overwrite_raw
        self.aoi_split = aoi_split

        self._get_outfile()

    def _get_outfile(self: SubsetCollection) -> None:
        """Define output file names."""
        self.monthly_raw_file = self.out_dir.joinpath(
            "raw",
            f"indicator_1_rawdata_{get_split_keyword(aoi_split=self.aoi_split)}_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.daily_raw_file = self.out_dir.joinpath(
            "raw",
            f"indicator_1_rawdata_{get_split_keyword(aoi_split=self.aoi_split)}_{self.orbit}_{self.pol}.csv",
        )

    def check_index(self: SubsetCollection) -> None:
        """Check for valid index."""
        if isinstance(self.dataframe.index, pd.Index):
            self.dataframe.index = pd.to_datetime(self.dataframe.index)

    def add_subset(self: SubsetCollection, df: pd.DataFrame) -> None:
        """Add sub AOI."""
        self.dataframe = pd.concat([self.dataframe, df], axis=1).sort_index()  # merge arrays

        self.check_index()

    def add_feature(self: SubsetCollection, feature: Feature) -> None:
        """Add feature."""
        self.features.append(feature)

    def add_geometry(self: SubsetCollection, geometry: Geometry) -> None:
        """Add geometries."""
        self.geometries.append(geometry)

    def add_regression_subset(self: SubsetCollection, df: pd.DataFrame) -> None:
        """Add regressed data."""
        self.regression_dataframe = pd.concat([self.regression_dataframe, df], axis=1).sort_index()  # merge arrays

    def add_linear_subset(self: SubsetCollection, df: pd.DataFrame) -> None:
        """Add linear data."""
        self.linear_dataframe = pd.concat([self.linear_dataframe, df], axis=1).sort_index()  # merge arrays

    def remove_dataframe_items(self: SubsetCollection) -> None:
        """Remove NaN rows from dataframe."""
        if "interval_to" in self.dataframe.columns:
            self.dataframe.drop("interval_to", axis=1, inplace=True)

        self.dataframe = remove_dataframe_nan_rows(df=self.dataframe)

    def aggregate_columns(self: SubsetCollection) -> None:
        """Aggregate dataframe AOIs into a single AOI calles 'total'."""
        for col in ["mean", "std", "min", "max"]:
            self.dataframe[f"total_{col}"] = self.dataframe.loc[:, self.dataframe.columns.str.endswith(col)].mean(
                axis=1
            )

        for col in ["sample_count", "nodata_count"]:
            self.dataframe[f"total_{col}"] = self.dataframe.loc[:, self.dataframe.columns.str.endswith(col)].sum(axis=1)

        total_feature = Feature()
        total_feature.fid = "total"
        self.add_feature(feature=total_feature)

    def drop_columns(self: SubsetCollection) -> None:
        """Drop dataframe columns."""
        self.dataframe = self.dataframe.T.drop_duplicates().T
        self.regression_dataframe = self.regression_dataframe.T.drop_duplicates().T
        self.linear_dataframe = self.linear_dataframe.T.drop_duplicates().T

        if "interval_from" in self.regression_dataframe.columns:
            self.regression_dataframe.drop("interval_from", axis=1, inplace=True)

        if "interval_from" in self.linear_dataframe.columns:
            self.linear_dataframe.drop("interval_from", axis=1, inplace=True)

    def monthly_aggregate(self: SubsetCollection) -> None:
        """Perform monthly aggregation of semi-daily data."""
        self.dataframe["year"] = self.dataframe.index.year
        self.dataframe["month"] = self.dataframe.index.month
        self.dataframe = self.dataframe.groupby(by=["year", "month"], as_index=False).mean(numeric_only=True)
        self.dataframe["interval_from"] = pd.to_datetime(self.dataframe[["year", "month"]].assign(DAY=15))
        self.dataframe = self.dataframe.set_index("interval_from")
        self.dataframe.drop(["year", "month"], axis=1, inplace=True)

    def check_existing_raw(self: SubsetCollection) -> None:
        """Check for existing archive data."""
        if not self.overwrite_raw and self.daily_raw_file.exists():
            self.archive_dataframe = pd.read_csv(self.daily_raw_file, decimal=".")
            self.archive_dataframe["interval_from"] = pd.to_datetime(self.archive_dataframe["interval_from"])
            self.archive_dataframe = self.archive_dataframe.set_index("interval_from")
            self.correct_archive_datatypes()

    def correct_archive_datatypes(self: SubsetCollection) -> None:
        """Convert archive dataframe data types."""
        # read from CSV introduces object datatype instead of float
        for col in self.archive_dataframe.columns[self.archive_dataframe.columns.str.startswith("interval_to")]:
            self.archive_dataframe[col] = self.archive_dataframe[col].astype("string")

        object_cols = list(self.archive_dataframe.select_dtypes(include="object"))

        try:
            self.archive_dataframe[object_cols] = self.archive_dataframe[object_cols].astype("float32")

        except ValueError:
            for col in object_cols:
                self.archive_dataframe[col] = self.archive_dataframe[col].str.replace(",", ".").astype("float32")

    def save_daily_raw(self: SubsetCollection) -> None:
        """Save semi-daily dataframe to file."""
        self.dataframe.to_csv(self.daily_raw_file, decimal=".")

    def save_monthly_raw(self: SubsetCollection) -> None:
        """Save monthly aggregated fataframe to file."""
        self.dataframe.to_csv(self.monthly_raw_file, decimal=".")

    def apply_regression(self: SubsetCollection, mode: str = "spline") -> None:
        """Apply regression."""
        for feature in self.features:
            regression = Regression(
                fid=feature.fid,
                monthly=self.monthly,
                df=self.dataframe.loc[:, self.dataframe.columns.str.startswith(f"{feature.fid}_")],
                mode=mode,
            )

            regression.apply_feature_regression()
            self.add_regression_subset(df=regression.regression_dataframe)
            self.add_linear_subset(df=regression.linear_dataframe)

        self.drop_columns()

    def save_regression(self: SubsetCollection, mode: str = "spline") -> None:
        """Save regression dataframes to file."""
        if not self.monthly:  # regression is not saved for monthly data
            reg_out_file = self.out_dir.joinpath(
                "regression",
                f"{mode}",
                f"indicator_1_{get_split_keyword(aoi_split=self.aoi_split)}_{mode}_{self.orbit}_{self.pol}.csv",
            )
            create_out_dir(base_dir=reg_out_file.parent)
            self.regression_dataframe.to_csv(reg_out_file, decimal=".")

        lin_out_file = self.out_dir.joinpath(
            "regression",
            "linear"
            f"indicator_1_linear_{get_split_keyword(aoi_split=self.aoi_split)}_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        create_out_dir(base_dir=lin_out_file.parent)
        self.linear_dataframe.to_csv(lin_out_file, decimal=".")


class OrbitCollection:
    """Encapsulate data attachment methods per orbit."""

    def __init__(self: OrbitCollection, orbit: str = "asc", monthly: bool = False) -> None:
        """Initialize OrbitCollection class."""
        self.orbit = orbit
        self.monthly = monthly
        self.asc_anomalies = None
        self.des_anomalies = None
        self.asc_subsets = None
        self.des_subsets = None

        self._get_orbits()

    def _get_orbits(self: OrbitCollection) -> None:
        if self.orbit == "both":
            self.orbits = ["asc", "des"]

        else:
            self.orbits = [self.orbit]

    def add_subsets(self: OrbitCollection, subsets: SubsetCollection, orbit: str = "asc") -> None:
        """Define subset collection per orbit."""
        if orbit == "asc":
            self.asc_subsets = subsets

        elif orbit == "des":
            self.des_subsets = subsets

        else:
            raise AttributeError(f"The provided orbit {orbit} is not supported.")

    def add_anomalies(self: OrbitCollection, anomalies: Anomalies, orbit: str = "asc") -> None:
        """Attach anomaly data to orbit collection."""
        if orbit == "asc":
            self.asc_anomalies = anomalies

        elif orbit == "des":
            self.des_anomalies = anomalies

        else:
            raise AttributeError(f"The provided orbit {orbit} is not supported.")

    def get_data(
        self: OrbitCollection,
    ) -> Generator[[SubsetCollection, Anomalies, str, bool], list]:
        """Retrieve data fpr specific orbit."""
        for orbit in self.orbits:
            if orbit == "asc":
                yield self.asc_subsets, self.asc_anomalies, orbit, True  # True for left axis

            elif orbit == "des" and len(self.orbits) == ORBIT_COUNT:
                yield self.des_subsets, self.des_anomalies, orbit, False  # False, to plot DES on right axis

            else:
                yield self.des_subsets, self.des_anomalies, orbit, True  # True for left axis
