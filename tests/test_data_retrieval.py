import unittest
from fiona.collection import Collection
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
from shapely import errors
from sat4ec.aoi_check import AOI
from pathlib import Path


class TestGetData(unittest.TestCase):