import pandas as pd
import numpy as np
import datetime
from scipy.interpolate import splrep, BSpline, UnivariateSpline, InterpolatedUnivariateSpline
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, SplineTransformer
from system.helper_functions import get_monthly_keyword
from system.authentication import Config
from sentinelhub import (
    Geometry,
    CRS,
    bbox_to_dimensions,
    DataCollection,
    SentinelHubStatistical,
    parse_time,
)


class IndicatorData(Config):
    def __init__(
        self,
        aoi=None,
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
        self.spline_dataframe = None
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
        for out in ["plot", "raw", "scenes", "anomalies", "spline"]:
            if not self.out_dir.joinpath(out).exists():
                self.out_dir.joinpath(out).mkdir(parents=True)

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

    def monthly_aggregate(self):
        self.dataframe["year"] = self.dataframe.index.year
        self.dataframe["month"] = self.dataframe.index.month
        self.dataframe = self.dataframe.groupby(by=["year", "month"], as_index=False).mean()
        self.dataframe["interval_from"] = pd.to_datetime(self.dataframe[["year", "month"]].assign(DAY=15))
        self.dataframe = self.dataframe.set_index("interval_from")
        self.dataframe.drop(["year", "month"], axis=1, inplace=True)

    def rename_column(self, src=None, dst=None):
        self.dataframe.rename(columns={f"{src}": f"{dst}"}, inplace=True)

    def apply_pandas_rolling(self, x_values):
        return self.dataframe["mean"].rolling(
            5,
            center=True,
            closed="both",
            win_type="cosine",
        ).mean(5)  # cosine

    def prepare_regression(self, mode="linear"):
        if mode == "linear":
            date_range = pd.date_range(freq="1D", start=self.dataframe.index[0], end=self.dataframe.index[-1])

        elif mode == "poly":
            date_range = self.dataframe.index

        else:
            raise ValueError(f"The provided mode {mode} is not supported. Please choose from [linear, poly].")

        self.spline_dataframe = pd.DataFrame({"interval_from": date_range}, index=date_range)

        time_diff = (self.dataframe.index[0] - self.dataframe.index).days * (-1)  # date difference
        self.dataframe["interval_diff"] = time_diff

        return pd.DataFrame({"interval_diff": np.arange(time_diff[-1]+1)})

    def apply_polynomial(self, x_values):
        poly_reg_model = LinearRegression()
        poly = PolynomialFeatures(degree=5, include_bias=False)
        poly_features = poly.fit_transform(self.dataframe["interval_diff"].values.reshape(-1, 1))
        poly_reg_model.fit(poly_features, self.dataframe["mean"])

        return poly_reg_model.predict(poly_features)

    def apply_linear(self, x_values):
        model = LinearRegression(fit_intercept=True)
        model.fit(self.dataframe[["interval_diff"]], self.dataframe["mean"])

        return model.predict(x_values)

    def apply_spline(self, x_values):
        # apply spline with weights: data point mean / global mean
        # where datapoint mean == global mean, weight equals 1 which is the default method weight
        # where datapoint mean > global mean, weight > 1 and indicates higher significance
        # where datapoint mean < global mean, weight < 1 and indicates lower significance
        tck = splrep(
            np.arange(len(self.dataframe)),  # numerical index on dataframe.index
            self.dataframe["mean"].to_numpy(),  # variable to interpolate
            w=(self.dataframe["mean"] / self.dataframe["mean"].mean()).to_numpy(),  # weights
            s=0.25 * len(self.dataframe),
        )

        return BSpline(*tck)(np.arange(len(self.dataframe)))

    def apply_regression(self, mode="rolling"):
        if mode == "rolling":
            predictions = self.apply_pandas_rolling(self.prepare_regression())

        elif mode == "spline":
            predictions = self.apply_spline(self.prepare_regression(mode="poly"))

        elif mode == "linear":
            predictions = self.apply_linear(self.prepare_regression(mode="linear"))

        elif mode == "poly":
            predictions = self.apply_polynomial(self.prepare_regression(mode="poly"))

        else:
            raise ValueError(f"The provided mode {mode} is not supported. Please choose from [rolling, spline, linear, poly].")

        self.spline_dataframe["mean"] = predictions
        self.dataframe.drop("interval_diff", axis=1)

    def save_spline(self):
        out_file = self.out_dir.joinpath(
            "spline",
            f"indicator_1_splinedata_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.spline_dataframe.to_csv(out_file)

    def save_raw(self):
        out_file = self.out_dir.joinpath(
            "raw",
            f"indicator_1_rawdata_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.dataframe.to_csv(out_file)


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
