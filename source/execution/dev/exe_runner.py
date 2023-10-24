from source.execution.exe_config import Config
from source.execution.exe_production import Production
from pathlib import Path


if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"input/AOIs"),
        working_dir=Path(r"/mnt/data1/gitlab/sat4ec/data"),  # Path.home().joinpath("sat4ec"),
        out_dir=Path(r"output"),
        orbit="both",  # ascending or descending orbit
        pol="VH",  # only use VH polarization
        aoi="vw_wolfsburgene",
        ext="geojson",
        start="2014-05-01",
        end="2022-12-31",
        monthly=True,
        regression="spline",
        linear=True,
        linear_fill=False,
        aoi_split=True,
    )
    prod = Production(config=conf)
    prod.workflow(_path=r"/mnt/data1/gitlab/sat4ec/source")
