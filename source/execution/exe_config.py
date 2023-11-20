class Config:
    def __init__(
        self,
        orbit="asc",
        aoi=None,
        ext="geojson",
        working_dir=None,
        out_dir=None,
        aoi_dir=None,
        start=None,
        end=None,
        monthly=False,
        regression="spline",
        linear=False,
        linear_fill=False,
        aoi_split=False,
        overwrite_raw=False,
    ):
        self.orbit = orbit
        self.pol = "VH"
        self.aoi_dir = aoi_dir
        self.aoi = aoi
        self.ext = ext
        self.start = start
        self.end = end
        self.working_dir = working_dir
        self.out_dir = out_dir
        self.monthly = monthly
        self.regression = regression
        self.linear = linear
        self.linear_fill = linear_fill
        self.aoi_split = aoi_split
        self.overwrite_raw = overwrite_raw

        self._get_out_dir()
        self._get_aoi_dir()
        self._get_aoi()

    def _get_out_dir(self):
        self.out_dir = self.working_dir.joinpath(self.out_dir, self.aoi)

    def _get_aoi_dir(self):
        self.aoi_dir = self.working_dir.joinpath(self.aoi_dir)
        self.aoi_dir.exists()

    def _get_aoi(self):
        self.aoi = self.aoi_dir.joinpath(f"{self.aoi}.{self.ext}")
        self.aoi_name = self.aoi.stem
