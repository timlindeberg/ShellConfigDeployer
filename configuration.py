import json
import os.path
import sys

import formatting
from colors import *

HOME = os.path.expanduser('~')
SCD_FOLDER = HOME + '/.scd'
SCD_CONFIG = SCD_FOLDER + '/config'

if not os.path.isfile(SCD_CONFIG):
    print(formatting.PREFIX + RED_ + "Missing configuration file " + BOLD(SCD_CONFIG.replace(HOME, '~')))
    sys.exit(0)

with open(SCD_CONFIG) as f:
    config = json.load(f)
