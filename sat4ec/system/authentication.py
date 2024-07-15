"""Get authentication for Sentinel Hub."""
from __future__ import annotations

from pathlib import Path

from sentinelhub import SHConfig
#from system.helper_functions import load_yaml


class Config:
    """Encapsulate methods to read credentials."""

    def __init__(self: Config, _id: str | None = None, secret: str | None = None) -> None:
        """Initialize class Config."""
        self.id = _id
        self.secret = secret
        self.config = None

        self._check_directory()
        # self._get_credentials()
        self._get_config()

    @staticmethod
    def _check_directory() -> None:
        if not Path(__file__).parent.exists():
            Path(__file__).parent.mkdir(parents=True)

    def _get_credentials(self: Config) -> None:
        """Read credentials from file."""
        credentials = load_yaml(Path(__file__).parent.joinpath("credentials.yaml"))

        if not self.id:
            self.id = credentials["SH_CLIENT_ID"]

        if not self.secret:
            self.secret = credentials["SH_CLIENT_SECRET"]

    def _get_config(self: Config) -> None:
        """Transfer credentials to Sentinel Hub."""
        self.config = SHConfig()

        self.config.sh_client_id = self.id
        self.config.sh_client_secret = self.secret
