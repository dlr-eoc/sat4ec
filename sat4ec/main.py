import argparse
import shutil
import traceback
from aoi_check import AOI
from anomaly_detection import Anomaly
from pathlib import Path
from datetime import datetime

from data_retrieval import IndicatorData as IData
from stac import StacItems
from system.helper_functions import get_logger


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

        indicator = IData(
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
        indicator.apply_spline()
        indicator.save_raw()

        anomaly = Anomaly(
            data=indicator.dataframe,
            df_columns=list(indicator.columns_map.values())[:4],  # ignore sample count and data count
            anomaly_column="mean",
            out_dir=indicator.out_dir,
            orbit=indicator.orbit,
            pol=pol,
            options=anomaly_options,
        )

        anomaly.apply_anomaly_detection()
        anomaly.join_with_indicator()
        anomaly.save()

        stac = StacItems(
            data=anomaly.dataframe,
            geometry=indicator.geometry,
            orbit=indicator.orbit,
            pol=pol,
            out_dir=indicator.out_dir,
        )

        stac.scenes_to_df()
        stac.join_with_anomalies()
        stac.save()

        shutil.move(
            Path(OUT_DIR).joinpath("log_sat4ec.json"),
            indicator.out_dir.joinpath(
                f"LOG_{indicator.orbit}_{indicator.pol}.json"
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

    if isinstance(args.plot_options, list):
        if "minmax" in args.plot_options:
            anomaly_options["minmax"] = True

        if "outliers" in args.plot_options:
            anomaly_options["outliers"] = True

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
    parser.add_argument(
        "--plot_options",
        nargs="*",
        choices=["min", "max", "mean", "std"],
        default=["mean"],
        help="Plot global minimum and maximum or outliers.",
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
