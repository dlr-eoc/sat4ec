### Inspecting results

Results will be saved per AOI to the specified output directory, per default located under `sat4ec/output`. Results are categorized into directories as follows:

| Directory  | Description                                                                        |
|------------|------------------------------------------------------------------------------------|
| anomalies  | Contains a CSV file per orbit with information on anomalies                        |
| plot       | Contains PNG files with plotted results                                            |
| raw        | Contains a CSV file per orbit with raw data                                        |
| regression | Contains a CSV file per orbit with regressed data                                  |
| scenes     | Contains a CSV file per orbit with names of Sentinel-1 scenes at anomal timestamps |

#### Raw data

CSV raw data looks as follows:

| interval_from             | interval_to               | 0_min      | 0_max      | 0_mean     | 0_std     | 0_sample_count | 0_nodata_count |
|---------------------------|---------------------------|------------|------------|------------|-----------|----------------|----------------|
| 2014-10-13 00:00:00+00:00 | 2014-10-14 00:00:00+00:00 | -22.138102 | -12.733138 | -17.364601 | 1.9985918 | 336            | 42             |
| 2014-10-25 00:00:00+00:00 | 2014-10-26 00:00:00+00:00 | -21.990717 | -14.023947 | -17.357225 | 1.8950151 | 336            | 42             |

The column `0_mean` and any further column in this example with the prefix `0` contains the results for the AOI feature with the feature ID `0`. If the AOI consists of multiple sub AOIS, each of them will be declared with a prefix and described in this table with the presented scheme. At the end of the table, columns in the same scheme will be placed with results of all sub AOIs aggegated into a single AOI with the prefix `total`, i.e. `total_mean`. The aggregated results will be computed as follows:

| Column       | Operation                               |
|--------------|-----------------------------------------|
| mean         | Mean of all sub AOI means               |
| std          | Mean of all sub AOI standard deviations |
| min          | Minimum of all sub AOI minima           |
| max          | Maximum of all sub AOI maxima           |
| sample_count | Sum of all sub AOI sample counts        |
| nodata_count | Sum of all sub AOI nodata counts        |

In the following, only `mean` and `std` will be used to derive information from the raw data.

#### Regression data

CSV regression data looks as follows:

| interval_from             | 0_mean              | 0_std              |
|---------------------------|---------------------|--------------------|
| 2014-10-13 00:00:00+00:00 | -17.364601          | 2.0650163064380194 |
| 2014-10-25 00:00:00+00:00 | -17.060163186323905 | 2.0671377074435457 |

The regression function specified in the runner will be applied to the raw data `mean` and `std`. As default, the spline regression function will be used. The regression function will be applied only to semi-daily, not monthly, data.

The directory also contains CSV files with linear regression data. Linear regression is applied both to semi-daily and monthly data and of important use for the anomaly detection.

#### Anomaly data

CSV anomaly data looks as follows:

| interval_from             | 0_anomaly | 0_mean              | 0_std              |
|---------------------------|-----------|---------------------|--------------------|
| 2014-10-13 00:00:00+00:00 | False     | -17.364601          | 2.0650163064380194 |
| 2014-10-25 00:00:00+00:00 | True      | -17.060163186323905 | 2.0671377074435457 |

If computing on semi-daily data, anomalies will be detected on regression data. If computing on monthly data, anomalies will be detected on raw data. Please keep in mind, that the linear regression data defines an insensitive range where no anomalies will be detected.

#### Scene data

CSV scene data looks as follows:

| interval_from             | 0_scene                                                             | 1_scene                                                             |
|---------------------------|---------------------------------------------------------------------|---------------------------------------------------------------------|
| 2016-07-17 00:00:00+00:00 | S1A_IW_GRDH_1SDV_20160717T165919_20160717T165944_012191_012E98_CB71 |                                                                     |
| 2016-09-08 00:00:00+00:00 | S1A_IW_GRDH_1SDV_20160908T170733_20160908T170758_012964_014825_1F5D | S1A_IW_GRDH_1SDV_20160908T170733_20160908T170758_012964_014825_1F5D |

This data contains the name of every anomal Sentinel-1 scene for a given (sub) AOI and timestamp. If no Sentinel-1 scene could be aqcuired for that timestamp, most likely because the data is not anomal, the field will be empty.

#### Plots

Plotted results look as follows:

![BMW Regensburg](../doc_images/bmw_regensburg_monthly_plot.png)