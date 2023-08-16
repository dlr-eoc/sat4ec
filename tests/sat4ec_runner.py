import subprocess
from pathlib import Path


def main(orbits=None, pols=None, aois=None):
    for orbit in orbits:
        for pol in pols:
            for key in aois.keys():
                response = subprocess.run([
                    "python3", 
                    "../sat4ec/main.py",
                    "--aoi_data",
                    str(aois[key]),
                    "--start_date",
                    "2020-01-01",
                    "--end_date",
                    "2020-12-31",
                    "--anomaly_options",
                    "plot",
                    "--orbit",
                    orbit,
                    "--polarization",
                    pol,
                ], capture_output=False)


if __name__ == "__main__":
    aoi_dir = Path(r"/tests/testdata")
    orbits = [
        "asc",
        "des"
    ]
    
    pols = [
        "VV",
        "VH"
    ]
    
    aois = {
        "gent": aoi_dir.joinpath("gent_parking_lot.geojson"),
        "munich_airport": aoi_dir.joinpath("munich_airport_1.geojson"),
        "munich_ikea": aoi_dir.joinpath("munich_ikea.geojson")
    }

    main(orbits, pols, aois)
    