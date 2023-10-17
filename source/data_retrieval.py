import pandas as pd
import numpy as np
from scipy.interpolate import splrep, BSpline
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from system.helper_functions import get_monthly_keyword, create_out_dir
from system.authentication import Config
from aoi_check import Feature
from sentinelhub import (
    Geometry,
    CRS,
    bbox_to_dimensions,
    DataCollection,
    SentinelHubStatistical,
    parse_time,
)


class Regression:
    def __init__(self, fid=None, df=None, mode="spline"):
        self.mode = mode
        self.fid = fid
        self.dataframe = df
        self.linear_dataframe = None
        self.regression_dataframe = None

    def apply_feature_regression(self):
        self.prepare_regression()
        self.linear_regression()

        if self.mode == "rolling":
            self.regression_dataframe[f"{self.fid}_mean"] = self.apply_pandas_rolling()

        elif self.mode == "spline":
            self.regression_dataframe[f"{self.fid}_mean"] = self.apply_spline()

        elif self.mode == "poly":
            self.regression_dataframe[f"{self.fid}_mean"] = self.apply_polynomial()

        else:
            raise ValueError(f"The provided mode {self.mode} is not supported. Please choose from [rolling, spline, poly].")

        self.dataframe = self.dataframe.drop("interval_diff", axis=1, inplace=False)

    def apply_pandas_rolling(self):
        return self.dataframe[f"{self.fid}_mean"].rolling(
            5,
            center=True,
            closed="both",
            win_type="cosine",
        ).mean(5)  # cosine

    def prepare_regression(self):
        time_diff = (self.dataframe.index[0] - self.dataframe.index).days * (-1)  # date difference
        date_range = pd.date_range(freq="1D", start=self.dataframe.index[0], end=self.dataframe.index[-1])

        self.regression_dataframe = pd.DataFrame({"interval_from": self.dataframe.index}, index=self.dataframe.index)
        self.dataframe.loc[:, "interval_diff"] = time_diff  # temporary
        self.linear_dataframe = pd.DataFrame({"interval_diff": np.arange(time_diff[-1]+1)}, index=date_range)

    def apply_polynomial(self):
        poly_reg_model = LinearRegression()
        poly = PolynomialFeatures(degree=5, include_bias=False)
        poly_features = poly.fit_transform(self.dataframe["interval_diff"].values.reshape(-1, 1))
        poly_reg_model.fit(poly_features, self.dataframe[f"{self.fid}_mean"])

        return poly_reg_model.predict(poly_features)

    def apply_linear(self, column="mean"):
        model = LinearRegression(fit_intercept=True)
        model.fit(self.dataframe[["interval_diff"]], self.dataframe[column])

        return model.predict(self.linear_dataframe.loc[self.linear_dataframe.index.intersection(self.dataframe.index)])

    def apply_spline(self):
        # apply spline with weights: data point mean / global mean
        # where datapoint mean == global mean, weight equals 1 which is the default method weight
        # where datapoint mean > global mean, weight > 1 and indicates higher significance
        # where datapoint mean < global mean, weight < 1 and indicates lower significance
        tck = splrep(
            np.arange(len(self.dataframe)),  # numerical index on dataframe.index
            self.dataframe[f"{self.fid}_mean"].to_numpy(),  # variable to interpolate
            w=(self.dataframe[f"{self.fid}_mean"] / self.dataframe[f"{self.fid}_mean"].mean()).to_numpy(),  # weights
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


class SubsetCollection:
    def __init__(self, out_dir=None, monthly=False, orbit="asc", pol="VH"):
        self.dataframe = None
        self.regression_dataframe = None
        self.linear_dataframe = None  # dataframe for default linear regression
        self.out_dir = out_dir
        self.monthly = monthly
        self.orbit = orbit
        self.pol = pol
        self.features = []

    def add_subset(self, df=None):
        self.dataframe = pd.concat([self.dataframe, df], axis=1).sort_index()  # merge arrays

    def add_feature(self, feature=None):
        self.features.append(feature)

    def add_regression_subset(self, df=None):
        self.regression_dataframe = pd.concat([self.regression_dataframe, df], axis=1).sort_index()  # merge arrays

    def add_linear_subset(self, df=None):
        self.linear_dataframe = pd.concat([self.linear_dataframe, df], axis=1).sort_index()  # merge arrays

    def aggregate_columns(self):
        for col in ["mean", "std", "min", "max"]:
            self.dataframe[f"total_{col}"] = self.dataframe.loc[:, self.dataframe.columns.str.endswith(col)].mean(
                axis=1)

        for col in ["sample_count", "nodata_count"]:
            self.dataframe[f"total_{col}"] = self.dataframe.loc[:, self.dataframe.columns.str.endswith(col)].sum(
                axis=1)

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
        self.dataframe = self.dataframe.groupby(by=["year", "month"], as_index=False).mean()
        self.dataframe["interval_from"] = pd.to_datetime(self.dataframe[["year", "month"]].assign(DAY=15))
        self.dataframe = self.dataframe.set_index("interval_from")
        self.dataframe.drop(["year", "month"], axis=1, inplace=True)

    def save_raw(self):
        out_file = self.out_dir.joinpath(
            "raw",
            f"indicator_1_rawdata_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.dataframe.to_csv(out_file)

    def apply_regression(self, mode="spline"):
        for feature in self.features:
            regression = Regression(
                fid=feature.fid,
                df=self.dataframe.loc[:, self.dataframe.columns.str.startswith(f"{feature.fid}_")],
                mode=mode
            )

            regression.apply_feature_regression()
            self.add_regression_subset(df=regression.regression_dataframe)
            self.add_linear_subset(df=regression.linear_dataframe)

        self.drop_columns()

    def save_regression(self, mode="spline"):
        reg_out_file = self.out_dir.joinpath(
            "regression",
            f"indicator_1_{mode}_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.regression_dataframe.to_csv(reg_out_file)

        lin_out_file = self.out_dir.joinpath(
            "regression",
            f"indicator_1_linear_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.linear_dataframe.to_csv(lin_out_file)


class IndicatorData(Config):
    def __init__(
        self,
        aoi=None,
        fid=None,
        out_dir=None,
        start_date=None,
        end_date=None,
        crs=CRS.WGS84,
        resolution=5,
        orbit="asc",
        pol="VH",
        monthly=False
    ):
        super().__init__()
        self.aoi = aoi
        self.fid = fid
        self.crs = crs
        self.geometry = None
        self.orbit = orbit
        self.interval = (f"{start_date}T00:00:00Z", f"{end_date}T23:59:59Z")
        self.size = None
        self.resolution = resolution
        self.aggregation = None
        self.eval_script = None
        self.request = None
        self.stats = None
        self.dataframe = None
        self.regression_dataframe = None
        self.linear_dataframe = None  # dataframe for default linear regression
        self.pol = pol
        self.out_dir = out_dir
        self.thresholds = {"min": None, "max": None}
        self.outliers = None
        self.monthly = monthly

        self._get_geometry()
        self._get_dimensions()
        self._get_collection()
        self._create_out_dirs()
        self._get_column_rename_map()

    def _get_column_rename_map(self):
        self.columns_map = {
            "B0_min": "min",
            "B0_max": "max",
            "B0_mean": "mean",
            "B0_stDev": "std",
            "B0_sampleCount": "sample_count",
            "B0_noDataCount": "nodata_count",
        }

    def _create_out_dirs(self):
        for out in ["plot", "raw", "scenes", "anomalies", "regression"]:
            create_out_dir(base_dir=self.out_dir, out_dir=out)

    def _get_geometry(self):
        self.geometry = Geometry(self.aoi, crs=self.crs)  # shapely polygon with CRS

    def _get_dimensions(self):
        """
        Get width and height of polygon in pixels. CRS is the respective UTM, automatically derived.
        """
        self.size = bbox_to_dimensions(self.geometry.bbox, self.resolution)

    def _get_collection(self):
        if self.orbit == "asc":
            self.collection = DataCollection.SENTINEL1_IW_ASC

        else:
            self.collection = DataCollection.SENTINEL1_IW_DES

    def _correct_datatypes(self):
        # Select columns with float64 dtype
        float64_cols = list(self.dataframe.select_dtypes(include="float64"))
        self.dataframe[float64_cols] = self.dataframe[float64_cols].astype("float32")

    def get_request_grd(self):
        # evalscript (unit: dB)
        self.eval_script = """
        //VERSION=3
        function setup() {{
          return {{
            input: [{{
              bands: ["{polarization}", "dataMask"]
            }}],
            output: [
              {{
                id: "default",
                bands: 1
              }},
              {{
                id: "dataMask",
                bands: 1
              }}]
          }};
        }}

        function evaluatePixel(samples) {{
            return {{
                default: [toDb(samples.{polarization})],
                dataMask: [samples.dataMask],
            }};
        }}

        function toDb(sigma_linear) {{
           if(sigma_linear === 0) return 0;
           return (10 * Math.log10(sigma_linear))  //equation from GEE Sentinel-1 Prepocessing
        }}
        """

        self.eval_script = self.eval_script.format(
            polarization="".join(self.pol),
        )

        # statistical API request (unit: dB)
        self.request = SentinelHubStatistical(
            aggregation=SentinelHubStatistical.aggregation(
                evalscript=self.eval_script,
                time_interval=self.interval,
                aggregation_interval="P1D",  # interval set to 1 day or 30 day increment
                size=self.size,
            ),
            input_data=[
                SentinelHubStatistical.input_data(
                    self.collection,
                    other_args={
                        "dataFilter": {
                            "mosaickingOrder": "mostRecent",
                            "resolution": "HIGH",
                        },
                        "processing": {
                            "orthorectify": "True",
                            "demInstance": "COPERNICUS",
                            # "radiometricTerrainOversampling": 2,  # terrain correction
                            "backCoeff": "SIGMA0_ELLIPSOID",
                            "speckleFilter": {
                                "type": "LEE",  # possibleValues:["NONE","LEE"]
                                "windowSizeX": 3,
                                "windowSizeY": 3,
                            },
                        },
                    },
                )
            ],
            geometry=self.geometry,
            config=self.config,
        )

    def get_data(self):
        self.stats = self.request.get_data()[0]

    @staticmethod
    def get_band_stats(bands):
        for key, values in bands.items():
            band = Band(name=key, stats=values["stats"])
            band.check_valid()
            yield band

    def stats_to_df(self):
        target = []

        for _item in self.stats["data"]:
            df_entry = {
                "interval_from": pd.to_datetime(parse_time(_item["interval"]["from"])),
                "interval_to": pd.to_datetime(parse_time(_item["interval"]["to"])),
            }

            bands = Bands()

            for band in self.get_band_stats(_item["outputs"]["default"]["bands"]):
                if not band.valid:
                    continue

                for stat_name, stat_value in band.stats.items():
                    df_entry[f"{band.name}_{stat_name}"] = stat_value

                bands.bands.append(band)

            if bands.check_valid():
                target.append(df_entry)

        self.dataframe = pd.DataFrame(target)
        self._correct_datatypes()
        self.dataframe = self.dataframe.set_index("interval_from")

        for col in self.columns_map:
            self.rename_column(src=col, dst=self.columns_map[col])

    def rename_column(self, src=None, dst=None):
        self.dataframe.rename(columns={f"{src}": f"{self.fid}_{dst}"}, inplace=True)


class Band:
    def __init__(self, name=None, stats=None):
        self.name = name
        self.valid = False
        self.stats = stats

    def check_valid(self):
        if self.stats["sampleCount"] > self.stats["noDataCount"]:
            self.valid = True


class Bands:
    def __init__(self):
        self.bands = []

    def check_valid(self):
        return any([band.valid for band in self.bands])
