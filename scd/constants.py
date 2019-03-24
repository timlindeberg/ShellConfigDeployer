import os.path

HOME = os.path.expanduser("~")
SCD_FOLDER = f"{HOME}/.scd"
SCD_CONFIG = f"{SCD_FOLDER}/config"
TAR_NAME = "scd_conf.tar.gz"
TAR_PATH = f"{SCD_FOLDER}/{TAR_NAME}"

PWD_NAME = f"tmp.txt"
PWD_PATH = f"{SCD_FOLDER}/{PWD_NAME}"

TEMPORARY_FILES = [TAR_PATH, PWD_PATH]

SERVER_STATUS_FILE = SCD_FOLDER + "/server_status"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

VERSION = "1.0"
