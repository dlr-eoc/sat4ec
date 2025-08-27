"""Get authentication for Sentinel Hub."""
from __future__ import annotations

from pathlib import Path
import os

from sentinelhub import SHConfig
from sentinelhub.download.sentinelhub_statistical_client import SentinelHubStatisticalDownloadClient

# from system.helper_functions import load_yaml


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

    def _get_config(self: Config) -> None:
        """Transfer credentials to Sentinel Hub with correct base URL."""
        self.config = SHConfig()

        self.config.sh_client_id = os.environ.get("SH_CLIENT_ID") #self.id
        self.config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET") #self.secret

        # defining correct environment for data access
        env = os.environ.get("SH_ENV", "commercial").lower()

        if env == "cdse":
            self.config.sh_base_url = "https://sh.dataspace.copernicus.eu"
            self.config.sh_token_url = (
                "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
            )

        else:  # commercial
            self.config.sh_base_url = "https://services.sentinel-hub.com"
            self.config.sh_token_url = (
                "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
            )

        print(f"[DEBUG Config] Using environment: {env}")
        print(f"[DEBUG Config] sh_base_url = {self.config.sh_base_url}")
        print(f"[DEBUG Config] sh_token_url = {self.config.sh_token_url}")

        _original_execute_download = SentinelHubStatisticalDownloadClient._execute_download

        def _execute_download_patched(self, request):
            """Force statistical requests to use the correct base URL from config."""
            if hasattr(self, "config") and getattr(self.config, "sh_base_url", None):
                request.url = f"{self.config.sh_base_url}/api/v1/statistics"
            return _original_execute_download(self, request)

        SentinelHubStatisticalDownloadClient._execute_download = _execute_download_patched

    # def _get_credentials(self: Config) -> None:
    #     """Read credentials from file."""
    #     credentials = load_yaml(Path(__file__).parent.joinpath("credentials.yaml"))

    #     if not self.id:
    #         self.id = credentials["SH_CLIENT_ID"]

    #     if not self.secret:
    #         self.secret = credentials["SH_CLIENT_SECRET"]