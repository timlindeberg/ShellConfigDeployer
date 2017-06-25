import json
import sys

from pygments import highlight, lexers, formatters

from scd.argparser import parser
from scd.constants import *
from scd.host_status import HostStatus
from scd.printer import Printer

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

_printer = Printer(False)


def error(msg, *items):
    _printer.error(msg, *items)
    sys.exit(1)


_CONFIG = SCD_CONFIG.replace(HOME, '~')

if not os.path.isfile(SCD_CONFIG):
    _printer.error("Missing configuration file %s.", _CONFIG)
    _printer.error("Creating default configuration. Please edit %s with your settings", _CONFIG)
    if not os.path.exists(SCD_FOLDER):
        os.makedirs(SCD_FOLDER)

    with open(SCD_CONFIG, 'w') as f:
        f.write(DEFAULT_CONFIG)
        sys.exit(1)

with open(SCD_CONFIG) as f:
    try:
        _config = json.load(f)
    except json.decoder.JSONDecodeError as e:
        _printer.error("Failed to parse configuration file %s:", _CONFIG)
        _printer.error("    " + str(e))
        sys.exit(1)

_args = parser.parse_args()

HOST = _args.host or _config.get('host') or error(
    "No host specified. Specify host either in %s under the attribute %s or as a command line argument.",
    _CONFIG, '"host"'
)

USER = _args.user or _config.get('user') or error(
    "No user specified. Specify user either in %s under the attribute %s or using the %s (%s) flag.",
    _CONFIG, '"user"', '--user', '-u'
)

SHELL = _config.get('shell') or error(
    "Shell is not specified. Specify which shell to use in %s under the attribute %s.",
    _CONFIG, '"shell"'
)

FILES = _config.get('files') or error(
    "Which files to deploy are not specified. Specify which files to deploy in %s under the attribute %s.",
    _CONFIG, '"files"'
)

PROGRAMS = _config.get('programs') or error(
    "Which programs to install are not specified. Specify which programs to install in %s under the attribute %s.",
    _CONFIG, '"programs"'
)

INSTALL_METHOD = _config.get('install_method') or error(
    "The install method is not specified. Specify the installation method in %s under the attribute %s. " +
    "Valid options are %s and %s.",
    _CONFIG, '"install_method"', 'yum', 'apt-get'
)

IGNORED_FILES = _config.get('ignored_files') or []
PORT = _args.port or _config.get('port') or 22
VERBOSE = _args.verbose
FORCE = _args.force

HOST_STATUS = HostStatus()

if _args.clear_status:
    if HOST_STATUS.clear(_args.clear_status):
        _printer.info("Clearing status of host %s.", _args.clear_status)
        HOST_STATUS.save()
    else:
        _printer.error("Host status file does not contain host %s.", _args.clear_status)
    sys.exit(0)

if _args.host_status:
    formatted_json = json.dumps(HOST_STATUS.status, sort_keys=True, indent=4)
    colorful_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()).strip()
    for line in colorful_json.split('\n'):
        _printer.info(line)
    sys.exit(0)

_password_file = _args.password_file

if _args.password:
    PASSWORD = _args.password
elif _password_file:
    if not os.path.isfile(_password_file):
        error("The given password file %s does not exist.", _password_file)

    PASSWORD = open(_password_file).read().strip()
else:
    PASSWORD = None
