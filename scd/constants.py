import os.path
from timeit import default_timer as timer

HOME = os.path.expanduser("~")
SCD_FOLDER = HOME + "/.scd"
SCD_CONFIG = SCD_FOLDER + "/config"
TAR_NAME = "scd_conf.tar.gz"
TAR_PATH = SCD_FOLDER + "/" + TAR_NAME

SERVER_STATUS_FILE = SCD_FOLDER + "/server_status"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

VERSION = "1.0"


def get_time(start_time):
    return "%.2f" % (timer() - start_time)
