import shutil
import subprocess
from pathlib import Path


def main(orbits=None, pols=None, aois=None, aoi_dir=None, start="2020-01-01", end="2020-12-31"):
    working_dir = aoi_dir.parent

    for key in aois.keys():
        for orbit in orbits:
            for pol in pols:
                shutil.copy(aois[key], working_dir)

                response = subprocess.run([
                    "python3", 
                    "../sat4ec/main.py",
                    "--aoi_data",
                    str(working_dir.joinpath(aois[key].name)),
                    "--start_date",
                    f"{start}",
                    "--end_date",
                    f"{end}",
                    "--anomaly_options",
                    "plot",
                    # "--plot_options",
                    # "minmax",
                    # "outliers",
                    "--orbit",
                    orbit,
                    "--polarization",
                    pol,
                ], capture_output=False)

        if working_dir.joinpath(key).exists():
            for item in working_dir.joinpath(key).glob("*"):
                for _file in item.glob("*"):  # delete files per orbit directory
                    _file.unlink()

                if item.is_dir():
                    shutil.rmtree(item)  # delete orbit directory

                if item.is_file():
                    item.unlink()

            shutil.rmtree(working_dir.joinpath(key))  # delete obsolete directory

        working_dir.joinpath("results").rename(working_dir.joinpath(key))
        working_dir.joinpath(aois[key].name).unlink()


if __name__ == "__main__":
    aoi_dir = Path(r"/mnt/data1/gitlab/sat4ec/tests/testdata/AOIs")
    orbits = [
        "asc",
        "des"
    ]
    
    pols = [
        # "VV",
        "VH"
    ]
    
    aois = {
        "gent": aoi_dir.joinpath("gent_parking_lot.geojson"),
        "munich_airport": aoi_dir.joinpath("munich_airport_1.geojson"),
        "munich_ikea": aoi_dir.joinpath("munich_ikea.geojson"),
        "bmw_leipzig": aoi_dir.joinpath("bmw_leipzig.geojson"),
        "vw_emden": aoi_dir.joinpath("vw_emden.geojson"),
        "bmw_regensburg": aoi_dir.joinpath("bmw_regensburg.geojson")
        # "bmw_leipzig_breakup": aoi_dir.joinpath("bmw_leipzig_breakup.geojson")
    }

    main(orbits, pols, aois, aoi_dir, start="2016-01-01", end="2022-12-31")
    