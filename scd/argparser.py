import argparse
import json

from pygments import highlight, lexers, formatters

from scd.colors import *
from scd.constants import *
from scd.printer import Printer
from scd.server_status import ServerStatus


class PrintServerStatusAction(argparse.Action):
    def __init__(self, option_strings, help, dest=argparse.SUPPRESS, default=argparse.SUPPRESS):
        super(PrintServerStatusAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        printer = Printer(False)
        printer.info(BOLD(WHITE("Server status")))

        server_status = ServerStatus().status
        formatted_json = json.dumps(server_status, sort_keys=True, indent=4)
        colorful_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter()).strip()
        for line in colorful_json.split('\n'):
            printer.info(line)
        parser.exit()


prog_description = '''
Deploys shell configuration to remote servers. Use ~/.scd/config to specify
what programs should be installed on the remote server and what files should
be deployed. Example:
{
    "username": "vagrant",
    "install_method": "apt-get",
    "server": "127.0.0.1",
    "port": 2222,
    "ignore_files": [
        ".gitignore",
        ".git",
        ".DS_Store"
    ],
    "files": [
        ".oh-my-zsh",
        ".zshrc",
        ".gitconfig"
    ]
    "programs": [
        "zsh",
        "tree"
    ]
}

This configuration will deploy the folder .oh-my-zsh and the files .zshrc and
.gitconfig placed in ~ on to the remote server and install zsh and tree.
It will ignore .git folders and .DS_Store files and sign on to the server using
the user 'vagrant' and install programs using apt-get. Server and port can be
specified in the configuration but is normally given as a command line
argument.

SCD keeps track of which servers have correct shell configuration by keeping
track of the time of deployment as well as a list of programs that have been
installed. Any files that have since changed or been added will be redeployed
to the server. It can not handle removal of files or programs.
'''

parser = argparse.ArgumentParser(prog='scd', description=prog_description,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('server', type=str, nargs='?',
                    help='the server to connect to')
parser.add_argument('-P', '--port', dest='port', type=int,
                    help='the port to connect to (default 22)')
parser.add_argument('-f', '--file', dest='password_file', type=str, default='',
                    help='a file containing the password to use')
parser.add_argument('-p', '--password', dest='password', type=str,
                    help='the password.')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                    help='print more output')
parser.add_argument('-u', '--user', dest='user', type=str,
                    help='the user to authenticate with')
parser.add_argument('--force', dest='force', action='store_true',
                    help='force a full deployment regardless of server status')
parser.add_argument('--print-server-status', action=PrintServerStatusAction,
                    help='print server status and exit')
parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
