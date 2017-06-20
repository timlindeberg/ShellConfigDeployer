import json
import os.path
import sys

import formatting
from colors import *

HOME = os.path.expanduser('~')
SCD_CONFIG = HOME + '/.scdrc'

if not os.path.isfile(SCD_CONFIG):
    print(formatting.PREFIX + RED + "Missing configuration file " + BOLD + "~/.scdrc." + CLEAR)
    sys.exit(0)

with open(SCD_CONFIG) as f:
    config = json.load(f)
