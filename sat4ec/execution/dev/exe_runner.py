from sat4ec.execution.exe_config import Config
from sat4ec.execution.exe_production import Production
from pathlib import Path


if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"input/AOIs"),
        working_dir=Path(r"/mnt/data1/gitlab/sat4ec/data"),  # Path.home().joinpath("sat4ec"),
        out_dir=Path(r"output"),
        orbit="des",  # ascending or descending orbit
        aoi="ford_cologne",
        ext="geojson",
        start="2021-03-01",
        end="2021-05-01",
        monthly=False,
        regression="spline",
        linear=True,
        linear_fill=False,
        aoi_split=True,
        overwrite_raw=False,
    )
    prod = Production(config=conf)
    prod.workflow(_path=r"/")
