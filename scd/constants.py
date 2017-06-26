import os.path

HOME = os.path.expanduser("~")
SCD_FOLDER = HOME + "/.scd"
SCD_CONFIG = SCD_FOLDER + "/config"
ZIP_NAME = "scd_conf.zip"
ZIP_PATH = SCD_FOLDER + "/" + ZIP_NAME

SERVER_STATUS_FILE = SCD_FOLDER + "/server_status"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

VERSION = "1.0"
