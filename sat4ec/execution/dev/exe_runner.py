"""Encapsulate Sat4Ec workflow."""
from pathlib import Path
from sat4ec.execution.exe_config import Config
from sat4ec.execution.exe_production import Production

if __name__ == "__main__":

    # choose one or more automotive facilties to analyze by commenting out all others
    aois = [ 
    "bmw_regensburg",
    # "bmw_leipzig",
    # "audi_ingolstadt",
    # "audi_neckarsulm",
    # "ford_cologne",
    # "ford_saarlouis",
    # "mercedes_bremen",
    # "mercedes_duesseldorf",
    # "mercedes_ludwigsfelde",
    # "opel_eisenach",
    # "opel_ruesselsheim",
    # "porsche_leipzig",
    # "vw_emden",
    # "vw_wolfsburg",
    # "vw_zwickau",
    ]

    for aoi in aois:
        conf = Config(
            aoi_dir=Path(r"docs\aois"),
            working_dir=Path(r"sat4ec"),
            out_dir=Path(r"output"),
            orbit="both",  # ascending or descending orbit or both
            aoi=aoi,
            ext="geojson",
            start=None,  # specify a starting date for the time series (YYYY-MM-DD) or comment this line or enter None if using default start date
            end=None,  # specify an end date for the time series (YYYY-MM-DD) or comment this line or enter None if using automatic end date
            monthly=True, # choose between monthly (True) and daily (False) data
            regression="spline", # choose between available interpolation methods for daily data: spline (default), rolling mean, polynomial
            linear=True,
            linear_fill=False,
            aoi_split=False, # choose between data for individual parking lots (True) or entire facilities (False)
            overwrite_raw=True,
            online=True,
        )
        prod = Production(config=conf)
        prod.workflow()