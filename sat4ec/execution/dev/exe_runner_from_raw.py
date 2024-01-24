from sat4ec.execution.exe_config import Config
from sat4ec.execution.exe_production import Production
from pathlib import Path


if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"input/AOIs"),
        working_dir=Path(r"/mnt/data1/gitlab/sat4ec/data"),  # Path.home().joinpath("sat4ec"),
        out_dir=Path(r"output"),
        orbit="both",  # ascending or descending orbit or both
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
    prod.workflow(_path=r"/")
