import argparse
import pandas as pd
import shutil
import traceback
from aoi_check import AOI
from anomaly_detection import Anomaly
from pathlib import Path
from datetime import datetime
from system import get_logger, load_yaml
from sentinelhub import (
    Geometry,
    CRS,
    bbox_to_dimensions,
    DataCollection,
    SentinelHubStatistical,
    SHConfig,
    parse_time,
    SentinelHubCatalog,
)

# container-specific paths
# IN_DIR = Path("/scratch/in")
# OUT_DIR = Path("/scratch/out")
OUT_DIR = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata/results")

# clean output directory
# for item in Path(OUT_DIR).glob("*"):
#     if item.is_file():
#         item.unlink()
#
#     else:
#         shutil.rmtree(item, ignore_errors=True)

# set up logging
logger = get_logger(__name__, out_dir=OUT_DIR)


class Config:
    def __init__(self, _id=None, secret=None):
        self.id = _id
        self.secret = secret
        self.config = None

        self._get_credentials()
        self._get_config()

    def _get_credentials(self):
        credentials = load_yaml(Path.cwd().joinpath("credentials.yaml"))

        if not self.id:
            self.id = credentials["SH_CLIENT_ID"]

        if not self.secret:
            self.secret = credentials["SH_CLIENT_SECRET"]

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
        orbit="asc",
        pol="VH",
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
        self.pol = pol
        self.out_dir = out_dir
        self.timestamp = datetime.now()

        self._get_geometry()
        self._get_dimensions()
        self._get_collection()
        self._get_out_dir()
        self._get_column_rename_map()

    def _get_column_rename_map(self):
        self.columns_map = {
            "B0_max": "max",
            "B0_min": "min",
            "B0_mean": "mean",
            "B0_stDev": "std"
        }

    def _get_out_dir(self):
        self.out_dir = self.out_dir.joinpath(
            f"{self.timestamp.strftime('%Y_%m_%d')}_{self.orbit}_{self.pol}"
        )

        if not self.out_dir.exists():
            self.out_dir.mkdir(parents=True, exist_ok=True)

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
                            "speckleFilter": {
                                "type": "LEE",  # possibleValues:["NONE","LEE"]
                                "windowSizeX": 3,
                                "windowSizeY": 3
                            },
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
        self.dataframe.rename(columns={f"{src}": f"{dst}"}, inplace=True)

    def save(self):
        out_file = self.out_dir.joinpath(
            f"indicator_1_{self.orbit}_{self.pol}_{self.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.csv",
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


class StacItems(Config):
    def __init__(
        self,
        geometry=None,
        df=None,
        orbit="asc",
        pol="VH",
        timestamp=None,
        out_dir=None,
    ):
        super().__init__()

        self.catalog = None
        self.geometry = geometry
        self.anomalies_df = df  # input
        self.dataframe = None  # output
        self.orbit = orbit
        self.timestamp = timestamp
        self.pol = pol
        self.out_dir = out_dir

        self._get_catalog()
        self._get_collection()

    def _get_catalog(self):
        self.catalog = SentinelHubCatalog(config=self.config)

    def _get_collection(self):
        self.catalog.get_collection(DataCollection.SENTINEL1)

    def get_scenes(self):
        return self.anomalies_df.apply(lambda row: self.search_catalog(row), axis=1)

    def scenes_to_df(self):
        scenes_df = self.get_scenes()

        self.dataframe = pd.DataFrame(
            {
                "interval_from": [
                    pd.to_datetime(_item["properties"]["datetime"]).normalize()
                    for values in scenes_df.values
                    for _item in values
                ],
                "scene": [
                    _item["id"] for values in scenes_df.values for _item in values
                ],
            }
        )

    def join_with_anomalies(self):
        self.dataframe = self.dataframe.set_index("interval_from")

        self.dataframe["scene"] = self.dataframe.set_index(self.dataframe.index)[
            "scene"
        ]
        self.dataframe["anomaly"] = self.anomalies_df.set_index(
            self.anomalies_df.index
        )["anomaly"]

    def save(self):
        out_file = self.out_dir.joinpath(
            f"scenes_indicator_1_{self.orbit}_{self.pol}_{self.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        )

        self.dataframe.to_csv(out_file)

    def search_catalog(self, row):
        date = row.name

        search_iterator = self.catalog.search(
            DataCollection.SENTINEL1,
            geometry=self.geometry,
            time=(
                f"{date.year}-{date.month}-{date.day}",
                f"{date.year}-{date.month}-{date.day}",
            ),
            fields={"include": ["id", "properties.datetime"], "exclude": []},
        )

        return list(search_iterator)


def main(
    aoi_data=None,
    start_date=None,
    end_date=None,
    anomaly_options=None,
    pol="VH",
    orbit="asc",
):
    with AOI(data=aoi_data) as aoi:
        aoi.get_features()

        indicator = Indicator(
            aoi=aoi.geometry,
            out_dir=OUT_DIR,
            start_date=start_date,
            end_date=end_date,
            orbit=orbit,
            pol=pol,
        )

        indicator.get_request_grd()
        indicator.get_data()
        indicator.stats_to_df()
        # indicator.save()

        anomaly = Anomaly(
            df=indicator.dataframe,
            df_columns=indicator.columns_map.values(),
            anomaly_column="max",
            out_dir=indicator.out_dir,
            orbit=indicator.orbit,
            timestamp=indicator.timestamp,
            pol=pol,
            options=anomaly_options,
        )

        anomaly.apply_anomaly_detection()
        anomaly.join_with_indicator(indicator_df=indicator.dataframe)
        anomaly.save()

        stac = StacItems(
            geometry=indicator.geometry,
            df=anomaly.dataframe,
            orbit=indicator.orbit,
            timestamp=indicator.timestamp,
            pol=pol,
            out_dir=indicator.out_dir,
        )

        stac.scenes_to_df()
        stac.join_with_anomalies()
        stac.save()

        shutil.move(
            Path(OUT_DIR).joinpath("log_sat4ec.json"),
            indicator.out_dir.joinpath(
                f"LOG_{indicator.orbit}_{indicator.pol}_{indicator.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
            ),
        )


def run():
    args = parse_commandline_args()

    if not args.start_date and not args.end_date:
        raise ValueError(f"You must provide a start and an end date.")

    # check if dates are in format YYYY-MM-DD
    for _date in [args.start_date, args.end_date]:
        _date = datetime.strptime(_date, "%Y-%m-%d")

    if isinstance(args.orbit, list):
        orbit = args.orbit[0].lower()

    else:
        orbit = args.orbit.lower()

    if isinstance(args.polarization, list):
        pol = args.polarization[0].upper()

    else:
        pol = args.polarization.upper()

    anomaly_options = {
        "invert": False,
        "normalize": False,
        "plot": False,
    }

    if isinstance(args.anomaly_options, list):
        if "invert" in args.anomaly_options:
            anomaly_options["invert"] = True

        if "normalize" in args.anomaly_options:
            anomaly_options["normalize"] = True

        if "plot" in args.anomaly_options:
            anomaly_options["plot"] = True

    main(
        aoi_data=args.aoi_data,
        start_date=args.start_date,
        end_date=args.end_date,
        anomaly_options=anomaly_options,
        pol=pol,
        orbit=orbit,
    )


def create_parser():
    parser = argparse.ArgumentParser(
        description="Compute aggregated statistics on Sentinel-1 data"
    )
    parser.add_argument(
        "--aoi_data",
        default="dummy",
        help="Path to AOI.[GEOJSON, SHP, GPKG], AOI geometry as WKT, "
        "Polygon or Multipolygon.",
        metavar="AOI",
    )
    parser.add_argument(
        "--start_date",
        help="Begin of the time series, as YYYY-MM-DD, like 2020-11-01",
        metavar="YYYY-MM-DD",
    )
    parser.add_argument(
        "--end_date",
        help="End of the time series, as YYYY-MM-DD, like 2020-11-01",
        metavar="YYYY-MM-DD",
    )
    parser.add_argument(
        "--polarization",
        help="Polarization of Sentinel-1 data, default: VH",
        choices=["VH", "VV"],
        nargs=1,
        default="VH",
    )
    parser.add_argument(
        "--orbit",
        help="Orbit of Sentinel-1 data, default: ascending",
        choices=["asc", "des"],
        nargs=1,
        default="asc",
    )
    parser.add_argument(
        "--anomaly_options",
        nargs="*",
        choices=["invert", "normalize", "plot"],
        help="Use anomaly detection to list scenes of high or low backscatter. Do not call "
        "to apply default parameters. Consult the README for more info.",
    )

    return parser


def parse_commandline_args():
    return create_parser().parse_args()


if __name__ == "__main__":
    # try:
    run()
    #
    # except:
    #     logger.error(traceback.format_exc())
