from source.execution.exe_config import Config
from source.execution.exe_production import Production
from pathlib import Path


if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"input/AOIs"),
        working_dir=Path(r"/mnt/data1/gitlab/sat4ec/data"),  # Path.home().joinpath("sat4ec"),
        out_dir=Path(r"output"),
        orbit="asc",  # ascending or descending orbit
        aoi="bmw_regensburg",
        ext="geojson",
        start="2022-12-01",
        monthly=False,
        regression="spline",
        linear=True,
        linear_fill=False,
        aoi_split=False,
    )
    prod = Production(config=conf)
    prod.workflow(_path=r"/mnt/data1/gitlab/sat4ec/source")
