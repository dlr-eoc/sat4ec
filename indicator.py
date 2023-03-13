import os
from shapely.geometry.polygon import Polygon
from sentinelhub import Geometry, CRS, bbox_to_dimensions, DataCollection, SentinelHubStatistical, SHConfig


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
    def __init__(self, aoi=None, start_date=None, end_date=None, crs=CRS.WGS84, resolution=5, ascending=True):
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
                aggregation_interval='P1D',  # interval set to 1 day increment
                size=self.size
            ),
            input_data=[
                SentinelHubStatistical.input_data(
                    self.collection,
                    other_args={"dataFilter": {"mosaickingOrder": "mostRecent", "resolution": "HIGH"},
                                "processing": {"orthorectify": "True", "backCoeff": "SIGMA0_ELLIPSOID",
                                               "demInstance": "COPERNICUS"}},
                )
            ],
            geometry=self.geometry,
            config=self.config
        )


if __name__ == "__main__":
    aoi = Polygon([
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
    ])

    indicator = Indicator(
        aoi=aoi,
        start_date="2022-11-01",
        end_date="2022-11-10"
    )

    indicator.get_request()
    stats = indicator.request.get_data()[0]
