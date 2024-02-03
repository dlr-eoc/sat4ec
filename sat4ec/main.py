"""Main entry point of application."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

from anomaly_detection import Anomalies
from aoi_check import AOI, Feature
from data_retrieval import IndicatorData as IData
from plot_data import Plots
from stac import StacCollection
from system.helper_functions import get_last_month, mutliple_orbits_raw_range
from system.orbit_collections import OrbitCollection as Orbits
from system.subset_collections import SubsetCollection as Subsets


def plot_data(
    out_dir: Path,
    name: str,
    orbit_collection: Orbits,
    features: list,
    monthly: bool = False,
    linear: bool = False,
    linear_fill: bool = False,
    aoi_split: bool = False,
) -> int:
    """Encapsulate the plotting routine."""
    with Plots(
        out_dir=out_dir,
        name=name,
        monthly=monthly,
        orbit=orbit_collection.orbit,
        linear=linear,
        linear_fill=linear_fill,
        features=features,
        aoi_split=aoi_split,
        raw_range=mutliple_orbits_raw_range(  # only for adjusting the plot space, not actually plotted here
            fid="0" if len(features) == 1 else "total",
            orbit_collection=orbit_collection,
        ),
    ) as plotting:
        plotting.plot_features(orbit_collection=orbit_collection)
        plotting.finalize()

        if monthly:
            plotting.save_raw(svg=True)

        else:
            plotting.save_regression(svg=True)

        plotting.show_plot()

    return 0


def run_indicator(_indicator: IData) -> IData:
    """Encapsulate call of Indicator class."""
    _indicator.get_request_grd()
    _indicator.get_data()
    _indicator.stats_to_df()

    return _indicator


def compute_raw_data(
    archive_data: pd.DataFrame,
    feature: Feature,
    out_dir: Path,
    start_date: str,
    end_date: str,
    orbit: str = "asc",
    pol: str = "VH",
    monthly: bool = False,
) -> IData:
    """Fetch raw data from Sentinel Hub."""
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
        indicator = run_indicator(indicator)

    elif existing_keyword and not column_keyword:  # archive data present
        # decide if executing following code: indicator = run_indicator(indicator)
        pass

    # check if new feature and earlier and/or future data required
    elif existing_keyword and column_keyword:  # archive data present
        if indicator.check_dates(start=True) == "past":
            indicator = run_indicator(indicator)
            past_df = indicator.dataframe
            indicator.get_start_end_date(start=start_date, end=end_date)

        else:
            past_df = indicator.dataframe

        if indicator.check_dates(end=True) == "future":
            indicator = run_indicator(indicator)
            future_df = indicator.dataframe
            indicator.get_start_end_date(start=start_date, end=end_date)

        else:
            future_df = indicator.dataframe

        indicator.concat_dataframes(past_df=past_df, future_df=future_df)
        indicator.remove_duplicate_date()
        indicator.slice_dates()

    return indicator


def compute_anomaly(
    df: pd.DataFrame,
    linear_data: pd.DataFrame,
    out_dir: Path,
    features: list,
    anomaly_column: str = "mean",
    orbit: str = "asc",
    pol: str = "VH",
    monthly: bool = False,
    aoi_split: bool = False,
) -> Anomalies:
    """Encapsulate anomaly detection."""
    anomalies = Anomalies(
        data=df,
        anomaly_column=anomaly_column,
        features=features,
        out_dir=out_dir,
        orbit=orbit,
        pol=pol,
        monthly=monthly,
        linear_data=linear_data,
        aoi_split=aoi_split,
    )

    anomalies.find_extrema()
    anomalies.save_anomalies()
    anomalies.cleanup()

    return anomalies


def get_s1_scenes(
    out_dir: Path,
    data: pd.DataFrame,
    features: list,
    geometries: list,
    orbit: str = "asc",
    pol: str = "VH",
    monthly: bool = False,
) -> int:
    """Get a list of Sentinel-1 scenes used in this analysis."""
    stac_collection = StacCollection(
        data=data.copy(),
        features=features,
        geometries=geometries,
        orbit=orbit,
        pol=pol,
        out_dir=out_dir,
        monthly=monthly,
    )
    stac_collection.get_stac_collection()

    return 0


def main(
    aoi_data: str,
    out_dir: Path,
    start_date: str,
    end_date: str,
    pol: str = "VH",
    in_orbit: str = "asc",
    name: str = "Unkown Brand",
    monthly: bool = False,
    regression: str = "spline",
    linear: bool = False,
    aoi_split: bool = False,
    linear_fill: bool = False,
    overwrite_raw: bool = False,
) -> 0:
    """Encapsulate entry point for main functions."""
    orbit_collection = Orbits(orbit=in_orbit, monthly=monthly)

    for orbit in orbit_collection.orbits:
        with AOI(data=aoi_data, aoi_split=aoi_split) as aoi_collection:
            subsets = Subsets(
                out_dir=out_dir,
                monthly=monthly,
                orbit=orbit,
                pol=pol,
                overwrite_raw=overwrite_raw,
                aoi_split=aoi_split,
            )
            subsets.check_existing_raw()

            for _, feature in enumerate(aoi_collection.get_feature()):
                indicator = compute_raw_data(
                    archive_data=subsets.archive_dataframe.loc[
                        :,
                        subsets.archive_dataframe.columns.str.startswith(f"{feature.fid}_"),
                    ]
                    if subsets.archive_dataframe is not None
                    else None,
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

            subsets.remove_dataframe_items()

        if len(subsets.features) > 1:
            subsets.aggregate_columns()

        subsets.save_daily_raw()  # save raw data

        if monthly:
            subsets.monthly_aggregate()
            subsets.save_monthly_raw()  # save monthly raw data

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
                aoi_split=subsets.aoi_split,
            )
            orbit_collection.add_anomalies(anomalies=raw_anomalies, orbit=orbit)

            get_s1_scenes(
                data=raw_anomalies.dataframe,
                features=subsets.features,
                geometries=subsets.geometries,
                orbit=orbit,
                pol=pol,
                out_dir=subsets.out_dir,
                monthly=monthly,
            )

        else:
            reg_anomalies = compute_anomaly(
                df=subsets.regression_dataframe,
                linear_data=subsets.linear_dataframe,
                out_dir=subsets.out_dir,
                orbit=orbit,
                pol=pol,
                monthly=monthly,
                features=subsets.features,
                aoi_split=subsets.aoi_split,
            )
            orbit_collection.add_anomalies(anomalies=reg_anomalies, orbit=orbit)

            get_s1_scenes(
                data=reg_anomalies.dataframe,
                features=subsets.features,
                geometries=subsets.geometries,
                orbit=orbit,
                pol=pol,
                out_dir=subsets.out_dir,
                monthly=monthly,
            )

    plot_data(
        orbit_collection=orbit_collection,
        out_dir=subsets.out_dir,
        name=name,
        monthly=monthly,
        linear=linear,
        features=subsets.features,
        linear_fill=linear_fill,
        aoi_split=subsets.aoi_split,
    )

    return 0


def parse_boolean(param: str, literal: str) -> bool:
    """Parse boolean string values into real booleans."""
    if param[0].lower() != "true" and param[0].lower() != "false":
        raise ValueError(
            f"The provided value {param[0]} for --{literal} is not supported. " f"Choose from [true, false]."
        )

    if param[0].lower() == "true":
        return True

    return False


def run() -> int:
    """Encapsulate entry point for CLI."""
    args = parse_commandline_args()

    end_date = get_last_month() if not args.end_date or args.end_date == "None" else args.end_date
    start_date = "2014-05-01" if not args.start_date or args.start_date == "None" else args.start_date

    # check if dates are in format YYYY-MM-DD
    for _date in [start_date, end_date]:
        _date = datetime.strptime(_date, "%Y-%m-%d")  # throws an error if conversion fails

    orbit = args.orbit[0].lower() if isinstance(args.orbit, list) else args.orbit.lower()
    pol = args.polarization[0].upper() if isinstance(args.polarization, list) else args.polarization.upper()

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

    return 0


def parse_commandline_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Compute aggregated statistics on Sentinel-1 data")
    parser.add_argument(
        "--aoi_data",
        default="dummy",
        help="Path to AOI.[GEOJSON, SHP, GPKG], AOI geometry as WKT, " "Polygon or Multipolygon.",
        metavar="AOI",
        required=True,
    )
    parser.add_argument(
        "--aoi_split",
        nargs=1,
        help="Wether to split the AOI into separate features or not, default: false.",
        choices=["true", "false"],
        default="false",
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
        default="spline",
    )
    parser.add_argument(
        "--linear",
        nargs=1,
        help="Wether to plot the linear regression with insensitive range or not, default: false.",
        choices=["true", "false"],
        default="false",
    )
    parser.add_argument(
        "--linear_fill",
        nargs=1,
        help="Wether to fill the linear insensitive range or not, default: false.",
        choices=["true", "false"],
        default="false",
    )
    parser.add_argument(
        "--overwrite_raw",
        nargs=1,
        help="Overwrite existing raw data if desired, default: false.",
        choices=["true", "false"],
        default="false",
    )

    return parser.parse_args(args)


if __name__ == "__main__":
    run()
