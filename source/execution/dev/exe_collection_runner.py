from source.execution.exe_config import Config
from source.execution.exe_production import Production
from pathlib import Path


if __name__ == "__main__":
    orbits = [
        "asc",
        "des"
    ]

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
            orbit="both",
            pol="VH",  # only use VH polarization
            aoi="porsche_leipzig",
            ext="geojson",
            start="2016-01-01",
            monthly=False,
            regression="spline",
            linear=True,
            linear_fill=False,
            aoi_split=True,
        )
        prod = Production(config=conf)
        prod.workflow()
