import argparse
import shutil
import traceback
from aoi_check import AOI
from system.collections import SubsetCollection as Subsets
from system.collections import OrbitCollection as Orbits
from plot_data import Plots
from anomaly_detection import Anomalies
from pathlib import Path
from datetime import datetime

from data_retrieval import IndicatorData as IData
from stac import StacCollection
from system.helper_functions import get_logger, get_last_month, mutliple_orbits_raw_range

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
    orbit_collection=None,
    monthly=False,
    linear=False,
    features=None,
    linear_fill=False,
):
    with Plots(
        out_dir=out_dir,
        name=name,
        monthly=monthly,
        orbit=orbit_collection.orbit,
        linear=linear,
        linear_fill=linear_fill,
        features=features,
        raw_range=mutliple_orbits_raw_range(  # only for adjusting the plot space, not actually plotted here
            fid="0" if len(features) == 1 else "total",
            orbit_collection=orbit_collection
        ),
    ) as plotting:
        plotting.plot_features(orbit_collection=orbit_collection)
        plotting.finalize()

        if monthly:
            plotting.save_raw()

        else:
            plotting.save_regression(svg=True)

        plotting.show_plot()


def run_indicator(_indicator):
    _indicator.get_request_grd()
    _indicator.get_data()
    _indicator.stats_to_df()

    return _indicator


