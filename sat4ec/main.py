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
from system.helper_functions import get_logger, get_anomaly_columns


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


def plot_data(
    out_dir=None,
    name=None,
    raw_data=None,
    raw_columns=None,
    spline_data=None,
    anomaly_data=None,
    orbit="asc",
):
    if spline_data is not None:
        with PlotData(
            out_dir=out_dir,
            name=name,
            raw_data=raw_data,
            raw_columns=raw_columns,
            spline_data=spline_data,
            anomaly_data=anomaly_data,
            orbit=orbit,
        ) as plotting:
            plotting.plot_rawdata(background=True)
            plotting.plot_splinedata()
            plotting.plot_anomalies()
            plotting.plot_finalize()
            plotting.save(spline=True)

    else:
        with PlotData(
            out_dir=out_dir,
            name=name,
            raw_data=raw_data,
            raw_columns=raw_columns,
            spline_data=spline_data,
            anomaly_data=anomaly_data,
            orbit=orbit,
        ) as plotting:
            plotting.plot_rawdata(background=False)
            plotting.plot_anomalies()
            plotting.plot_finalize()
            plotting.save(spline=False)


def compute_raw_data(aoi=None, start_date=None, end_date=None, orbit="asc", pol="VH"):
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
    indicator.apply_regression()
    indicator.save(spline=False)  # save raw data
    indicator.save(spline=True)  # save spline data

    return indicator


def compute_anomaly(
    df=None,
    df_columns=None,
    anomaly_column="mean",
    out_dir=None,
    orbit="asc",
    pol="VH",
    spline=False,
):
    anomaly = Anomaly(
        data=df,
        df_columns=df_columns,
        anomaly_column=anomaly_column,
        out_dir=out_dir,
        orbit=orbit,
        pol=pol,
    )

    anomaly.find_extrema()
    anomaly.save(spline=spline)

    return anomaly


def main(
    aoi_data=None,
    start_date=None,
    end_date=None,
    pol="VH",
    orbit="asc",
    name="",
    columns=("mean", "std"),
):
    with AOI(data=aoi_data) as aoi:
        aoi.get_features()

        indicator = compute_raw_data(
            aoi=aoi, start_date=start_date, end_date=end_date, orbit=orbit, pol=pol
        )

        raw_anomalies = compute_anomaly(
            df=indicator.dataframe,
            df_columns=get_anomaly_columns(indicator.columns_map, dst_cols=columns),
            out_dir=indicator.out_dir,
            orbit=orbit,
            pol=pol,
            spline=False,
        )

        spline_anomalies = compute_anomaly(
            df=indicator.spline_dataframe,
            df_columns=get_anomaly_columns(indicator.columns_map, dst_cols=columns),
            out_dir=indicator.out_dir,
            orbit=orbit,
            pol=pol,
            spline=True,
        )

        stac = StacItems(
            data=raw_anomalies.dataframe,
            geometry=indicator.geometry,
            orbit=indicator.orbit,
            pol=pol,
            out_dir=indicator.out_dir,
        )

        plot_data(
            out_dir=indicator.out_dir,
            name=name,
            raw_data=indicator.dataframe,
            raw_columns=get_anomaly_columns(
                indicator.columns_map, dst_cols=columns
            ),
            anomaly_data=raw_anomalies.dataframe,
            orbit=orbit,
        )

        plot_data(
            out_dir=indicator.out_dir,
            name=name,
            raw_data=indicator.dataframe,
            raw_columns=get_anomaly_columns(
                indicator.columns_map, dst_cols=columns
            ),
            spline_data=indicator.spline_dataframe,
            anomaly_data=spline_anomalies.dataframe,
            orbit=orbit,
        )

        # stac.scenes_to_df()
        # stac.join_with_anomalies()
        # stac.save()

        shutil.move(
            Path(OUT_DIR).joinpath("log_sat4ec.json"),
            indicator.out_dir.joinpath(f"LOG_{indicator.orbit}_{indicator.pol}.json"),
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

    main(
        aoi_data=args.aoi_data,
        start_date=args.start_date,
        end_date=args.end_date,
        pol=pol,
        orbit=orbit,
        name=args.name[0],
        columns=args.columns,
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
        "--name",
        nargs=1,
        help="Name of the location, e.g. BMW Regensburg. Appears in the plot title.",
    )
    parser.add_argument(
        "--columns",
        help="Parameters to plot.",
        choices=["mean", "std", "min", "max"],
        nargs=1,
        default=["mean", "std"],
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
