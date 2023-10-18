from source.execution.exe_config import Config
from source.execution.exe_production import Production
from pathlib import Path


if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"input/AOIs"),
        working_dir=Path(r"/mnt/data1/gitlab/sat4ec/data"),  # Path.home().joinpath("sat4ec"),
        out_dir=Path(r"output"),
        orbit="des",  # ascending or descending orbit
        pol="VH",  # only use VH polarization
        aoi="vw_wolfsburg",
        ext="geojson",
        start="2016-01-01",
        monthly=False,
        regression="spline",
        linear=True,
        aoi_split=False,
    )
    prod = Production(config=conf)
    prod.workflow(_path=r"/mnt/data1/gitlab/sat4ec/source")
