"""Encapsulate workflow for multiple AOIs."""
from pathlib import Path

from sat4ec.execution.exe_config import Config
from sat4ec.execution.exe_production import Production

if __name__ == "__main__":
    orbits = ["asc", "des"]

    pol = "VH"

    aois = [
        # "munich_airport",
        # "munich_ikea"
        # "volvo_gent",
        # "bmw_regensburg",
        # "bmw_leipzig",
        # "vw_emden",
        # "vw_wolfsburg",
        # "vw_zwickau",
        # "opel_ruesselsheim",
        "porsche_leipzig",
        # "ford_koeln",
    ]

    for aoi in aois:
        conf = Config(
            aoi_dir=Path(r"input/AOIs"),
            working_dir=Path(r"/mnt/data1/gitlab/sat4ec/data"),  # Path.home().joinpath("sat4ec"),
            out_dir=Path(r"output"),
            orbit="both",  # ascending or descending orbit or both
            aoi=aoi,
            ext="geojson",
            start="2016-01-01",  # comment this line or enter None if using default start date
            end="2021-05-01",  # comment this line or enter None if using automatic end date
            monthly=False,
            regression="spline",
            linear=True,
            linear_fill=False,
            aoi_split=True,
        )
        prod = Production(config=conf)
        prod.workflow()
