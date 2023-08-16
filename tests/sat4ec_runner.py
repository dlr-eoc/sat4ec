import subprocess
from pathlib import Path


def main(orbits=None, pols=None, aois=None, aoi_dir=None):
    for key in aois.keys():
        for orbit in orbits:
            for pol in pols:
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

        aoi_dir.joinpath("results").rename(aoi_dir.joinpath(key))


if __name__ == "__main__":
    aoi_dir = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata")
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

    main(orbits, pols, aois, aoi_dir)
    