def compute_raw_data(
    archive_data=None,
    feature=None,
    out_dir=None,
    start_date=None,
    end_date=None,
    orbit="asc",
    pol="VH",
    monthly=False,
):
    indicator = IData(
        archive_data=archive_data,
        aoi=feature.geometry,
        fid=feature.fid,
        out_dir=out_dir,
        start_date=start_date,
        end_date=end_date,
        orbit=orbit,
        pol=pol,
        monthly=monthly,
    )
    existing_keyword, column_keyword = indicator.check_existing_data()

    if not existing_keyword:  # no archive data, run indicator once
        print("not existing")
        indicator = run_indicator(indicator)

    else:  # archive data present, check if new feature and earlier and/or future data required
        if not column_keyword:
            print("no column")
            # indicator = run_indicator(indicator)

        else:
            if indicator.check_dates(start=True) == "past":
                indicator = run_indicator(indicator)
                indicator.insert_past_dates()
                indicator.get_start_end_date(start=start_date, end=end_date)

            if indicator.check_dates(end=True) == "future":
                indicator = run_indicator(indicator)
                indicator.insert_future_dates()
                indicator.get_start_end_date(start=start_date, end=end_date)

            indicator.remove_duplicate_date()

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
    anomalies = Anomalies(
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
    anomalies.save_anomalies()
    anomalies.cleanup()

    return anomalies


def get_s1_scenes(
        data=None,
        features=None,
        geometries=None,
        orbit="asc",
        pol="VH",
        out_dir=None,
):
    stac_collection = StacCollection(
        data=data.copy(),
        features=features,
        geometries=geometries,
        orbit=orbit,
        pol=pol,
        out_dir=out_dir,
    )
    stac_collection.get_stac_collection()


def main(
    aoi_data=None,
    out_dir=None,
    start_date=None,
    end_date=None,
    pol="VH",
    in_orbit="asc",
    name="Unkown Brand",
    monthly=False,
    regression="spline",
    linear=False,
    aoi_split=False,
    linear_fill=False,
    overwrite_raw=False,
):
    orbit_collection = Orbits(orbit=in_orbit, monthly=monthly)

    for orbit in orbit_collection.orbits:
        with AOI(data=aoi_data, aoi_split=aoi_split) as aoi_collection:
            subsets = Subsets(out_dir=out_dir, monthly=monthly, orbit=orbit, pol=pol, overwrite_raw=overwrite_raw)
            subsets.check_existing_raw()

            for index, feature in enumerate(aoi_collection.get_feature()):
                indicator = compute_raw_data(
                    archive_data=subsets.archive_dataframe.loc[
                        :, subsets.archive_dataframe.columns.str.startswith(f"{feature.fid}_")
                    ],
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
                subsets.add_geometry(indicator.geometry)

        if len(subsets.features) > 1:
            subsets.aggregate_columns()

        subsets.save_raw()  # save raw data

        if monthly:
            subsets.monthly_aggregate()
            subsets.save_raw()  # save monthly raw data

        subsets.apply_regression(mode=regression)
        subsets.save_regression(mode=regression)  # save spline data
        orbit_collection.add_subsets(subsets=subsets, orbit=orbit)

        if monthly:
            raw_anomalies = compute_anomaly(
                df=subsets.dataframe,
                linear_data=subsets.linear_dataframe,
                out_dir=subsets.out_dir,
                orbit=orbit,
                pol=pol,
                monthly=monthly,
                features=subsets.features,
            )
            orbit_collection.add_anomalies(anomalies=raw_anomalies, orbit=orbit)

            # get_s1_scenes(
            #     data=raw_anomalies.dataframe,
            #     features=subsets.features,
            #     geometries=subsets.geometries,
            #     orbit=orbit,
            #     pol=pol,
            #     out_dir=subsets.out_dir,
            # )

        else:
            reg_anomalies = compute_anomaly(
                df=subsets.regression_dataframe,
                linear_data=subsets.linear_dataframe,
                out_dir=subsets.out_dir,
                orbit=orbit,
                pol=pol,
                monthly=monthly,
                features=subsets.features,
            )
            orbit_collection.add_anomalies(anomalies=reg_anomalies, orbit=orbit)

            # get_s1_scenes(
            #     data=reg_anomalies.dataframe,
            #     features=subsets.features,
            #     geometries=subsets.geometries,
            #     orbit=orbit,
            #     pol=pol,
            #     out_dir=subsets.out_dir,
            # )

    plot_data(
        orbit_collection=orbit_collection,
        out_dir=subsets.out_dir,
        name=name,
        monthly=monthly,
        linear=linear,
        features=subsets.features,
        linear_fill=linear_fill,
    )


def parse_boolean(param=None, literal=None):
    if param[0].lower() == "true":
        return True

    elif param[0].lower() == "false":
        return False

    else:
        raise ValueError(f"The provided value {param[0]} for --{literal} is not supported. "
                         f"Choose from [true, false].")


def run():
    args = parse_commandline_args()

    if not args.end_date or args.end_date == "None":
        end_date = get_last_month()

    else:
        end_date = args.end_date

    if not args.start_date or args.start_date == "None":
        start_date = "2014-05-01"

    else:
        start_date = args.start_date

    # check if dates are in format YYYY-MM-DD
    for _date in [start_date, end_date]:
        _date = datetime.strptime(_date, "%Y-%m-%d")  # throws an error if conversion fails

    if isinstance(args.orbit, list):
        orbit = args.orbit[0].lower()

    else:
        orbit = args.orbit.lower()

    if isinstance(args.polarization, list):
        pol = args.polarization[0].upper()

    else:
        pol = args.polarization.upper()

    linear = parse_boolean(param=args.linear, literal="linear")
    linear_fill = parse_boolean(param=args.linear_fill, literal="linear_fill")
    aoi_split = parse_boolean(param=args.aoi_split, literal="aoi_split")
    overwrite_raw = parse_boolean(param=args.overwrite_raw, literal="overwrite_raw")

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
        start_date=start_date,
        end_date=end_date,
        pol=pol,
        in_orbit=orbit,
        name=args.name[0],
        monthly=aggregate,
        regression=args.regression[0],
        linear=linear,
        aoi_split=aoi_split,
        linear_fill=linear_fill,
        overwrite_raw=overwrite_raw,
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
        choices=["asc", "des", "both"],
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
    parser.add_argument(
        "--linear_fill",
        nargs=1,
        help="Wether to fill the linear insensitive range or not, default: false.",
        choices=["true", "false"],
        default="false"
    )
    parser.add_argument(
        "--overwrite_raw",
        nargs=1,
        help="Overwrite existing raw data if desired, default: false.",
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
