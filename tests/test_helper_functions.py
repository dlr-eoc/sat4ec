import pandas as pd


def prepare_test_dataframes(data_dir=None):
    raw_data = pd.read_csv(data_dir.joinpath("raw", "indicator_1_rawdata_asc_VH.csv"))
    raw_monthly_data = pd.read_csv(
        data_dir.joinpath("raw", "indicator_1_rawdata_monthly_asc_VH.csv")
    )
    reg_data = pd.read_csv(
        data_dir.joinpath("regression", "indicator_1_spline_asc_VH.csv")
    )
    reg_anomaly_data = pd.read_csv(
        data_dir.joinpath("anomalies", "indicator_1_anomalies_interpolated_asc_VH.csv")
    )
    raw_anomaly_data = pd.read_csv(
        data_dir.joinpath("anomalies", "indicator_1_anomalies_raw_monthly_asc_VH.csv")
    )
    linear_data = pd.read_csv(
        data_dir.joinpath("regression", "indicator_1_linear_asc_VH.csv")
    )
    linear_monthly_data = pd.read_csv(
        data_dir.joinpath("regression", "indicator_1_linear_monthly_asc_VH.csv")
    )

    raw_data.loc[:, "interval_from"] = pd.to_datetime(raw_data["interval_from"])
    raw_monthly_data.loc[:, "interval_from"] = pd.to_datetime(
        raw_monthly_data["interval_from"]
    )
    reg_data.loc[:, "interval_from"] = pd.to_datetime(reg_data["interval_from"])
    reg_anomaly_data.loc[:, "interval_from"] = pd.to_datetime(
        reg_anomaly_data["interval_from"]
    )
    raw_anomaly_data.loc[:, "interval_from"] = pd.to_datetime(
        raw_anomaly_data["interval_from"]
    )
    linear_data.loc[:, "interval_from"] = pd.to_datetime(linear_data["interval_from"])
    linear_monthly_data.loc[:, "interval_from"] = pd.to_datetime(linear_monthly_data["interval_from"])

    raw_data = raw_data.set_index("interval_from")
    raw_monthly_data = raw_monthly_data.set_index("interval_from")
    reg_data = reg_data.set_index("interval_from")
    reg_anomaly_data = reg_anomaly_data.set_index("interval_from")
    raw_anomaly_data = raw_anomaly_data.set_index("interval_from")
    linear_data = linear_data.set_index("interval_from")
    linear_monthly_data = linear_monthly_data.set_index("interval_from")

    return (
        raw_data,
        raw_monthly_data,
        reg_data,
        reg_anomaly_data,
        raw_anomaly_data,
        linear_data,
        linear_monthly_data,
    )
