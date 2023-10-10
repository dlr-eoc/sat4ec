import subprocess
from source.execution.exe_helper_functions import get_name


class Production:
    def __init__(self, config=None):
        self.config = config

    def workflow(self):
        response = subprocess.run(
            [
                "python3",
                "source/main.py",
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
            ],
            capture_output=False,
        )