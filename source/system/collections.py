import pandas as pd
from aoi_check import Feature
from system.helper_functions import get_monthly_keyword, get_split_keyword, create_out_dir, remove_dataframe_nan_rows
from system.helper_functions import Regression


class SubsetCollection:
    def __init__(self, out_dir=None, monthly=False, orbit="asc", pol="VH", overwrite_raw=False, aoi_split=False):
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

    def _get_outfile(self):
        self.monthly_raw_file = self.out_dir.joinpath(
            "raw",
            f"indicator_1_rawdata_{get_split_keyword(aoi_split=self.aoi_split)}_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.daily_raw_file = self.out_dir.joinpath(
            "raw",
            f"indicator_1_rawdata_{get_split_keyword(aoi_split=self.aoi_split)}_{self.orbit}_{self.pol}.csv",
        )

    def check_index(self):
        if isinstance(self.dataframe.index, pd.Index):
            self.dataframe.index = pd.to_datetime(self.dataframe.index)
        
    def add_subset(self, df=None):
        self.dataframe = pd.concat(
            [self.dataframe, df], axis=1
        ).sort_index()  # merge arrays
        
        self.check_index()

    def add_feature(self, feature=None):
        self.features.append(feature)

    def add_geometry(self, geometry=None):
        self.geometries.append(geometry)

    def add_regression_subset(self, df=None):
        self.regression_dataframe = pd.concat(
            [self.regression_dataframe, df], axis=1
        ).sort_index()  # merge arrays

    def add_linear_subset(self, df=None):
        self.linear_dataframe = pd.concat(
            [self.linear_dataframe, df], axis=1
        ).sort_index()  # merge arrays

    def remove_nan_rows(self):
        self.dataframe = remove_dataframe_nan_rows(df=self.dataframe)

    def aggregate_columns(self):
        for col in ["mean", "std", "min", "max"]:
            self.dataframe[f"total_{col}"] = self.dataframe.loc[
                :, self.dataframe.columns.str.endswith(col)
            ].mean(axis=1)

        for col in ["sample_count", "nodata_count"]:
            self.dataframe[f"total_{col}"] = self.dataframe.loc[
                :, self.dataframe.columns.str.endswith(col)
            ].sum(axis=1)

        total_feature = Feature()
        total_feature.fid = "total"
        self.add_feature(feature=total_feature)

    def drop_columns(self):
        self.dataframe = self.dataframe.T.drop_duplicates().T
        self.regression_dataframe = self.regression_dataframe.T.drop_duplicates().T
        self.linear_dataframe = self.linear_dataframe.T.drop_duplicates().T

        if "interval_from" in self.regression_dataframe.columns:
            self.regression_dataframe.drop("interval_from", axis=1, inplace=True)

        if "interval_from" in self.linear_dataframe.columns:
            self.linear_dataframe.drop("interval_from", axis=1, inplace=True)

    def monthly_aggregate(self):
        self.dataframe["year"] = self.dataframe.index.year
        self.dataframe["month"] = self.dataframe.index.month
        self.dataframe = self.dataframe.groupby(
            by=["year", "month"], as_index=False
        ).mean(numeric_only=True)
        self.dataframe["interval_from"] = pd.to_datetime(
            self.dataframe[["year", "month"]].assign(DAY=15)
        )
        self.dataframe = self.dataframe.set_index("interval_from")
        self.dataframe.drop(["year", "month"], axis=1, inplace=True)

    def check_existing_raw(self):
        if not self.overwrite_raw:
            if self.daily_raw_file.exists():
                self.archive_dataframe = pd.read_csv(self.daily_raw_file, decimal=".")
                self.archive_dataframe["interval_from"] = pd.to_datetime(
                    self.archive_dataframe["interval_from"]
                )
                self.archive_dataframe = self.archive_dataframe.set_index("interval_from")

                self.correct_archive_datatypes()

    def correct_archive_datatypes(self):
        # correct datatypes
        # read from CSV introduces object datatype instead of float
        for col in self.archive_dataframe.columns[self.archive_dataframe.columns.str.startswith("interval_to")]:
            self.archive_dataframe[col] = self.archive_dataframe[col].astype("string")

        object_cols = list(self.archive_dataframe.select_dtypes(include="object"))

        try:
            self.archive_dataframe[object_cols] = self.archive_dataframe[
                object_cols
            ].astype("float32")

        except ValueError:
            for col in object_cols:
                self.archive_dataframe[col] = (
                    self.archive_dataframe[col].str.replace(",", ".").astype("float32")
                )

    def save_daily_raw(self):
        self.dataframe.to_csv(self.daily_raw_file, decimal=".")

    def save_monthly_raw(self):
        self.dataframe.to_csv(self.monthly_raw_file, decimal=".")

    def apply_regression(self, mode="spline"):
        for feature in self.features:
            regression = Regression(
                fid=feature.fid,
                monthly=self.monthly,
                df=self.dataframe.loc[
                    :, self.dataframe.columns.str.startswith(f"{feature.fid}_")
                ],
                mode=mode,
            )

            regression.apply_feature_regression()
            self.add_regression_subset(df=regression.regression_dataframe)
            self.add_linear_subset(df=regression.linear_dataframe)

        self.drop_columns()

    def save_regression(self, mode="spline"):
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
    def __init__(self, orbit="asc", monthly=False):
        self.orbit = orbit
        self.monthly = monthly
        self.asc_anomalies = None
        self.des_anomalies = None
        self.asc_subsets = None
        self.des_subsets = None

        self._get_orbits()

    def _get_orbits(self):
        if self.orbit == "both":
            self.orbits = ["asc", "des"]

        else:
            self.orbits = [self.orbit]

    def add_subsets(self, subsets=None, orbit="asc"):
        if orbit == "asc":
            self.asc_subsets = subsets

        elif orbit == "des":
            self.des_subsets = subsets

        else:
            raise AttributeError(f"The provided orbit {orbit} is not supported.")

    def add_anomalies(self, anomalies=None, orbit="asc"):
        if orbit == "asc":
            self.asc_anomalies = anomalies

        elif orbit == "des":
            self.des_anomalies = anomalies

        else:
            raise AttributeError(f"The provided orbit {orbit} is not supported.")

    def get_data(self):
        for orbit in self.orbits:
            if orbit == "asc":
                yield self.asc_subsets, self.asc_anomalies, orbit, True  # True for left axis

            else:
                if len(self.orbits) == 2:
                    yield self.des_subsets, self.des_anomalies, orbit, False  # False, to plot DES on right axis

                else:
                    yield self.des_subsets, self.des_anomalies, orbit, True  # True for left axis
