"""Retrieve Sentinel-1 image chips for certain dates."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sentinelhub import DataCollection, Geometry, SentinelHubCatalog
from system.authentication import Config
from system.helper_functions import get_monthly_keyword


class StacCollection:
    """Encapsulate methods to retrieve Sentinel-1 scenes."""

    def __init__(
        self: StacCollection,
        data: pd.DataFrame | Path | str,
        features: list | None = None,
        out_dir: Path | None = None,
        geometries: list | None = None,
        orbit: str = "asc",
        pol: str = "VH",
        monthly: bool = False,
    ) -> None:
        """Initialize StacCollection class."""
        self.features = features
        self.geometries = geometries
        self.orbit = orbit
        self.pol = pol
        self.out_dir = out_dir
        self.monthly = monthly
        self.anomalies_df = None
        self.dataframe = pd.DataFrame()

        self._get_data(data=data)

    def _get_data(self: StacCollection, data: Path | str | pd.DataFrame) -> None:
        if isinstance(data, Path):
            self.anomalies_df = self._load_df(data)

        elif isinstance(data, str):
            if Path(data).exists():
                self.anomalies_df = self._load_df(Path(data))

        else:  # data is of type pd.DataFrame
            self.anomalies_df = data

    @staticmethod
    def _load_df(filename: Path) -> pd.DataFrame:
        """Load dataframe from file."""
        df = pd.read_csv(filename)
        df["interval_from"] = pd.to_datetime(df["interval_from"])

        return df.set_index("interval_from")  # required to find scenes at DateTimeIndex

    def init_dataframe(self: StacCollection, df: pd.DataFrame) -> None:
        """Initialize a dataframe copy."""
        self.dataframe = df.copy()

    def add_stac_item(self: StacCollection, df: pd.DataFrame) -> None:
        """Merge dataframes."""
        self.dataframe = self.dataframe.merge(df, how="outer")

    def get_stac_collection(self: StacCollection) -> None:
        """Get STAC collection for the selected AOIs."""
        for index, (feature, geometry) in enumerate(zip(self.features, self.geometries, strict=False)):
            stac = StacItems(
                anomalies_df=self.anomalies_df.loc[self.anomalies_df[f"{feature.fid}_anomaly"]],
                fid=feature.fid,
                geometry=geometry,
            )

            stac.scenes_to_df()
            stac.join_with_anomalies()

            if index == 0:
                self.init_dataframe(df=stac.dataframe)

            else:
                self.add_stac_item(df=stac.dataframe)

        self.delete_columns()
        self.sort_columns()
        self.save()

    def delete_columns(self: StacCollection, columns: tuple[str, str] = ("mean", "std")) -> None:
        """Delete dataframe columns."""
        self.dataframe = self.dataframe.loc[:, ~self.dataframe.columns.str.endswith(columns)]

    def sort_columns(self: StacCollection) -> None:
        """Sort dataframe columns."""
        self.dataframe = self.dataframe[["interval_from"], *sorted(self.dataframe.columns[1:])]

    def save(self: StacCollection) -> None:
        """Save dataframe with Sentinel-1 scene names."""
        out_file = self.out_dir.joinpath(
            "scenes",
            f"indicator_1_scenes_{get_monthly_keyword(monthly=self.monthly)}{self.orbit}_{self.pol}.csv",
        )
        self.dataframe.to_csv(out_file, decimal=".")


class StacItems(Config):
    """Encapsulate methods to retrieve Sentinel-1 data for one AOI."""

    def __init__(
        self: StacItems,
        anomalies_df: pd.DataFrame,
        fid: str,
        geometry: Geometry,
    ) -> None:
        """Initialize SatcItems class."""
        super().__init__()

        self.config = None
        self.catalog = None
        self.dataframe = None  # output
        self.anomalies_df = anomalies_df
        self.fid = fid
        self.geometry = geometry

        self._get_catalog()
        self._get_collection()

    def _get_catalog(self: StacItems) -> None:
        """Get Sentinel-1 catalog."""
        self.catalog = SentinelHubCatalog(config=self.config)

    def _get_collection(self: StacItems) -> None:
        """Get Sentinel-1 collection."""
        self.catalog.get_collection(DataCollection.SENTINEL1)

    def join_with_anomalies(self: StacItems) -> None:
        """Connect Sentinel-1 scenes with detected anomalies."""
        if isinstance(self.anomalies_df.index, pd.DatetimeIndex):
            if self.anomalies_df.index.tzinfo is None:
                self.anomalies_df.index = self.anomalies_df.index.tz_localize("UTC")

            else:
                self.anomalies_df.index = self.anomalies_df.index.tz_convert("UTC")

            self.anomalies_df.insert(0, "tmp", self.anomalies_df.index.to_series())
            self.anomalies_df = self.anomalies_df.reset_index(drop=True)
            self.anomalies_df = self.anomalies_df.rename(columns={"tmp": "interval_from"})

            # remove any Unnamed column
            self.anomalies_df = self.anomalies_df.loc[:, ~self.anomalies_df.columns.str.contains("^Unnamed")]

        true_anomalies = self.anomalies_df.loc[self.anomalies_df[f"{self.fid}_anomaly"]]  # True at these indices

        self.dataframe = pd.merge(self.dataframe, true_anomalies, on="interval_from", how="inner")
        self.dataframe = self.dataframe.drop(f"{self.fid}_anomaly", axis=1)

    def get_scenes(self: StacItems) -> list:
        """Get a list of Sentinel-1 scenes."""
        return [self.search_catalog(row) for row in range(len(self.anomalies_df))]

    def scenes_to_df(self: StacItems) -> None:
        """Transfer scenes from catalog into dataframe."""
        catalog = self.get_scenes()

        self.dataframe = pd.DataFrame(
            {
                "interval_from": [scene["datetime"].iloc[0] for scene in catalog],
                f"{self.fid}_scene": [scene["id"].iloc[0] for scene in catalog],
            }
        )

    def search_catalog(self: StacItems, row: int) -> pd.DataFrame:
        """Search Sentinel Hub catalog for scenes at anomaly dates."""
        date = self.anomalies_df.iloc[row].name

        search_iterator = self.catalog.search(
            DataCollection.SENTINEL1,
            geometry=self.geometry,
            time=(date - pd.Timedelta(days=12), date + pd.Timedelta(days=12)),  # start date  # end date
            fields={"include": ["id", "properties.datetime"], "exclude": []},
        )

        df = self.get_closest_date(self.catalog_to_dataframe(search_iterator), date=date)
        df.index = df.index.normalize()

        return df.reset_index()

    @staticmethod
    def catalog_to_dataframe(catalog: list) -> pd.DataFrame:
        """Retrieve items from catalog and store in dataframe."""
        df = pd.DataFrame(
            [{"id": item["id"], "datetime": pd.to_datetime(item["properties"]["datetime"])} for item in catalog]
        )
        df = df.drop_duplicates(subset=["datetime"], ignore_index=True)

        return df.set_index("datetime")

    @staticmethod
    def get_closest_date(df: pd.DataFrame, date: str) -> pd.DataFrame:
        """Find closest date of Sentinel-1 observation."""
        return df.iloc[df.index.get_indexer([pd.to_datetime(date, utc=True)], method="nearest")]
