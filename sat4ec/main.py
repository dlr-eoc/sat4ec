import argparse
import shutil
import traceback
from aoi_check import AOI
from anomaly_detection import Anomaly
from plot_data import PlotData
from pathlib import Path
from datetime import datetime

from data_retrieval import IndicatorData as IData
from stac import StacItems
from system.helper_functions import get_logger

# clean output directory
# for item in Path(OUT_DIR).glob("*"):
#     if item.is_file():
#         item.unlink()
#
#     else:
#         shutil.rmtree(item, ignore_errors=True)


def plot_data(
    out_dir=None,
    name=None,
    raw_data=None,
    spline_data=None,
    anomaly_data=None,
    orbit="asc",
    monthly=False
):
    with PlotData(
        out_dir=out_dir,
        name=name,
        raw_data=raw_data,
        spline_data=spline_data,
        anomaly_data=anomaly_data,
        orbit=orbit,
        monthly=monthly
    ) as plotting:
        plotting.plot_rawdata()
        plotting.plot_splinedata()
        plotting.plot_anomalies()
        plotting.plot_finalize()
        plotting.save_spline()


def compute_raw_data(
    aoi=None,
    out_dir=None,
    start_date=None,
    end_date=None,
    orbit="asc",
    pol="VH",
    monthly=False,
):
    indicator = IData(
        aoi=aoi.geometry,
        out_dir=out_dir,
        start_date=start_date,
        end_date=end_date,
        orbit=orbit,
        pol=pol,
        monthly=monthly,
    )

    indicator.get_request_grd()
    indicator.get_data()
    indicator.stats_to_df()
    indicator.save_raw()  # save raw data

    if monthly:
        indicator.monthly_aggregate()
        indicator.save_raw()  # save raw mothly data

    indicator.apply_regression()
    indicator.save_spline()  # save spline data

    return indicator


def compute_anomaly(
    df=None,
    anomaly_column="mean",
    out_dir=None,
    orbit="asc",
    pol="VH",
    monthly=False,
    spline=False
):
    anomaly = Anomaly(
        data=df,
        anomaly_column=anomaly_column,
        out_dir=out_dir,
        orbit=orbit,
        pol=pol,
        monthly=monthly
    )

    anomaly.find_extrema()

    if spline:
        anomaly.save_spline()

    else:
        anomaly.save_raw()

    return anomaly


def main(
    aoi_data=None,
    out_dir=None,
    start_date=None,
    end_date=None,
    pol="VH",
    orbit="asc",
    name="Unkown Brand",
    monthly=False,
):
    with AOI(data=aoi_data) as aoi:
        aoi.get_features()

        indicator = compute_raw_data(
            aoi=aoi,
            out_dir=out_dir,
            start_date=start_date,
            end_date=end_date,
            orbit=orbit,
            pol=pol,
            monthly=monthly,
        )

        raw_anomalies = compute_anomaly(
            df=indicator.dataframe,
            out_dir=indicator.out_dir,
            orbit=orbit,
            pol=pol,
            monthly=monthly,
            spline=False
        )

        spline_anomalies = compute_anomaly(
            df=indicator.spline_dataframe,
            out_dir=indicator.out_dir,
            orbit=orbit,
            pol=pol,
            monthly=monthly,
            spline=True
        )

        stac = StacItems(
            data=spline_anomalies.dataframe,
            geometry=indicator.geometry,
            orbit=indicator.orbit,
            pol=pol,
            out_dir=indicator.out_dir,
        )

        plot_data(
            out_dir=indicator.out_dir,
            name=name,
            raw_data=indicator.dataframe,
            spline_data=indicator.spline_dataframe,
            anomaly_data=spline_anomalies.dataframe,
            orbit=orbit,
            monthly=monthly
        )

        stac.scenes_to_df()
        stac.join_with_anomalies()
        stac.save()


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

    if args.aggregate[0] == "daily":
        aggregate = False

    elif args.aggregate[0] == "monthly":
        aggregate = True

    else:
        raise ValueError(
            f"The provided value {args.aggregate} for the aggregation is incorrect. Choose from [daily, monthly]."
        )

    main(
        aoi_data=args.aoi_data,
        out_dir=Path(args.out_dir),
        start_date=args.start_date,
        end_date=args.end_date,
        pol=pol,
        orbit=orbit,
        name=args.name[0],
        monthly=aggregate,
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
        "--out_dir",
        default="dummy",
        help="Path to output directory.",
        metavar="OUT",
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
        "--aggregate",
        help="Aggregation interval, default: daily",
        choices=["daily", "monthly"],
        nargs=1,
        default="daily",
    )
    parser.add_argument(
        "--orbit",
        help="Orbit of Sentinel-1 data, default: ascending",
        choices=["asc", "des"],
        nargs=1,
        default="asc",
    )
    parser.add_argument(
        "--name",
        nargs=1,
        help="Name of the location, e.g. BMW Regensburg. Appears in the plot title.",
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
