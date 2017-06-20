import datetime
import json
import os.path
import sys

import deployment
from config import config

HOME = os.path.expanduser('~')
SERVER_STATUS_FILE = HOME + '/.scdstatus'


def flat_map(lists):
    if len(lists) == 0:
        return []
    return reduce(list.__add__, lists)


def default_status():
    return {
        'last_modified': 0,
        'installed_programs': []
    }


def read_json(file):
    with open(file) as f:
        return json.load(f)


def modifed_files(all_files, last_modified):
    def modified(file):
        if os.path.isdir(file):
            if config['ignore_git_folders'] and file.endswith('.git'):
                return []
            return flat_map([modified(file + '/' + f) for f in os.listdir(file)])
        if os.path.getctime(file) > last_modified:
            return [os.path.abspath(file)]
        return []

    home = os.path.expanduser('~') + '/'
    return flat_map([modified(home + file) for file in all_files])


def read_server_status(server_name):
    if not os.path.isfile(SERVER_STATUS_FILE):
        return default_status()

    with open(SERVER_STATUS_FILE) as f:
        server_status = json.load(f).get(server_name)
        return default_status() if server_status is None else server_status


def missing_programs(programs, installed):
    return [prog for prog in programs if prog not in installed]


if len(sys.argv) == 0:
    print("Usage: scd <server>")
    sys.exit(0)

server_name = sys.argv[1]

server_status = read_server_status(server_name)

programs_to_install = missing_programs(config['programs'], server_status['installed_programs'])

print("Programs to install: %s" % programs_to_install)

files = modifed_files(config['files'], server_status['last_modified'])

print("Modified files: %s" % len(files))

s = "01/12/2011"
x = datetime.datetime.strptime(s, "%d/%m/%Y").timestamp()

print(x)

if len(files) != 0:
    deployment.deploy_to_server(server_name, files)

print(files)
