| credentials | **DO NOT SHARE THIS FILE!** Contains a `.txt` file with SentinelHub credentials. Ignored by the `.gitignore`. |
|-------------|---------------------------------------------------------------------------------------------------------------|
|             |                                                                                                               |

```
sat4ec
├── credentials
│   └── credentials.txt
├
├── docs
│   ├── aoi_bmw_regensburg.png
│   ├── bmw_regensburg_car_zoom.png
│   ├── edc
│   │   └── images
│   │       ├── aoi_wolfsburg.png
│   │       ├── exe_runner.png
│   │       ├── files.png
│   │       ├── files_sat4ec.png
│   │       ├── indicator_1_porsche_leipzig_interpolated_asc_VH.png
│   │       ├── indicator_1_porsche_leipzig_rawdata_monthly_asc_VH.png
│   │       ├── opel_eisenach_202310.png
│   │       ├── output_directories.png
│   │       ├── rawdata_daily.png
│   │       └── rawdata_monthly.png
│   ├── indicator_1_bmw_regensburg_splinedata_asc_VH.png
│   └── tutorial
│       ├── execution.md
│       └── structure.md
├── exe_collection_runner.ipynb
├── exe_runner.ipynb
├── README.md
├── sat4ec_env.yml
├── source
│   ├── anomaly_detection.py
│   ├── aoi_check.py
│   ├── data_retrieval.py
│   ├── execution
│   │   ├── dev
│   │   │   ├── exe_collection_runner.py
│   │   │   ├── exe_runner_from_raw.py
│   │   │   └── exe_runner.py
│   │   ├── exe_config.py
│   │   ├── exe_helper_functions.py
│   │   └── exe_production.py
│   ├── main.py
│   ├── plot_data.py
│   ├── stac.py
│   └── system
│       ├── authentication.py
│       ├── collections.py
│       ├── credentials.yaml
│       └── helper_functions.py
└── tests
    ├── test_anomaly_detection.py
    ├── test_aoi.py
    ├── testdata
    │   ├── input
    │   │   ├── anomalies
    │   │   │   ├── indicator_1_anomalies_raw_monthly_aoi_split_asc_VH.csv
    │   │   │   ├── indicator_1_anomalies_raw_monthly_asc_VH.csv
    │   │   │   ├── indicator_1_anomalies_regression_daily_aoi_split_asc_VH.csv
    │   │   │   └── indicator_1_anomalies_regression_daily_asc_VH.csv
    │   │   ├── AOIs
    │   │   │   ├── empty.geojson
    │   │   │   ├── vw_wolfsburg2subfeatures.geojson
    │   │   │   └── vw_wolfsburg_aoi_split.geojson
    │   │   ├── raw
    │   │   │   ├── indicator_1_rawdata_aoi_split_asc_VH.csv
    │   │   │   ├── indicator_1_rawdata_daily_asc_VH.csv
    │   │   │   ├── indicator_1_rawdata_monthly_aoi_split_asc_VH.csv
    │   │   │   └── indicator_1_rawdata_monthly_asc_VH.csv
    │   │   └── regression
    │   │       ├── indicator_1_linear_daily_aoi_split_asc_VH.csv
    │   │       ├── indicator_1_linear_daily_asc_VH.csv
    │   │       ├── indicator_1_linear_monthly_aoi_split_asc_VH.csv
    │   │       ├── indicator_1_linear_monthly_asc_VH.csv
    │   │       ├── indicator_1_regression_daily_aoi_split_asc_VH.csv
    │   │       └── indicator_1_regression_daily_asc_VH.csv
    │   ├── orbit_input
    │   │   ├── anomalies
    │   │   │   ├── indicator_1_anomalies_raw_monthly_aoi_split_asc_VH.csv
    │   │   │   ├── indicator_1_anomalies_raw_monthly_aoi_split_des_VH.csv
    │   │   │   ├── indicator_1_anomalies_raw_monthly_asc_VH.csv
    │   │   │   ├── indicator_1_anomalies_raw_monthly_des_VH.csv
    │   │   │   ├── indicator_1_anomalies_regression_daily_aoi_split_asc_VH.csv
    │   │   │   ├── indicator_1_anomalies_regression_daily_aoi_split_des_VH.csv
    │   │   │   ├── indicator_1_anomalies_regression_daily_asc_VH.csv
    │   │   │   └── indicator_1_anomalies_regression_daily_des_VH.csv
    │   │   ├── raw
    │   │   │   ├── indicator_1_rawdata_daily_aoi_split_asc_VH.csv
    │   │   │   ├── indicator_1_rawdata_daily_aoi_split_des_VH.csv
    │   │   │   ├── indicator_1_rawdata_daily_asc_VH.csv
    │   │   │   ├── indicator_1_rawdata_daily_des_VH.csv
    │   │   │   ├── indicator_1_rawdata_monthly_aoi_split_asc_VH.csv
    │   │   │   ├── indicator_1_rawdata_monthly_aoi_split_des_VH.csv
    │   │   │   ├── indicator_1_rawdata_monthly_asc_VH.csv
    │   │   │   └── indicator_1_rawdata_monthly_des_VH.csv
    │   │   └── regression
    │   │       ├── indicator_1_linear_daily_aoi_split_asc_VH.csv
    │   │       ├── indicator_1_linear_daily_aoi_split_des_VH.csv
    │   │       ├── indicator_1_linear_daily_asc_VH.csv
    │   │       ├── indicator_1_linear_daily_des_VH.csv
    │   │       ├── indicator_1_linear_monthly_aoi_split_asc_VH.csv
    │   │       ├── indicator_1_linear_monthly_aoi_split_des_VH.csv
    │   │       ├── indicator_1_linear_monthly_asc_VH.csv
    │   │       ├── indicator_1_linear_monthly_des_VH.csv
    │   │       ├── indicator_1_regression_daily_aoi_split_asc_VH.csv
    │   │       ├── indicator_1_regression_daily_aoi_split_des_VH.csv
    │   │       ├── indicator_1_regression_daily_asc_VH.csv
    │   │       └── indicator_1_regression_daily_des_VH.csv
    ├── test_data_retrieval.py
    ├── test_helper_functions.py
    ├── test_plotting.py
    └── test_stac.py
```