import pandas as pd
from system.helper_functions import get_last_month, create_out_dir, convert_dataframe_tz, adapt_start_end_time
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
        archive_data=None,
        aoi=None,
        fid=None,
        out_dir=None,
        start_date=None,
        end_date=None,
        crs=CRS.WGS84,
        resolution=5,
        orbit="asc",
        pol="VH",
        monthly=False,
    ):
        super().__init__()
        self.archive_data = archive_data
        self.aoi = aoi
        self.fid = fid
        self.crs = crs
        self.geometry = None
        self.orbit = orbit
        self.start_date = None
        self.end_date = None
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

        self.get_start_end_date(start=start_date, end=end_date)
        self._get_geometry()
        self._get_dimensions()
        self._get_collection()
        self._create_out_dirs()
        self._get_column_rename_map()

    def get_start_end_date(self, start=None, end=None):
        if start is None:
            self.start_date = "2014-05-01"

        else:
            self.start_date = start

        if end is None:
            self.end_date = get_last_month()

        else:
            self.end_date = end

        self._set_interval()

    def _set_interval(self):
        self.interval = (adapt_start_end_time(start=True, date=self.start_date), adapt_start_end_time(end=True, date=self.end_date))

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

    def check_dates(self, start=False, end=False):
        if start:
            # start_date is less than earliest archive date --> new data required for earlier dates
            if convert_dataframe_tz(var=pd.to_datetime(self.interval[0])) < convert_dataframe_tz(var=pd.to_datetime(self.archive_data.index[0])):
                self.end_date = self.archive_data.index[0].date()  # strip date what looks like 2021-01-03 00:00:00+00:00
                self._set_interval()

                return "past"

        if end:
            # end_date is greater than latest archive date --> new data required for future dates
            if convert_dataframe_tz(pd.to_datetime(self.interval[-1])) > convert_dataframe_tz(pd.to_datetime(self.archive_data.index[-1])):
                self.start_date = self.archive_data.index[-1].date()
                self._set_interval()

                return "future"

    def check_existing_data(self):
        if self.archive_data is not None:  # if some raw date has already been saved
            if f"{self.fid}_mean" in self.archive_data.columns:  # feature exists in archive data
                return True, True

            else:  # archive data present, but required feature not recorded
                return True, False

        else:  # no archive data
            return False, None

    def insert_past_dates(self):
        """
        Append archive dates to earlier dates,
        e.g. ["2019-11-11", "2019-12-12"] is first appended by ["2020-01-01", "2020-02-02"]
           date        val
        0  2019-11-11  11
        1  2019-12-12  12
        2  2020-01-01   1
        3  2020-02-02   2
        """

        self.dataframe = pd.concat([self.dataframe, self.archive_data], axis=0)

    def insert_future_dates(self):
        """
        Append recent dates to archive dates,
        e.g. ["2020-01-01", "2020-02-02"] is first appended by ["2020-03-03", "2020-04-04"]
           date        val
        0  2020-01-01  1
        1  2020-02-02  2
        2  2020-03-03  3
        3  2020-04-04  4
        """

        self.dataframe = pd.concat([self.archive_data, self.dataframe], axis=0)

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

        if not self.dataframe.empty:  # proceed if dataframe is not empty
            self.dataframe = self.dataframe.set_index("interval_from")

            for col in self.columns_map:
                self.rename_column(src=col, dst=self.columns_map[col])

    def rename_column(self, src=None, dst=None):
        self.dataframe.rename(columns={f"{src}": f"{self.fid}_{dst}"}, inplace=True)

    def remove_duplicate_date(self):
        self.dataframe = self.dataframe[~self.dataframe.index.duplicated()]


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
