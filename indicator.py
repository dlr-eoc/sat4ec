from shapely.geometry.polygon import Polygon
from sentinelhub import Geometry, CRS, bbox_to_dimensions, DataCollection


class Indicator:
    def __init__(self, aoi=None, start_date=None, end_date=None, crs=CRS.WGS84, resolution=5, ascending=True):
        self.aoi = aoi
        self.crs = crs
        self.geometry = None
        self.ascending = ascending
        self.interval = (f'{start_date}T00:00:00Z', f'{end_date}T23:59:59Z')
        self.size = None
        self.resolution = resolution

        self._get_geometry()
        self._get_dimensions()
        self._get_collection()

    def _get_geometry(self):
        self.geometry = Geometry(self.aoi, crs=self.crs)  # shapely polygon with CRS

    def _get_dimensions(self):
        """
        Get width and height of polygon in pixels. CRS is the respective UTM, automatically derived.
        """
        self.size = bbox_to_dimensions(self.geometry.bbox, self.resolution)

    def _get_collection(self):
        if self.ascending:
            self.collection = DataCollection.SENTINEL1_IW_ASC

        else:
            self.collection = DataCollection.SENTINEL1_IW_DES


if __name__ == "__main__":
    aoi = Polygon([
        (3.754824, 51.096633),
        (3.753451, 51.096242),
        (3.755747,  51.093102),
        (3.755661, 51.09511),
        (3.755211, 51.094989),
        (3.754953, 51.095393),
        (3.755211, 51.09608),
        (3.755125, 51.0967),
        (3.755447, 51.097953),
        (3.755168, 51.098048),
        (3.755009, 51.097886),
        (3.754116, 51.097697),
        (3.754824, 51.096633),
    ])

    indicator = Indicator(
        aoi=aoi,
        start_date="2022-11-01",
        end_date="2022-11-10"
    )
