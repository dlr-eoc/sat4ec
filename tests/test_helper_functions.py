import pandas as pd


def prepare_test_dataframes(data_dir=None, aoi_split=False, orbit="asc"):
    if aoi_split:
        raw_data = pd.read_csv(data_dir.joinpath("raw", f"indicator_1_rawdata_aoi_split_asc_VH.csv"))
        raw_monthly_data = pd.read_csv(
            data_dir.joinpath("raw", f"indicator_1_rawdata_monthly_aoi_split_asc_VH.csv")
        )
        reg_data = pd.read_csv(
            data_dir.joinpath("regression", f"indicator_1_regression_daily_aoi_split_asc_VH.csv")
        )
        linear_data = pd.read_csv(
            data_dir.joinpath("regression", f"indicator_1_linear_daily_aoi_split_asc_VH.csv")
        )
        linear_monthly_data = pd.read_csv(
            data_dir.joinpath("regression", f"indicator_1_linear_monthly_aoi_split_asc_VH.csv")
        )
        reg_anomaly_data = pd.read_csv(
            data_dir.joinpath("anomalies", f"indicator_1_anomalies_regression_aoi_split_asc_VH.csv")
        )
        raw_monthly_anomaly_data = pd.read_csv(
            data_dir.joinpath("anomalies", f"indicator_1_anomalies_raw_monthly_aoi_split_asc_VH.csv")
        )

    else:
        raw_data = pd.read_csv(data_dir.joinpath("raw", f"indicator_1_rawdata_daily_{orbit}_VH.csv"))
        raw_monthly_data = pd.read_csv(
            data_dir.joinpath("raw", f"indicator_1_rawdata_monthly_{orbit}_VH.csv")
        )
        reg_data = pd.read_csv(
            data_dir.joinpath("regression", f"indicator_1_regression_daily_{orbit}_VH.csv")
        )
        linear_data = pd.read_csv(
            data_dir.joinpath("regression", f"indicator_1_linear_daily_{orbit}_VH.csv")
        )
        linear_monthly_data = pd.read_csv(
            data_dir.joinpath("regression", f"indicator_1_linear_monthly_{orbit}_VH.csv")
        )
        reg_anomaly_data = pd.read_csv(
            data_dir.joinpath("anomalies", f"indicator_1_anomalies_regression_daily_{orbit}_VH.csv")
        )
        raw_monthly_anomaly_data = pd.read_csv(
            data_dir.joinpath("anomalies", f"indicator_1_anomalies_raw_monthly_{orbit}_VH.csv")
        )

    raw_data.loc[:, "interval_from"] = pd.to_datetime(raw_data["interval_from"])
    raw_monthly_data.loc[:, "interval_from"] = pd.to_datetime(
        raw_monthly_data["interval_from"]
    )
    reg_data.loc[:, "interval_from"] = pd.to_datetime(reg_data["interval_from"])
    reg_anomaly_data.loc[:, "interval_from"] = pd.to_datetime(
        reg_anomaly_data["interval_from"]
    )
    raw_monthly_anomaly_data.loc[:, "interval_from"] = pd.to_datetime(
        raw_monthly_anomaly_data["interval_from"]
    )
    linear_data.loc[:, "interval_from"] = pd.to_datetime(linear_data["interval_from"])
    linear_monthly_data.loc[:, "interval_from"] = pd.to_datetime(linear_monthly_data["interval_from"])

    raw_data = raw_data.set_index("interval_from")
    raw_monthly_data = raw_monthly_data.set_index("interval_from")
    reg_data = reg_data.set_index("interval_from")
    reg_anomaly_data = reg_anomaly_data.set_index("interval_from")
    raw_monthly_anomaly_data = raw_monthly_anomaly_data.set_index("interval_from")
    linear_data = linear_data.set_index("interval_from")
    linear_monthly_data = linear_monthly_data.set_index("interval_from")

    return (
        raw_data,
        raw_monthly_data,
        reg_data,
        reg_anomaly_data,
        raw_monthly_anomaly_data,
        linear_data,
        linear_monthly_data,
    )
