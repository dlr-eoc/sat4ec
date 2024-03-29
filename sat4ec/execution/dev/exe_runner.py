"""Encapsulate workflow for a single AOI."""
from pathlib import Path

from sat4ec.execution.exe_config import Config
from sat4ec.execution.exe_production import Production

if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"input/AOIs"),
        working_dir=Path(r"/mnt/data1/gitlab/sat4ec/data"),
        out_dir=Path(r"output"),
        orbit="des",  # ascending or descending orbit or both
        aoi="mercedes_bremen",
        ext="geojson",
        start="2021-03-01",  # comment this line or enter None if using default start date
        end="2021-05-01",  # comment this line or enter None if using automatic end date
        monthly=False,
        regression="spline",
        linear=True,
        linear_fill=False,
        aoi_split=True,
        overwrite_raw=False,
        online=False,
    )
    prod = Production(config=conf)
    prod.workflow(_path=r"/")
