"""Open and prepare dataframes for testing."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pandas as pd


def prepare_test_dataframes(
    data_dir: Path | None = None, aoi_split: bool = False, orbit: str = "asc"
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame,]:
    """Open and prepare dataframes for testing."""
    if aoi_split:
        raw_data = pd.read_csv(data_dir.joinpath("raw", f"indicator_1_rawdata_split_aoi_{orbit}_VH.csv"))
        raw_monthly_data = pd.read_csv(
            data_dir.joinpath("raw", f"indicator_1_rawdata_split_aoi_monthly_{orbit}_VH.csv")
        )
        reg_data = pd.read_csv(
            data_dir.joinpath("regression", "spline", f"indicator_1_split_aoi_spline_{orbit}_VH.csv")
        )
        linear_data = pd.read_csv(data_dir.joinpath("regression", f"linearindicator_1_linear_split_aoi_{orbit}_VH.csv"))
        linear_monthly_data = pd.read_csv(
            data_dir.joinpath("regression", f"linearindicator_1_linear_split_aoi_monthly_{orbit}_VH.csv")
        )
        reg_anomaly_data = pd.read_csv(
            data_dir.joinpath(
                "anomalies",
                f"indicator_1_anomalies_regression_split_aoi_{orbit}_VH.csv",
            )
        )
        raw_monthly_anomaly_data = pd.read_csv(
            data_dir.joinpath(
                "anomalies",
                f"indicator_1_anomalies_raw_monthly_aoi_split_{orbit}_VH.csv",
            )
        )

    else:
        raw_data = pd.read_csv(data_dir.joinpath("raw", f"indicator_1_rawdata_single_aoi_{orbit}_VH.csv"))
        raw_monthly_data = pd.read_csv(
            data_dir.joinpath("raw", f"indicator_1_rawdata_single_aoi_monthly_{orbit}_VH.csv")
        )
        reg_data = pd.read_csv(
            data_dir.joinpath("regression", "spline", f"indicator_1_single_aoi_spline_{orbit}_VH.csv")
        )
        linear_data = pd.read_csv(
            data_dir.joinpath("regression", f"linearindicator_1_linear_single_aoi_{orbit}_VH.csv")
        )
        linear_monthly_data = pd.read_csv(
            data_dir.joinpath("regression", f"linearindicator_1_linear_single_aoi_monthly_{orbit}_VH.csv")
        )
        reg_anomaly_data = pd.read_csv(
            data_dir.joinpath("anomalies", f"indicator_1_anomalies_regression_single_aoi_{orbit}_VH.csv")
        )
        raw_monthly_anomaly_data = pd.read_csv(
            data_dir.joinpath("anomalies", f"indicator_1_anomalies_raw_single_aoi_monthly_{orbit}_VH.csv")
        )

    raw_data.loc[:, "interval_from"] = pd.to_datetime(raw_data["interval_from"])
    raw_monthly_data.loc[:, "interval_from"] = pd.to_datetime(raw_monthly_data["interval_from"])
    reg_data.loc[:, "interval_from"] = pd.to_datetime(reg_data["interval_from"])
    reg_anomaly_data.loc[:, "interval_from"] = pd.to_datetime(reg_anomaly_data["interval_from"])
    raw_monthly_anomaly_data.loc[:, "interval_from"] = pd.to_datetime(raw_monthly_anomaly_data["interval_from"])
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
