"""Encapsulate workflow for a single AOI."""
from pathlib import Path
from sat4ec.execution.exe_config import Config
from sat4ec.execution.exe_production import Production

if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"docs\aois"),
        working_dir=Path(r"sat4ec"),
        out_dir=Path(r"output"),
        orbit="asc",  # ascending or descending orbit or both
        aoi="ford_cologne",
        ext="geojson",
        start="2021-03-01",  # comment this line or enter None if using default start date
        end="2021-05-03",  # comment this line or enter None if using automatic end date
        monthly=False,
        regression="spline",
        linear=True,
        linear_fill=False,
        aoi_split=False,
        overwrite_raw=False,
        online=True,
    )
    prod = Production(config=conf)
    prod.workflow()
