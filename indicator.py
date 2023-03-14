import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from shapely.geometry.polygon import Polygon
from sentinelhub import (
    Geometry,
    CRS,
    bbox_to_dimensions,
    DataCollection,
    SentinelHubStatistical,
    SHConfig,
    parse_time,
)


class Config:
    def __init__(self, _id=None, secret=None):
        self.id = _id
        self.secret = secret
        self.config = None

        self._get_credentials()
        self._get_config()

    def _get_credentials(self):
        if not self.id:
            self.id = os.environ["SH_CLIENT_ID"]

        if not self.secret:
            self.secret = os.environ["SH_CLIENT_SECRET"]

    def _get_config(self):
        self.config = SHConfig()

        self.config.sh_client_id = self.id
        self.config.sh_client_secret = self.secret


class Indicator(Config):
    def __init__(
        self,
        aoi=None,
        out_dir=None,
        start_date=None,
        end_date=None,
        crs=CRS.WGS84,
        resolution=5,
        ascending=True,
    ):
        super().__init__()
        self.aoi = aoi
        self.crs = crs
        self.geometry = None
        self.ascending = ascending
        self.interval = (f"{start_date}T00:00:00Z", f"{end_date}T23:59:59Z")
        self.size = None
        self.resolution = resolution
        self.aggregation = None
        self.eval_script = None
        self.request = None
        self.stats = None
        self.dataframe = None
        self.out_dir = out_dir

        self._get_geometry()
        self._get_dimensions()
        self._get_collection()

    def _get_geometry(self):
        self.geometry = Geometry(self.aoi, crs=self.crs)  # shapely polygon with CRS

    def _get_dimensions(self):
        """
        Get width and height of polygon in pixels. CRS is the respective UTM, automatically derived.
        """
        self.size = bbox_to_dimensions(self.geometry.bbox, self.resolution)

    def _get_collection(self):
        if self.ascending:
            self.collection = DataCollection.SENTINEL1_IW_ASC

        else:
            self.collection = DataCollection.SENTINEL1_IW_DES

    def _correct_datatypes(self):
        # Select columns with float64 dtype
        float64_cols = list(self.dataframe.select_dtypes(include="float64"))
        self.dataframe[float64_cols] = self.dataframe[float64_cols].astype("float32")

    def get_request(self):
        # evalscript (unit: dB)
        self.eval_script = """
        //VERSION=3
        function setup() {
          return {
            input: [{
              bands: ["VH", "dataMask"]
            }],
            output: [
              {
                id: "default",
                bands: 1
              },
              {
                id: "dataMask",
                bands: 1
              }]
          };
        }

        function evaluatePixel(samples) {
            return {
                default: [toDb(samples.VH)],
                dataMask: [samples.dataMask],
            };
        }

        function toDb(sigma_linear) {
           if(sigma_linear === 0) return 0;
           return (10 * Math.log10(sigma_linear))  //equation from GEE Sentinel-1 Prepocessing
        }
        """

        # statistical API request (unit: dB)
        self.request = SentinelHubStatistical(
            aggregation=SentinelHubStatistical.aggregation(
                evalscript=self.eval_script,
                time_interval=self.interval,
                aggregation_interval="P1D",  # interval set to 1 day increment
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
                            "backCoeff": "SIGMA0_ELLIPSOID",
                            "demInstance": "COPERNICUS",
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

        for item in self.stats["data"]:
            df_entry = {
                "interval_from": pd.to_datetime(parse_time(item["interval"]["from"])),
                "interval_to": pd.to_datetime(parse_time(item["interval"]["to"])),
            }

            bands = Bands()

            for band in self.get_band_stats(item["outputs"]["default"]["bands"]):
                if not band.valid:
                    continue

                for stat_name, stat_value in band.stats.items():
                    df_entry[f"{band.name}_{stat_name}"] = stat_value

                bands.bands.append(band)

            if bands.check_valid():
                target.append(df_entry)

        self.dataframe = pd.DataFrame(target)
        self._correct_datatypes()

    def save(self):
        out_file = self.out_dir.joinpath(
            datetime.now().strftime("%Y_%m_%d"),
            f"indicator_1_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv",
        )

        if not out_file.parent.exists():
            out_file.parent.mkdir(parents=True, exist_ok=True)

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


if __name__ == "__main__":
    aoi = Polygon(
        [
            (3.754824, 51.096633),
            (3.753451, 51.096242),
            (3.755747, 51.093102),
            (3.755661, 51.09511),
            (3.755211, 51.094989),
            (3.754953, 51.095393),
            (3.755211, 51.09608),
            (3.755125, 51.0967),
            (3.755447, 51.097953),
            (3.755168, 51.098048),
            (3.755009, 51.097886),
            (3.754116, 51.097697),
            (3.754824, 51.096633),
        ]
    )

    indicator = Indicator(
        aoi=aoi,
        out_dir=Path(r"/mnt/data1/gitlab/sat4ec/results"),
        start_date="2020-11-01",
        end_date="2022-11-30",
        ascending=False,
    )

    indicator.get_request()
    indicator.get_data()
    indicator.stats_to_df()
    indicator.save()
