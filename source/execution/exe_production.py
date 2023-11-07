import subprocess
import os
from pathlib import Path
from source.execution.exe_helper_functions import get_name

# for development
# os.environ["PROJ_LIB"] = str(Path.home().joinpath("mambaforge", "envs", "sat4ec", "share", "proj").absolute())
# for production
os.environ["PROJ_LIB"] = str(Path.home().joinpath("sat4ec", "sat4ec_env", "share", "proj").absolute())


class Production:
    def __init__(self, config=None):
        self.config = config

    def workflow(self, _path=r"source"):
        response = subprocess.run(
            [
                "python3",
                f"{Path(_path).joinpath('main.py')}",
                "--aoi_data",
                self.config.aoi,
                "--out_dir",
                self.config.out_dir,
                "--start_date",
                f"{self.config.start}",
                # "--end_date",
                # f"{self.config.end}",
                "--orbit",
                self.config.orbit,
                "--polarization",
                self.config.pol,
                "--name",
                get_name(self.config.aoi_name),
                "--aggregate",
                "monthly" if self.config.monthly else "daily",
                "--regression",
                self.config.regression,
                "--linear",
                "true" if self.config.linear else "false",
                "--linear_fill",
                "true" if self.config.linear_fill else "false",
                "--aoi_split",
                "true" if self.config.aoi_split else "false",
            ],
            capture_output=False,
        )
