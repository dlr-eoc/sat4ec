import datetime as dt
import os

from matplotlib import mlab
from shapely import geometry, wkt

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

from sentinelhub import (
    CRS,
    BBox,
    DataCollection,
    Geometry,
    SentinelHubStatistical,
    SentinelHubStatisticalDownloadClient,
    SHConfig,
    parse_time,
    geometry,
    SentinelHubCatalog,
    bbox_to_dimensions,
)

sh_client_id = ""
sh_client_secret = ""

if not sh_client_id:
    sh_client_id = os.environ["SH_CLIENT_ID"]

if not sh_client_secret:
    sh_client_secret = os.environ["SH_CLIENT_SECRET"]

if not sh_client_id or not sh_client_secret:
    raise ValueError("No valid Sentinel HUB credentials are available. Plese contact system administrator.")

config = SHConfig()

config.sh_client_id = sh_client_id
config.sh_client_secret = sh_client_secret

# OUTPUT_DIR = os.path.join(USR_PATH, "output") #local folder
OUTPUT_DIR = "/home/jovyan/result-data/e8"  # will be copied to the local folder of the user requesting the data


# helper function

def stats_to_df(stats_data):
    """Transform Statistical API response into a pandas.DataFrame"""
    df_data = []

    for single_data in stats_data["data"]:
        df_entry = {}
        is_valid_entry = True

        df_entry["interval_from"] = parse_time(single_data["interval"]["from"]).date()
        df_entry["interval_to"] = parse_time(single_data["interval"]["to"]).date()

        for output_name, output_data in single_data["outputs"].items():
            for band_name, band_values in output_data["bands"].items():

                band_stats = band_values["stats"]
                if band_stats["sampleCount"] == band_stats["noDataCount"]:
                    is_valid_entry = False
                    break

                for stat_name, value in band_stats.items():
                    col_name = f"{output_name}_{band_name}_{stat_name}"
                    if stat_name == "percentiles":
                        for perc, perc_val in value.items():
                            perc_col_name = f"{col_name}_{perc}"
                            df_entry[perc_col_name] = perc_val
                    else:
                        df_entry[col_name] = value

        if is_valid_entry:
            df_data.append(df_entry)

    return pd.DataFrame(df_data)


if __name__ == "__main__":
    aoi = "POLYGON ((3.754824 51.096633, \
                  3.753451 51.096242, \
                  3.755747 51.093102, \
                  3.755661 51.09511, \
                  3.755211 51.094989, \
                  3.754953 51.095393, \
                  3.755211 51.09608, \
                  3.755125 51.0967, \
                  3.755447 51.097953, \
                  3.755168 51.098048, \
                  3.755009 51.097886, \
                  3.754116 51.097697, \
                  3.754824 51.096633))"

    time_period = "2022-11-01/2022-11-10"

    orbit = "ASC"

    from_to = time_period.split("/")

    interval = (f'{from_to[0]}T00:00:00Z', f'{from_to[1]}T23:59:59Z')

    print(f'interval: {interval}')

    geometry = Geometry(aoi, crs=CRS.WGS84)

    print(geometry)

    size = bbox_to_dimensions(geometry.bbox, resolution=5)

    print(f'size: {size}')

    if not orbit:
        orbit = "ASC"

    collection = DataCollection.SENTINEL1_IW_ASC if orbit == "ASC" else DataCollection.SENTINEL1_IW_DES

    print(f'collection: {collection}')


    # evalscript (unit: dB)
    evalscript_db = """
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
    request = SentinelHubStatistical(
        aggregation=SentinelHubStatistical.aggregation(
            evalscript=evalscript_db,
            time_interval=interval,
            aggregation_interval='P1D',
            size=size
        ),
        input_data=[
            SentinelHubStatistical.input_data(
                collection,
                other_args={"dataFilter": {"mosaickingOrder": "mostRecent", "resolution": "HIGH"},
                            "processing": {"orthorectify": "True", "backCoeff": "SIGMA0_ELLIPSOID",
                                           "demInstance": "COPERNICUS"}},
            ),
        ],
        geometry=geometry,
        config=config
    )


    # % % time

    stats = request.get_data()[0]


    # convert statistical data to pandas dataframe
    data_frame = stats_to_df(stats)


    # Change 'interval_from' and 'interval_to' to datetime
    data_frame.loc[:, 'interval_from'] = pd.to_datetime(data_frame['interval_from'])
    data_frame.loc[:, 'interval_to'] = pd.to_datetime(data_frame['interval_to'])

    day_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    final_dir = os.path.join(OUTPUT_DIR, datetime.now().strftime("%Y_%m_%d"))
    file = os.path.join(final_dir, f'e8_indicator_{day_time}.csv')

    os.makedirs(final_dir, exist_ok=True)
    # Import CSV from git
    data_frame.to_csv(file)
