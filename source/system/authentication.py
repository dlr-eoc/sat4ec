from pathlib import Path
from source.system.helper_functions import load_yaml
from sentinelhub import SHConfig


class Config:
    def __init__(self, _id=None, secret=None):
        self.id = _id
        self.secret = secret
        self.config = None

        self._check_directory()
        self._get_credentials()
        self._get_config()

    @staticmethod
    def _check_directory():
        if not Path(__file__).parent.exists():
            Path(__file__).parent.mkdir(parents=True)

    def _get_credentials(self):
        credentials = load_yaml(Path(__file__).parent.joinpath("credentials.yaml"))

        if not self.id:
            self.id = credentials["SH_CLIENT_ID"]

        if not self.secret:
            self.secret = credentials["SH_CLIENT_SECRET"]

    def _get_config(self):
        self.config = SHConfig()

        self.config.sh_client_id = self.id
        self.config.sh_client_secret = self.secret
