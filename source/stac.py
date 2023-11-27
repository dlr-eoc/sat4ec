import pandas as pd
import pytz
import dateutil

from system.authentication import Config
from sentinelhub import DataCollection, SentinelHubCatalog
from pathlib import Path


class StacCollection:
    def __init__(
        self,
        data=None,
        features=None,
        geometries=None,
        orbit="asc",
        pol="VH",
        out_dir=None,
    ):
        self.features = features
        self.geometries = geometries
        self.orbit = orbit
        self.pol = pol
        self.out_dir = out_dir

        self.anomalies_df = self._get_data(data=data)
        self.dataframe = pd.DataFrame()

    def _get_data(self, data):
        if isinstance(data, Path):
            return self._load_df(data)

        elif isinstance(data, str):
            if Path(data).exists():
                return self._load_df(Path(data))

        elif isinstance(data, pd.DataFrame):
            return data

        else:
            return None

    @staticmethod
    def _load_df(filename):
        df = pd.read_csv(filename)
        df["interval_from"] = pd.to_datetime(df["interval_from"])
        df = df.set_index("interval_from")  # required to find scenes at DateTimeIndex

        return df

    def init_dataframe(self, df=None):
        self.dataframe = df.copy()

    def add_stac_item(self, df=None):
        self.dataframe = self.dataframe.merge(df, how="outer")

    def get_stac_collection(self):
        for index, (feature, geometry) in enumerate(
            zip(self.features, self.geometries)
        ):
            stac = StacItems(
                anomalies_df=self.anomalies_df.loc[
                    self.anomalies_df[f"{feature.fid}_anomaly"]
                ],
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
        self.save()

    def delete_columns(self, columns=("mean", "std")):
        self.dataframe = self.dataframe.loc[
            :, ~self.dataframe.columns.str.endswith(columns)
        ]

    def save(self):
        out_file = self.out_dir.joinpath(
            "scenes",
            f"indicator_1_scenes_{self.orbit}_{self.pol}.csv",
        )

        self.dataframe.to_csv(out_file, decimal=".")


class StacItems(Config):
    def __init__(
        self,
        anomalies_df=None,
        fid=None,
        geometry=None,
    ):
        super().__init__()

        self.catalog = None
        self.dataframe = None  # output
        self.anomalies_df = anomalies_df
        self.fid = fid
        self.geometry = geometry

        self._get_catalog()
        self._get_collection()

    def _get_catalog(self):
        self.catalog = SentinelHubCatalog(config=self.config)

    def _get_collection(self):
        self.catalog.get_collection(DataCollection.SENTINEL1)

    def join_with_anomalies(self):
        if isinstance(self.anomalies_df.index, pd.DatetimeIndex):
            if self.anomalies_df.index.tzinfo is None:
                self.anomalies_df.index = self.anomalies_df.index.tz_localize("UTC")

            else:
                self.anomalies_df.index = self.anomalies_df.index.tz_convert("UTC")

            self.anomalies_df.insert(0, "tmp", self.anomalies_df.index.to_series())
            self.anomalies_df = self.anomalies_df.reset_index(drop=True)
            self.anomalies_df = self.anomalies_df.rename(
                columns={"tmp": "interval_from"}
            )

            # remove any Unnamed column
            self.anomalies_df = self.anomalies_df.loc[:, ~self.anomalies_df.columns.str.contains("^Unnamed")]

        true_anomalies = self.anomalies_df.loc[
            self.anomalies_df[f"{self.fid}_anomaly"]
        ]  # True at these indices

        self.dataframe = pd.merge(self.dataframe, true_anomalies, on="interval_from", how="inner")
        self.dataframe = self.dataframe.drop(f"{self.fid}_anomaly", axis=1)

    def get_scenes(self):
        return [self.search_catalog(row) for row in range(len(self.anomalies_df))]

    def scenes_to_df(self):
        catalog = self.get_scenes()

        self.dataframe = pd.DataFrame(
            {
                "interval_from": [
                    scene["datetime"].iloc[0] for scene in catalog
                ],
                f"{self.fid}_scene": [
                    scene["id"].iloc[0] for scene in catalog
                ],
            }
        )

    def remove_datetime_index(self):
        if isinstance(self.dataframe.index, pd.DatetimeIndex):
            self.dataframe.insert(0, "tmp", self.dataframe.index.to_series())
            self.dataframe = self.dataframe.reset_index(drop=True)
            self.dataframe = self.dataframe.rename(columns={"tmp": "interval_from"})

    def search_catalog(self, row):
        date = self.anomalies_df.iloc[row].name

        search_iterator = self.catalog.search(
            DataCollection.SENTINEL1,
            geometry=self.geometry,
            time=(
                date - pd.Timedelta(days=12),  # start date
                date + pd.Timedelta(days=12)  # end date
            ),
            fields={"include": ["id", "properties.datetime"], "exclude": []},
        )

        df = self.get_closest_date(self.catalog_to_dataframe(search_iterator), date=date)
        df.index = df.index.normalize()
        df = df.reset_index()

        return df

    @staticmethod
    def catalog_to_dataframe(catalog=None):
        df = pd.DataFrame(
            [
                {
                    "id": item["id"],
                    "datetime": pd.to_datetime(item["properties"]["datetime"])
                } for item in catalog]
        )
        df = df.drop_duplicates(subset=["datetime"], ignore_index=True)
        df = df.set_index("datetime")

        return df

    @staticmethod
    def get_closest_date(df=None, date=None):
        return df.iloc[df.index.get_indexer([pd.to_datetime(date, utc=True)], method="nearest")]
