import argparse
import shutil
import traceback
from aoi_check import AOI
from anomaly_detection import AnomalyCollection
from plot_data import PlotCollection, PlotData
from pathlib import Path
from datetime import datetime

from data_retrieval import IndicatorData as IData
from data_retrieval import SubsetCollection as Subsets
from stac import StacItems
from system.helper_functions import get_logger, get_last_month

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
    reg_data=None,
    anomaly_data=None,
    linear_data=None,
    orbit="asc",
    monthly=False,
    linear=False,
    features=None,
):
    with PlotCollection(
        out_dir=out_dir,
        name=name,
        raw_data=raw_data,
        reg_data=reg_data,
        anomaly_data=anomaly_data,
        linear_data=linear_data,
        orbit=orbit,
        monthly=monthly,
        linear=linear,
        features=features,
    ) as plotting:
        plotting.plot_features()
        plotting.finalize(show=True)

        if monthly:
            plotting.save_raw()

        else:
            plotting.save_regression()


def compute_raw_data(
    feature=None,
    out_dir=None,
    start_date=None,
    end_date=None,
    orbit="asc",
    pol="VH",
    monthly=False,
):
    indicator = IData(
        aoi=feature.geometry,
        fid=feature.fid,
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

    return indicator


def compute_anomaly(
    df=None,
    linear_data=None,
    anomaly_column="mean",
    out_dir=None,
    orbit="asc",
    pol="VH",
    monthly=False,
    features=None,
):
    anomalies = AnomalyCollection(
        data=df,
        anomaly_column=anomaly_column,
        features=features,
        out_dir=out_dir,
        orbit=orbit,
        pol=pol,
        monthly=monthly,
        linear_data=linear_data,
    )

    anomalies.find_extrema()

    if monthly:
        anomalies.save_raw()

    else:
        anomalies.save_regression()

    return anomalies


def main(
    aoi_data=None,
    out_dir=None,
    start_date=None,
    end_date=None,
    pol="VH",
    orbit="asc",
    name="Unkown Brand",
    monthly=False,
    regression="spline",
    linear=False,
    aoi_split=False,
):
    with AOI(data=aoi_data, aoi_split=aoi_split) as aoi_collection:
        subsets = Subsets(out_dir=out_dir, monthly=monthly, orbit=orbit, pol=pol)

        for index, feature in enumerate(aoi_collection.get_feature()):
            indicator = compute_raw_data(
                feature=feature,
                out_dir=out_dir,
                start_date=start_date,
                end_date=end_date,
                orbit=orbit,
                pol=pol,
                monthly=monthly,
            )

            subsets.add_subset(df=indicator.dataframe)
            subsets.add_feature(feature)

        if len(subsets.features) > 1:
            subsets.aggregate_columns()

        subsets.save_raw()  # save raw data

        if monthly:
            subsets.monthly_aggregate()
            subsets.save_raw()  # save raw mothly data

        # TODO: regression on monthly data? Currently linear and spline regression are computed
        subsets.apply_regression(mode=regression)
        subsets.save_regression(mode=regression)  # save spline data

        raw_anomalies = compute_anomaly(
            df=subsets.dataframe,
            linear_data=subsets.linear_dataframe,
            out_dir=subsets.out_dir,
            orbit=orbit,
            pol=pol,
            monthly=monthly,
            features=subsets.features,
        )

        reg_anomalies = compute_anomaly(
            df=subsets.regression_dataframe,
            linear_data=subsets.linear_dataframe,
            out_dir=subsets.out_dir,
            orbit=orbit,
            pol=pol,
            monthly=monthly,
            features=subsets.features,
        )

        # stac = StacItems(
        #     data=reg_anomalies.dataframe,
        #     geometry=indicator.geometry,
        #     orbit=indicator.orbit,
        #     pol=pol,
        #     out_dir=indicator.out_dir,
        # )

        if monthly:
            # plot anomalies on raw data
            plot_data(
                out_dir=subsets.out_dir,
                name=name,
                raw_data=subsets.dataframe,
                reg_data=subsets.dataframe,
                anomaly_data=raw_anomalies.dataframe,
                linear_data=subsets.linear_dataframe,
                orbit=orbit,
                monthly=monthly,
                linear=linear,
                features=subsets.features,
            )

        else:
            # plot anomalies on regression data
            plot_data(
                out_dir=subsets.out_dir,
                name=name,
                raw_data=subsets.dataframe,
                anomaly_data=reg_anomalies.dataframe,
                reg_data=subsets.regression_dataframe,
                linear_data=subsets.linear_dataframe,
                orbit=orbit,
                monthly=monthly,
                linear=linear,
                features=subsets.features,
            )

        # stac.scenes_to_df()
        # stac.join_with_anomalies()
        # stac.save()


def run():
    args = parse_commandline_args()

    if not args.end_date:
        end_date = get_last_month()

    else:
        end_date = args.end_date

    # check if dates are in format YYYY-MM-DD
    for _date in [args.start_date, end_date]:
        _date = datetime.strptime(_date, "%Y-%m-%d")  # throws an error if conversion fails

    if isinstance(args.orbit, list):
        orbit = args.orbit[0].lower()

    else:
        orbit = args.orbit.lower()

    if isinstance(args.polarization, list):
        pol = args.polarization[0].upper()

    else:
        pol = args.polarization.upper()

    if args.linear[0].lower() == "true":
        linear = True

    elif args.linear[0].lower() == "false":
        linear = False

    else:
        raise ValueError(f"The provided value {args.linear[0]} for --linear is not supported. "
                         f"Choose from [true, false].")

    if args.aoi_split[0].lower() == "true":
        aoi_split = True

    elif args.aoi_split[0].lower() == "false":
        aoi_split = False

    else:
        raise ValueError(f"The provided value {args.aoi_split[0]} for --aoi_split is not supported. "
                         f"Choose from [true, false].")

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
        end_date=end_date,
        pol=pol,
        orbit=orbit,
        name=args.name[0],
        monthly=aggregate,
        regression=args.regression[0],
        linear=linear,
        aoi_split=aoi_split
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
        required=True,
    )
    parser.add_argument(
        "--aoi_split",
        nargs=1,
        help="Wether to split the AOI into separate features or not, default: false.",
        choices=["true", "false"],
        default="false"
    )
    parser.add_argument(
        "--out_dir",
        default="dummy",
        help="Path to output directory.",
        metavar="OUT",
        required=True,
    )
    parser.add_argument(
        "--start_date",
        help="Begin of the time series, as YYYY-MM-DD, like 2020-11-01",
        metavar="YYYY-MM-DD",
        required=True,
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
    parser.add_argument(
        "--regression",
        nargs=1,
        help="Type of the regression, default: spline.",
        choices=["spline", "poly", "rolling"],
        default="spline"
    )
    parser.add_argument(
        "--linear",
        nargs=1,
        help="Wether to plot the linear regression with insensitive range or not, default: false.",
        choices=["true", "false"],
        default="false"
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
