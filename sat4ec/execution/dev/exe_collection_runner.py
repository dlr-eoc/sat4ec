"""Encapsulate workflow for multiple AOIs."""
from pathlib import Path
from sat4ec.execution.exe_config import Config
from sat4ec.execution.exe_production import Production

if __name__ == "__main__":
    orbits = ["asc", "des"]

    pol = "VH"

    aois = [
    "bmw_regensburg",
    "bmw_leipzig",
    "audi_ingolstadt",
    "audi_neckarsulm",
    "ford_cologne",
    "ford_saarlouis",
    "mercedes_bremen",
    "mercedes_duesseldorf",
    "mercedes_ludwigsfelde",
    "opel_eisenach",
    "opel_ruesselsheim",
    "porsche_leipzig",
    "vw_emden",
    "vw_wolfsburg",
    "vw_zwickau",
    ]

    for aoi in aois:
        conf = Config(
            aoi_dir=Path(r"docs\aois"),
            working_dir=Path(r"sat4ec"),
            out_dir=Path(r"output"),
            orbit="both",  # ascending or descending orbit or both
            aoi=aoi,
            ext="geojson",
            start=None,  # comment this line or enter None if using default start date
            end=None,  # comment this line or enter None if using automatic end date
            monthly=True,
            regression="spline",
            linear=True,
            linear_fill=False,
            aoi_split=False,
            overwrite_raw=True,
            online=True,
        )
        prod = Production(config=conf)
        prod.workflow()
