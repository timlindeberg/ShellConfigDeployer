import argparse

from scd.constants import *

prog_description = """
Deploys shell configuration to remote servers. Use ~/.scd/config to specify
what programs should be installed on the remote server and what files should
be deployed. Example:
{
    "user": "vagrant",
    "install_method": "apt-get",
    "host": "127.0.0.1",
    "port": 2222,
    "ignored_files": [
        ".gitignore",
        ".git",
        ".DS_Store"
    ],
    "files": [
        ".oh-my-zsh",
        ".zshrc",
        ".gitconfig"
    ],
    "programs": [
        "unzip",
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
"""

parser = argparse.ArgumentParser(prog="scd", description=prog_description,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("hostname", type=str, nargs="?",
                    help="the host to connect to")
parser.add_argument("-P", "--port", dest="port", type=int,
                    help="the port to connect to (default 22)")
parser.add_argument("-f", "--password-file", dest="password_file", type=str, default="",
                    help="a file containing the password to use")
parser.add_argument("-r", "--read-password", dest="read_password", action="store_true",
                    help="read the password from stdin")
parser.add_argument("-p", "--password", dest="password", type=str,
                    help="the password")
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
parser.add_argument("--host-status", dest="print_host_status", action="store_true",
                    help="print host status and exit")
parser.add_argument("--print-config", dest="print_config", action="store_true",
                    help="print configuration and exit")
parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)
