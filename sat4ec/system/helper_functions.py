"""Perform linear and non-linear regression on the raw data."""
from datetime import datetime, time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from dateutil.relativedelta import relativedelta
from system.orbit_collections import OrbitCollection as Orbits

ORBIT_COUNT = 2


def mutliple_orbits_raw_range(orbit_collection: Orbits, fid: str = "total") -> pd.DataFrame:
    """Define the plottable range of the raw data."""
    asc_df = pd.DataFrame()
    des_df = pd.DataFrame()

    for orbit in orbit_collection.orbits:
        if orbit == "asc":
            asc_df["asc_mean"] = orbit_collection.asc_subsets.dataframe.loc[:, f"{fid}_mean"]
            asc_df["asc_std"] = orbit_collection.asc_subsets.dataframe.loc[:, f"{fid}_std"]

        else:
            des_df["des_mean"] = orbit_collection.des_subsets.dataframe.loc[:, f"{fid}_mean"]
            des_df["des_std"] = orbit_collection.des_subsets.dataframe.loc[:, f"{fid}_std"]

    if len(orbit_collection.orbits) == ORBIT_COUNT:
        subsets_df = pd.concat([asc_df, des_df], axis=1)
        subsets_df[f"{fid}_mean"] = subsets_df[["asc_mean", "des_mean"]].mean(axis=1)
        subsets_df[f"{fid}_std"] = subsets_df[["asc_std", "des_std"]].mean(axis=1)

    else:
        orbit = orbit_collection.orbits[0]

        subsets_df = asc_df if orbit == "asc" else des_df
        subsets_df[f"{fid}_mean"] = subsets_df.loc[:, f"{orbit}_mean"]
        subsets_df[f"{fid}_std"] = subsets_df.loc[:, f"{orbit}_std"]

    return subsets_df


def get_monthly_keyword(monthly: bool = False) -> str:
    """Determine if computing on semi-daily or monthly data."""
    if monthly:
        return "monthly_"

    return ""


def get_split_keyword(aoi_split: bool = False) -> str:
    """Determine if computing on split or aggregated AOIs."""
    if aoi_split:
        return "split_aoi"

    return "single_aoi"


def get_last_month() -> str:
    """Get last day of last month, e.g. 2024-01-31 if triggering in February 2024."""
    current_date = datetime.now()
    last_month = datetime(current_date.year, current_date.month, 1) + relativedelta(days=-1)

    return datetime.strftime(last_month, "%Y-%m-%d")


def adapt_start_end_time(date: str, start: bool = False, end: bool = False) -> str:
    """Attach hours, minutes and seconds to date.

    Start date must have time part set to 00:00:00.
    End date must have time part set to 23:59:59.
    """
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")

    if start:
        date = datetime.combine(date, time(hour=0, minute=0, second=0))

    if end:
        date = datetime.combine(date, time(hour=23, minute=59, second=59))

    return datetime.strftime(date, "%Y-%m-%dT%H:%M:%SZ")


def date_to_string(date: pd.Timestamp, remove_isoformat_t: bool = True) -> str:
    """Interval dates are in format YYYY-MM-DDT00:00:00Z. Convert to string with YYYY-MM-DD 00:00:00."""
    date = date.isoformat()

    if remove_isoformat_t:
        date = date.replace("T", " ")

    return date


def create_out_dir(base_dir: Path, out_dir: str = "") -> None:
    """Create output directory if not existing."""
    if not base_dir.joinpath(out_dir).exists():
        base_dir.joinpath(out_dir).mkdir(parents=True)


def convert_dataframe_tz(var: pd.DatetimeIndex | pd.Timestamp) -> pd.DatetimeIndex:
    """Set timezone info."""
    if isinstance(var, pd.DatetimeIndex | pd.Timestamp):
        var = var.tz_localize("UTC") if var.tzinfo is None else var.tz_convert("UTC")

    return var


def remove_dataframe_nan_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove NaN rows from dataframe."""
    return df[np.isfinite(df).all(1)]


def load_yaml(yaml_path: Path) -> dict:
    """Load a YAML file."""
    with Path.open(yaml_path, "r") as f:
        return yaml.safe_load(f)
