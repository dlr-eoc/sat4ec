"""Encapsulate raw data retrieval."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from shapely.geometry import MultiPolygon, Polygon

import numpy as np
import pandas as pd
from sentinelhub import (
    CRS,
    DataCollection,
    Geometry,
    SentinelHubStatistical,
    bbox_to_dimensions,
    parse_time,
)
from system.authentication import Config
from system.helper_functions import (
    adapt_start_end_time,
    convert_dataframe_tz,
    create_out_dir,
    date_to_string,
    get_last_month,
)


class Band:
    """Define a single band."""

    def __init__(self: Band, name: str, stats: dict) -> None:
        """Initialize Band class."""
        self.name = name
        self.valid = False
        self.stats = stats

    def check_valid(self: Band) -> None:
        """Check if band is valid."""
        if self.stats["sampleCount"] > self.stats["noDataCount"]:
            self.valid = True


class Bands:
    """Have a list of different bands."""

    def __init__(self: Bands) -> None:
        """Initialize Bands class."""
        self.bands = []

    def check_valid(self: Bands) -> bool:
        """Check for any valid band."""
        return any(band.valid for band in self.bands)


class IndicatorData(Config):
    """Encapsulate raw data retrieval."""

    def __init__(
        self: IndicatorData,
        aoi: Polygon | MultiPolygon,
        fid: str,
        out_dir: Path,
        start_date: str | None = None,
        end_date: str | None = None,
        archive_data: pd.DataFrame | None = None,
        crs: CRS = CRS.WGS84,
        resolution: int = 5,
        orbit: str = "asc",
        pol: str = "VH",
        monthly: bool = False,
        online: bool = True,  # load statistics from Sentinel Hub, False if solely using offline data
    ) -> None:
        """Initialize IndicatorData class."""
        super().__init__()
        self.dataframe = pd.DataFrame()
        self.config = None
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
        self.regression_dataframe = None
        self.linear_dataframe = None  # dataframe for default linear regression
        self.pol = pol
        self.out_dir = out_dir
        self.thresholds = {"min": None, "max": None}
        self.outliers = None
        self.monthly = monthly
        self.online = online

        self.get_start_end_date(start=start_date, end=end_date)
        self._get_geometry()
        self._get_dimensions()
        self._get_collection()
        self._create_out_dirs()
        self._get_column_rename_map()

    def get_start_end_date(self: IndicatorData, start: str, end: str) -> None:
        """Get start and end date."""
        if start is None:
            self.start_date = "2014-05-01"

        else:
            self.start_date = start

        if end is None:
            self.end_date = get_last_month()

        else:
            self.end_date = end

        self._set_interval()

    def _set_interval(self: IndicatorData) -> None:
        """Set date interval for data retrieval."""
        self.interval = (
            adapt_start_end_time(start=True, date=self.start_date),
            adapt_start_end_time(end=True, date=self.end_date),
        )

    def _get_column_rename_map(self: IndicatorData) -> None:
        self.columns_map = {
            "B0_min": "min",
            "B0_max": "max",
            "B0_mean": "mean",
            "B0_stDev": "std",
            "B0_sampleCount": "sample_count",
            "B0_noDataCount": "nodata_count",
        }

    def _create_out_dirs(self: IndicatorData) -> None:
        """Create output directory if not existing."""
        for out in ["plot", "raw", "scenes", "anomalies", "regression"]:
            create_out_dir(base_dir=self.out_dir, out_dir=out)

    def _get_geometry(self: IndicatorData) -> None:
        self.geometry = Geometry(self.aoi, crs=self.crs)  # shapely polygon with CRS

    def _get_dimensions(self: IndicatorData) -> None:
        """Get width and height of polygon in pixels. CRS is the respective UTM, automatically derived."""
        self.size = bbox_to_dimensions(self.geometry.bbox, self.resolution)

    def _get_collection(self: IndicatorData) -> None:
        if self.orbit == "asc":
            self.collection = DataCollection.SENTINEL1_IW_ASC

        else:
            self.collection = DataCollection.SENTINEL1_IW_DES

    def _correct_datatypes(self: IndicatorData) -> None:
        """Convert dataframe columns from float64 to float32."""
        float64_cols = list(self.dataframe.select_dtypes(include="float64"))
        self.dataframe[float64_cols] = self.dataframe[float64_cols].astype("float32")

    def check_dates(self: IndicatorData, start: bool = False, end: bool = False) -> str | None:
        """Check if earlier or future data is requested."""
        # start_date is less than earliest archive date --> new data required for earlier dates
        if start and convert_dataframe_tz(var=pd.to_datetime(self.interval[0])) < convert_dataframe_tz(
            var=pd.to_datetime(self.archive_data.index[0])
        ):
            self.end_date = self.archive_data.index[0].date()  # strip date what looks like 2021-01-03 00:00:00+00:00
            self._set_interval()

            return "past"

        # end_date is greater than latest archive date --> new data required for future dates
        if end and convert_dataframe_tz(pd.to_datetime(self.interval[-1])) > convert_dataframe_tz(
            pd.to_datetime(self.archive_data.index[-1])
        ):
            self.start_date = self.archive_data.index[-1].date()
            self._set_interval()

            return "future"

        return None

    def check_existing_data(self: IndicatorData) -> [bool, bool | None]:
        """Check for existing archive data."""
        if self.archive_data is not None:  # if some raw date has already been saved
            if f"{self.fid}_mean" in self.archive_data.columns:  # feature exists in archive data
                return True, True

        else:  # no archive data
            return False, None

        return True, False  # archive data present, but required feature not recorded

    def concat_dataframes(
        self: IndicatorData, past_df: pd.Dataframe | None = None, future_df: pd.DataFrame | None = None
    ) -> None:
        """Append archive dates to earlier dates.

        For example ["2019-11-11", "2019-12-12"] is first appended by ["2020-01-01", "2020-02-02"]
           date        val
        0  2019-11-11  11
        1  2019-12-12  12
        2  2020-01-01   1
        3  2020-02-02   2
        The, append recent dates to archive dates,
        e.g. ["2020-01-01", "2020-02-02"] is first appended by ["2020-03-03", "2020-04-04"]
           date        val
        0  2020-01-01  1
        1  2020-02-02  2
        2  2020-03-03  3
        3  2020-04-04  4
        """
        self.dataframe = pd.concat([past_df, self.archive_data, future_df], axis=0)

    def get_request_grd(self: IndicatorData) -> None:
        """Define evaluation script and Sentinel Hub request."""
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

    def get_data(self: IndicatorData) -> None:
        """Extract data from request."""
        self.stats = self.request.get_data()[0]

    @staticmethod
    def get_band_stats(bands: dict) -> Generator[Band, Band]:
        """Retrieve band."""
        for key, values in bands.items():
            band = Band(name=key, stats=values["stats"])
            band.check_valid()
            yield band

    def stats_to_df(self: IndicatorData) -> None:
        """Store Sentinel-1 statistics in dataframe."""
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

    def rename_column(self: IndicatorData, src: str, dst: str) -> None:
        """Rename dataframe column."""
        self.dataframe.rename(columns={f"{src}": f"{self.fid}_{dst}"}, inplace=True)

    def remove_duplicate_date(self: IndicatorData) -> None:
        """Remove duplicate dates."""
        self.dataframe = self.dataframe[~self.dataframe.index.duplicated()]

    def get_offline_data(self: IndicatorData) -> None:
        """Get dataframe from disk as using Sentinel Hub is not desired."""
        self.dataframe = self.archive_data

    def slice_dates(self: IndicatorData) -> None:
        """Slice a specific part of the time series."""
        start_slice = date_to_string(date=pd.to_datetime(self.interval[0], utc=True))
        end_slice = date_to_string(date=pd.to_datetime(self.interval[1], utc=True))

        # find closest start and end date in given dataframe
        # e.g. if start_slice = 2021-03-01 but given dates cover 2021-02-28 and 2021-03-02 only
        closest_start = self.dataframe.index[self.dataframe.index.get_indexer([start_slice], method="nearest")]
        closest_end = self.dataframe.index[self.dataframe.index.get_indexer([end_slice], method="nearest")]

        # if closest available date is in another month, get the closest date that comes later
        # by that ensure that monthly statistics remain valid
        # e.g. if start_slice = 2021-03-01 but closest date is 2021-02-28, select next date like 2021-03-02
        if pd.to_datetime(start_slice).month != closest_start.month.values[0]:
            closest_start = self.dataframe.iloc[[np.searchsorted(self.dataframe.index, start_slice)]].index

        if pd.to_datetime(end_slice).month != closest_end.month.values[0]:
            closest_end = self.dataframe.iloc[[np.searchsorted(self.dataframe.index, end_slice)]].index

        self.dataframe = self.dataframe.loc[closest_start[0] : closest_end[0]]
