import pandas as pd

from system.authentication import Config
from sentinelhub import DataCollection, SentinelHubCatalog


class StacItems(Config):
    def __init__(
        self,
        geometry=None,
        df=None,
        orbit="asc",
        pol="VH",
        timestamp=None,
        out_dir=None,
    ):
        super().__init__()

        self.catalog = None
        self.geometry = geometry
        self.anomalies_df = df  # input
        self.dataframe = None  # output
        self.orbit = orbit
        self.timestamp = timestamp
        self.pol = pol
        self.out_dir = out_dir

        self._get_catalog()
        self._get_collection()

    def _get_catalog(self):
        self.catalog = SentinelHubCatalog(config=self.config)

    def _get_collection(self):
        self.catalog.get_collection(DataCollection.SENTINEL1)

    def get_scenes(self):
        return self.anomalies_df.apply(lambda row: self.search_catalog(row), axis=1)

    def scenes_to_df(self):
        scenes_df = self.get_scenes()

        self.dataframe = pd.DataFrame(
            {
                "interval_from": [
                    pd.to_datetime(_item["properties"]["datetime"]).normalize()
                    for values in scenes_df.values
                    for _item in values
                ],
                "scene": [
                    _item["id"] for values in scenes_df.values for _item in values
                ],
            }
        )

    def join_with_anomalies(self):
        self.dataframe = self.dataframe.set_index("interval_from")

        self.dataframe["scene"] = self.dataframe.set_index(self.dataframe.index)[
            "scene"
        ]
        self.dataframe["anomaly"] = self.anomalies_df.set_index(
            self.anomalies_df.index
        )["anomaly"]

    def save(self):
        out_file = self.out_dir.joinpath(
            f"scenes_indicator_1_{self.orbit}_{self.pol}_{self.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.csv",
        )

        self.dataframe.to_csv(out_file)

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
