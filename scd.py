import fnmatch
import os.path
import sys
from functools import reduce

import colors
import formatting
import settings
from deployment import ConfigDeployer
from settings import config

HOME = os.path.expanduser('~')


def flat_map(lists):
    if len(lists) == 0:
        return []
    return reduce(list.__add__, lists)


def modified_files(all_files, last_modified):
    def modified(file):
        for ignore in config['ignore_files']:
            if fnmatch.fnmatch(file, ignore):
                return []
        if os.path.isdir(file):
            return flat_map([modified(file + '/' + f) for f in os.listdir(file)])
        if os.path.getctime(file) > last_modified:
            return [os.path.abspath(file)]
        return []

    return flat_map([modified(HOME + '/' + file) for file in all_files])


def missing_programs(programs, installed):
    return [prog for prog in programs if prog not in installed]


server_name = settings.SERVER

server_status = settings.SERVER_STATUS[server_name]

programs_to_install = missing_programs(config['programs'], server_status['installed_programs'])
files_to_deploy = modified_files(config['files'], server_status['last_modified'])

if len(files_to_deploy) == 0 and len(programs_to_install) == 0:
    sys.exit(0)

config_deployer = ConfigDeployer(server_name, programs_to_install, files_to_deploy)
success = config_deployer.deploy()
if success:
    print(formatting.PREFIX + colors.GREEN("Configuration successfully deployed."))
    settings.SERVER_STATUS.update(server_name)
    settings.SERVER_STATUS.save()
