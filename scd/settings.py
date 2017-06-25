import json
import sys

from scd.argparser import parser
from scd.colors import *
from scd.constants import *
from scd.printer import Printer
from scd.server_status import ServerStatus

DEFAULT_CONFIG = """
{
    "username": "<USER>",
    "install_method": "<yum> | <apt-get>",
    "ignore_files": [
        ".gitignore",
        ".git",
        ".DS_Store"
    ],
    "files": [
        ".oh-my-zsh",
        ".zshrc"
    ],
    "programs": [
        "unzip",
        "zsh"
    ]
}
""".strip()

printer = Printer(False)

if not os.path.isfile(SCD_CONFIG):
    printer.info(RED("Missing configuration file " + BOLD(SCD_CONFIG.replace(HOME, '~'))))
    printer.info(RED("Creating default configuration. Please edit " + BOLD(SCD_CONFIG.replace(HOME, '~')) +
                     RED(" with your settings.")))
    if not os.path.exists(SCD_FOLDER):
        os.makedirs(SCD_FOLDER)

    with open(SCD_CONFIG, 'w') as f:
        f.write(DEFAULT_CONFIG)
    sys.exit(1)

with open(SCD_CONFIG) as f:
    try:
        config = json.load(f)
    except json.decoder.JSONDecodeError as e:
        printer.info(RED("Failed to parse configuration file " +
                         BOLD(SCD_CONFIG.replace(HOME, '~')) + RED(":")))
        printer.info("    " + RED(e))
        sys.exit(1)

args = parser.parse_args()
SERVER = args.server or config.get('server')
PORT = args.port or config.get('port') or 22
VERBOSE = args.verbose
FORCE = args.force

SERVER_STATUS = ServerStatus()

printer = Printer(VERBOSE)
password_file = args.password_file

if not SERVER:
    printer.info(RED("No server specified."))
    sys.exit(1)

if args.password:
    PASSWORD = args.password
elif password_file:
    if not os.path.isfile(password_file):
        printer.info(RED_ + "The given password file " + BOLD(password_file) + RED(" does not exist."))
        sys.exit(1)
    PASSWORD = open(password_file).read().strip()
else:
    PASSWORD = None
