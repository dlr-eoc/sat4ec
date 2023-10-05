import logging
import sys
import yaml

from dateutil.relativedelta import relativedelta
from datetime import datetime
from jsonformatter import JsonFormatter
from pathlib import Path


def get_monthly_keyword(monthly=False):
    if monthly:
        return "monthly_"

    else:
        return ""


def get_last_month():
    current_date = datetime.now()
    last_month = datetime(current_date.year, current_date.month, 1) + relativedelta(days=-1)

    return datetime.strftime(last_month, "%Y-%m-%d")


def create_out_dir(base_dir=None, out_dir=None):
    if not base_dir.joinpath(out_dir).exists():
        base_dir.joinpath(out_dir).mkdir(parents=True)


def load_yaml(yaml_path):
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def get_logger(
        name,
        out_dir=None,
        level=logging.INFO,
        also_log_to_stdout=True
):
    log_file = Path(out_dir).joinpath("log_sat4ec.json")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    string_format = """{
        "Asctime":         "asctime",
        "Levelname":       "levelname",
        "Pathname":        "pathname",
        "Message":         "message"
    }"""

    formatter = JsonFormatter(string_format)

    # create a file handler
    if not Path(out_dir).exists():
        Path(out_dir).mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_file)
    handler.setLevel(level)

    # create a logging format
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    if also_log_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(level)
        logger.addHandler(stdout_handler)

    return logger
