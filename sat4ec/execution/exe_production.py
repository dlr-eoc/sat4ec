"""Encapsulate production workflow."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from exe_config import Config

from sat4ec.execution.exe_helper_functions import get_name

# for production
os.environ["PROJ_LIB"] = str(Path.home().joinpath("sat4ec", "sat4ec_env", "share", "proj").absolute())


class Production:
    """Encapsulate production workflow."""

    def __init__(self: Production, config: Config | None = None) -> None:
        """Initialize Production class."""
        self.config = config

    def workflow(self: Production, _path: str = r"sat4ec") -> None:
        """Set workflow parameters."""
        python_command = "python" if os.name == "nt" else "python3"
        env = os.environ.copy()

        #subprocess.run(
        process = subprocess.Popen(
            [
                python_command,
                f"{Path(_path).joinpath('main.py')}",
                "--aoi_data",
                self.config.aoi,
                "--out_dir",
                self.config.out_dir,
                "--start_date",
                f"{self.config.start}",
                "--end_date",
                f"{self.config.end}",
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
                "--overwrite_raw",
                "true" if self.config.overwrite_raw else "false",
                "--online_data",
                "true" if self.config.online else "false",
            ],
            # capture_output=False,
            # check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=env,
        )

        # Capture and print stdout and stderr
        for line in process.stdout:
            print(line.strip())
        for line in process.stderr:
            print(line.strip())

        # Wait for the process to finish and get the return code
        return_code = process.wait()
        if return_code == 0:
            print("Subprocess completed successfully.")
        else:
            print("Subprocess failed.")
