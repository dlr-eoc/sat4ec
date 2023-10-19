from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry import mapping, shape
from shapely import from_wkt
from pathlib import Path, PurePath
import fiona


# TODO: Check that aspect has only 2 vertices, otherwise orientation deems impossible.
# TODO: Check that aspect group of parking lot AOIs and aspect line are equal.
# TODO: Document that equal aspect groups are obligatory for parking lot AOI and aspect line.
# TODO: Compute orientation of aspect line. Orientation only from 0 to 180°.
# TODO: Compare with S1 orbit orientation. Orbits are constant.


class Feature:
    def __init__(self, feature=None, fid=None):
        self.feature = feature
        self.fid = fid
        self.azimuth_group = None
        self.geometry = None

        if self.feature is not None:
            self._get_geometry()
            self._get_fid()
            self._get_azimuth_group()

    def _get_geometry(self):
        self.geometry = shape(self.feature["geometry"])

    def _get_fid(self):
        if self.feature["properties"].get("id"):  # check if feature holds column with name id
            self.fid = self.feature["properties"]["id"]

        else:
            self.fid = self.feature["id"]

    def _get_azimuth_group(self):
        if self.feature["properties"].get("group"):
            self.azimuth_group = self.feature["properties"]["group"]

        else:
            self.azimuth_group = None


class AOI:
    def __init__(self, data, aoi_split=False, name="aoi"):
        self.name = name
        self.geometry = None
        self.features = None
        self.schema = None
        self.record = None
        self.aoi = None
        self.aoi_split = aoi_split

        if isinstance(data, str):
            if "POLYGON" in data:  # wkt string
                self.geometry = from_wkt(data)
                self.build_aoi(geometry_type="Polygon", geometry=self.geometry)

            elif Path(data).exists():
                self.filename = Path(data)
                self.load_aoi()
                self.get_features()

            else:
                raise TypeError(f"The provided data {data} cannot be resolved to WKT or to a path.")

        elif isinstance(data, Path):
            self.filename = data
            self.load_aoi()
            self.get_features()

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

    def get_feature(self):
        if self.geometry is not None:
            feature = Feature()
            feature.geometry = self.geometry
            yield feature  # return feature with geometry that has already been computed

        else:
            if len(self.features) == 1:
                feature = Feature(feature=self.features[0])
                self.build_aoi(geometry_type="Polygon", geometry=feature.geometry)

                yield feature  # AOI holds a single feature/polygon

            elif len(self.features) > 1:
                if self.aoi_split:
                    # duplicates functionality self.get_features, but treats features individually
                    for f in self.features:
                        feature = Feature(feature=f)
                        yield feature

                else:
                    feature = Feature()
                    feature.geometry = MultiPolygon([shape(feature["geometry"]) for feature in self.features])
                    feature.fid = "0"
                    self.build_aoi(geometry_type="MultiPolygon", geometry=feature.geometry)

                    yield feature  # AOI holds multiple features/polygons but are merged to a multipolygon

            else:
                raise AttributeError(f"The AOI {self.filename} does not contain any features.")
