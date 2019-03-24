import argparse
import re

from scd.constants import *


def _read_description() -> str:
    with open("README.md", 'r') as f:
        description = f.read()

    description = description.split('## Installation')[0]
    description = re.sub(r'```(.*)', '', description)
    return description


parser = argparse.ArgumentParser(prog="scd", description=_read_description(),
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("hosts", type=str, nargs="*",
                    help="the hosts to deploy configuration to")
parser.add_argument("-P", "--port", dest="port", type=int,
                    help="the port to connect to (default 22)")
parser.add_argument("-f", "--password-file", dest="password_file", type=str, default="",
                    help="a file containing the password to use")
parser.add_argument("-r", "--read-password", dest="read_password", action="store_true",
                    help="read the password from stdin")
parser.add_argument("-p", "--password", dest="password", type=str,
                    help="the password")
parser.add_argument("-i", "--private_key", dest="private_key", type=str,
                    help="path to a private key file to use")
parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                    help="print more output")
parser.add_argument("-u", "--user", dest="user", type=str,
                    help="the user to authenticate with")
parser.add_argument("--no-color", dest="no_color", action="store_true",
                    help="removes all color from output")
parser.add_argument("--clear-status", metavar="HOST", dest="clear_status", type=str,
                    help="clear the status of a given server and exit")
parser.add_argument("--force", dest="force", action="store_true",
                    help="force a full deployment regardless of host status")
parser.add_argument("--host-status", nargs="?", dest="print_host_status", const="all", type=str,
                    help="print host status and exit")
parser.add_argument("--print-config", dest="print_config", action="store_true",
                    help="print configuration and exit")
parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)
