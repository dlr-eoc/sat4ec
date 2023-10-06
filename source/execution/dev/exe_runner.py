from source.execution.exe_config import Config
from source.execution.exe_production import Production
from pathlib import Path


if __name__ == "__main__":
    conf = Config(
        aoi_dir=Path(r"input/AOIs"),
        working_dir=Path.home().joinpath("sat4ec"),
        out_dir=Path(r"output"),
        orbit="asc",  # ascending or descending orbit
        pol="VH",  # only use VH polarization
        aoi="porsche_leipzig",
        ext="geojson",
        start="2016-01-01",
        monthly=False,
        regression="spline",
        linear=True,
    )
    prod = Production(config=conf)
    prod.workflow()
