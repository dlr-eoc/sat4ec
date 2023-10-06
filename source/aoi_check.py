from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry import mapping, shape
from shapely import from_wkt
from pathlib import Path, PurePath
import fiona


class AOI:
    def __init__(self, data, name="aoi"):
        self.name = name
        self.geometry = None
        self.features = None
        self.schema = None
        self.record = None
        self.aoi = None

        if isinstance(data, Path):
            self.filename = data
            self.load_aoi()

        elif isinstance(Path(data), PurePath):  # path can be resolved to a pathlib object
            if Path(data).exists():
                self.filename = Path(data)
                self.load_aoi()

            else:
                raise FileNotFoundError(f"The provided path {data} does not exist.")

        elif isinstance(data, str):
            if "POLYGON" in data:  # wkt string
                self.geometry = from_wkt(data)
                self.build_aoi(geometry_type="Polygon", geometry=self.geometry)

            else:
                raise AttributeError(f"The provided data {data} misses the keyword POLYGON.")

        elif isinstance(data, Polygon):
            self.geometry = data
            self.build_aoi(geometry_type="Polygon", geometry=self.geometry)

        else:
            raise TypeError(f"The provided data {data} is of unsupported type {type(data)}.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.aoi:
            self.aoi.close()

    def _build_schema(self, geometry_type="Polygon"):
        self.schema = {
            "geometry": geometry_type,
            "properties": {
                "name": "str"
            }
        }

    def _build_record(self, geometry=None):
        self.record = {
            "geometry": mapping(geometry),
            "properties": {
                "name": self.name
            }
        }

    def build_aoi(self, geometry_type="Polygon", geometry=None):
        self._build_schema(geometry_type=geometry_type)
        self._build_record(geometry=geometry)

    def save_aoi(self, out_dir, driver="GPKG", crs="epsg:4326", overwrite=True):
        if not overwrite and out_dir.joinpath(f"{self.name}.{driver.lower()}").exists():
            pass

        else:
            with fiona.open(
                    out_dir.joinpath(f"{self.name}.{driver.lower()}"), "w", driver=driver, crs=crs, schema=self.schema
            ) as out:
                out.write(self.record)

    def load_aoi(self):
        self.aoi = fiona.open(self.filename)

    def get_features(self):
        self.features = [feature for feature in self.aoi]

        if len(self.features) > 1:
            self.geometry = MultiPolygon([shape(feature["geometry"]) for feature in self.features])
            self.build_aoi(geometry_type="MultiPolygon", geometry=self.geometry)

        elif len(self.features) == 1:
            self.geometry = shape(self.features[0]["geometry"])
            self.build_aoi(geometry_type="Polygon", geometry=self.geometry)

        else:
            raise AttributeError(f"The AOI {self.filename} does not contain any features.")
