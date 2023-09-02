import shutil
import subprocess
import pandas as pd
from pathlib import Path

from sat4ec.data_retrieval import IndicatorData as IData
from sat4ec.aoi_check import AOI
from anomaly_detection import Anomaly
from plot_data import PlotData
from system.helper_functions import get_anomaly_columns


def get_name(name=None):
    brand = name.split("_")[0]
    location = name.split("_")[1]

    if len(name.split("_")) > 2:
        raise ValueError(f"The name of the AOI {name} does not follow scheme BRAND_LOCATION.")

    else:
        return f"{brand.upper()}_{location.title()}"


def get_indicator(
    aoi=None,
    out_dir=None,
    start_date="2020-01-01",
    end_date="2020-12-31",
    orbit="asc",
    pol="VH",
):
    indicator = IData(
        aoi=aoi,
        out_dir=out_dir,
        start_date=start_date,
        end_date=end_date,
        orbit=orbit,
        pol=pol,
    )
    indicator.dataframe = pd.read_csv(
        out_dir.joinpath("raw", f"indicator_1_rawdata_{orbit}_VH.csv")
    )
    indicator.dataframe["interval_from"] = pd.to_datetime(
        indicator.dataframe["interval_from"]
    )
    indicator.dataframe = indicator.dataframe.set_index("interval_from")

    indicator.apply_regression()
    indicator.save(spline=True)

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


def plot_data(spline=False, out_dir=None, name=None, raw_data=None, raw_columns=None, spline_data=None, anomaly_data=None, orbit="asc"):
    if spline:
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
            plotting.save(spline=spline)

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
            plotting.save(spline=spline)


def entire_workflow(
    orbits=None,
    pols=None,
    aois=None,
    working_dir=None,
    start="2020-01-01",
    end="2020-12-31",
):
    for key in aois.keys():
        for orbit in orbits:
            for pol in pols:
                shutil.copy(aois[key], working_dir)

                response = subprocess.run(
                    [
                        "python3",
                        "../sat4ec/main.py",
                        "--aoi_data",
                        str(working_dir.joinpath(aois[key].name)),
                        "--start_date",
                        f"{start}",
                        "--end_date",
                        f"{end}",
                        "--orbit",
                        orbit,
                        "--polarization",
                        pol,
                    ],
                    capture_output=False,
                )

        if working_dir.joinpath(key).exists():
            for item in working_dir.joinpath(key).glob("*"):
                for _file in item.glob("*"):  # delete files per orbit directory
                    _file.unlink()

                if item.is_dir():
                    shutil.rmtree(item)  # delete orbit directory

                if item.is_file():
                    item.unlink()

            shutil.rmtree(working_dir.joinpath(key))  # delete obsolete directory

        working_dir.joinpath("results").rename(working_dir.joinpath(key))
        working_dir.joinpath(aois[key].name).unlink()


def from_raw_data(
    orbits=None,
    pols=None,
    aois=None,
    working_dir=None,
    start="2020-01-01",
    end="2020-12-31",
):
    for key in aois.keys():
        aoi_dir = working_dir.joinpath(key)

        for orbit in orbits:
            for pol in pols:
                shutil.copy(aois[key], aoi_dir)

                with AOI(data=aoi_dir.joinpath(aois[key].name)) as aoi:
                    aoi.get_features()

                    indicator = get_indicator(
                        aoi=aoi.geometry,
                        out_dir=aoi_dir,
                        start_date=start,
                        end_date=end,
                        orbit=orbit,
                        pol=pol,
                    )

                    raw_anomalies = compute_anomaly(
                        df=indicator.dataframe,
                        df_columns=get_anomaly_columns(indicator.columns_map),
                        out_dir=indicator.out_dir,
                        orbit=orbit,
                        pol=pol,
                        spline=False,
                    )

                    spline_anomalies = compute_anomaly(
                        df=indicator.spline_dataframe,
                        df_columns=get_anomaly_columns(indicator.columns_map),
                        out_dir=indicator.out_dir,
                        orbit=orbit,
                        pol=pol,
                        spline=True,
                    )

                    plot_data(
                        out_dir=indicator.out_dir,
                        name=get_name(key),
                        raw_data=indicator.dataframe,
                        raw_columns=get_anomaly_columns(indicator.columns_map, dst_cols=["mean", "std"]),
                        anomaly_data=raw_anomalies.dataframe,
                        orbit=orbit,
                    )

                    plot_data(
                        out_dir=indicator.out_dir,
                        name=get_name(key),
                        raw_data=indicator.dataframe,
                        raw_columns=get_anomaly_columns(indicator.columns_map, dst_cols=["mean", "std"]),
                        spline_data=indicator.spline_dataframe,
                        anomaly_data=spline_anomalies.dataframe,
                        orbit=orbit,
                    )


def main(
    orbits=None,
    pols=None,
    aois=None,
    aoi_dir=None,
    start="2020-01-01",
    end="2020-12-31",
):
    working_dir = aoi_dir.parent
    # entire_workflow(
    #     orbits=orbits,
    #     pols=pols,
    #     aois=aois,
    #     working_dir=working_dir,
    #     start=start,
    #     end=end,
    # )
    from_raw_data(
        orbits=orbits,
        pols=pols,
        aois=aois,
        working_dir=working_dir,
        start=start,
        end=end,
    )


if __name__ == "__main__":
    aoi_dir = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata/AOIs")
    orbits = ["asc", "des"]

    pols = [
        # "VV",
        "VH"
    ]

    aois = {
        "volvo_gent": aoi_dir.joinpath("volvo_gent.geojson"),
        "munich_airport": aoi_dir.joinpath("munich_airport.geojson"),
        "munich_ikea": aoi_dir.joinpath("munich_ikea.geojson"),
        "bmw_leipzig": aoi_dir.joinpath("bmw_leipzig.geojson"),
        "vw_emden": aoi_dir.joinpath("vw_emden.geojson"),
        "bmw_regensburg": aoi_dir.joinpath("bmw_regensburg.geojson"),
    }

    main(orbits, pols, aois, aoi_dir, start="2016-01-01", end="2022-12-31")
