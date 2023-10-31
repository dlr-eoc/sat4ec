import pandas as pd

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
        df = df.set_index("interval_from")

        return df

    def init_dataframe(self, df=None):
        self.dataframe = df.copy()

    def add_stac_item(self, df=None):
        self.dataframe = self.dataframe.merge(df, how="outer")

    def get_stac_collection(self):
        for index, (feature, geometry) in enumerate(zip(self.features, self.geometries)):
            stac = StacItems(
                anomalies_df=self.anomalies_df.loc[
                    :, self.anomalies_df.columns.str.startswith(f"{feature.fid}_")
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
        self.dataframe = self.dataframe.loc[:, ~self.dataframe.columns.str.endswith(columns)]

    def save(self):
        out_file = self.out_dir.joinpath(
            "scenes", f"indicator_1_scenes_{self.orbit}_{self.pol}.csv",
        )

        self.dataframe.to_csv(out_file)


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
        true_anomalies = self.anomalies_df.loc[self.anomalies_df[f"{self.fid}_anomaly"]]  # True at these indices
        self.dataframe = self.dataframe.merge(true_anomalies, on=["interval_from"], how="inner")
        self.dataframe = self.dataframe.drop(f"{self.fid}_anomaly", axis=1)

    def get_scenes(self):
        return self.anomalies_df.apply(lambda row: self.search_catalog(row), axis=1)

    def scenes_to_df(self):
        scenes_df = self.get_scenes()

        self.dataframe = pd.DataFrame(
            {
                "interval_from": [
                    pd.to_datetime(_item["properties"]["datetime"]).normalize()  # get rid of time
                    for values in scenes_df.values
                    for _item in values
                ],
                f"{self.fid}_scene": [
                    _item["id"] for values in scenes_df.values for _item in values
                ],
            }
        )

    def search_catalog(self, row):
        date = row.name

        search_iterator = self.catalog.search(
            DataCollection.SENTINEL1,
            geometry=self.geometry,
            time=(
                f"{date.year}-{date.month}-{date.day}",
                f"{date.year}-{date.month}-{date.day}",
            ),
            fields={"include": ["id", "properties.datetime"], "exclude": []},
        )

        return list(search_iterator)
