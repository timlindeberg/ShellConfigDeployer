import argparse
import json
import sys

from pygments import highlight, lexers, formatters

from colors import *
from constants import *
from printer import Printer
from server_status import ServerStatus


class PrintServerStatusAction(argparse.Action):
    def __init__(self, option_strings, server_status=None,
                 dest=argparse.SUPPRESS, default=argparse.SUPPRESS,
                 help="show program's version number and exit"):
        super(PrintServerStatusAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)
        self.server_status = server_status

    def __call__(self, parser, namespace, values, option_string=None):
        print(printer.PREFIX + BOLD(WHITE("Server status")))
        formatted_json = json.dumps(self.server_status, sort_keys=True, indent=4)
        colorful_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()).strip()
        print('\n'.join([printer.PREFIX + line for line in colorful_json.split('\n')]))
        parser.exit()


SERVER_STATUS = ServerStatus()

parser = argparse.ArgumentParser(prog='scd', description='Deploys configuration to remote servers.')
parser.add_argument('server', type=str,
                    help='the server to connect to')
parser.add_argument('-P', dest='port', type=int, default=22,
                    help='the port to connect to (default 22)')
parser.add_argument('-f', dest='password_file', type=str, default='',
                    help='a file containing the password to use')
parser.add_argument('-p', dest='password', type=str,
                    help='the password.')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help='print more output')
parser.add_argument('--force', dest='force', action='store_true',
                    help='force a full deployment regardless of server status')
parser.add_argument('--print-server-status', action=PrintServerStatusAction,
                    server_status=SERVER_STATUS.status,
                    help='print server status and exit')
parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

args = parser.parse_args()

SERVER = args.server
PORT = args.port
VERBOSE = args.verbose
FORCE = args.force
printer = Printer(VERBOSE)
password_file = args.password_file
if args.password:
    PASSWORD = args.password
elif password_file:
    if not os.path.isfile(password_file):
        printer.info(RED_ + "The given password file " + BOLD(password_file) + RED(" does not exist."))
        sys.exit(1)
    PASSWORD = open(password_file).read().strip()
else:
    PASSWORD = None

if not os.path.isfile(SCD_CONFIG):
    printer.info(RED_ + "Missing configuration file " + BOLD(SCD_CONFIG.replace(HOME, '~')))
    sys.exit(1)

with open(SCD_CONFIG) as f:
    try:
        config = json.load(f)
    except json.decoder.JSONDecodeError as e:
        printer.info(RED_ + "Failed to parse configuration file " + BOLD(
            SCD_CONFIG.replace(HOME, '~') + ":"))
        printer.info("     " + RED(e.msg))
        sys.exit(1)
