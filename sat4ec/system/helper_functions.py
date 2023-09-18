import logging
import sys
import yaml

from jsonformatter import JsonFormatter
from pathlib import Path


def get_monthly_keyword(monthly=False):
    if monthly:
        return "monthly_"

    else:
        return ""


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
