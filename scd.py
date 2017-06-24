import fnmatch
import os.path
import sys
from functools import reduce

import settings
from colors import *
from deployment import ConfigDeployer
from printer import Printer
from settings import config

printer = Printer(settings.VERBOSE)


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

    res = []
    for f in all_files:
        printer.verbose("Checking timestamp of " + MAGENTA(f))
        res += modified(settings.HOME + '/' + f)
    return res


def missing_programs(programs, installed):
    return [prog for prog in programs if prog not in installed]


server_name = settings.SERVER

server_status = settings.SERVER_STATUS.default_status() if settings.FORCE else settings.SERVER_STATUS[server_name]

programs_to_install = missing_programs(config['programs'], server_status['installed_programs'])
files_to_deploy = modified_files(config['files'], server_status['last_modified'])

num_files_to_deploy = len(files_to_deploy)
num_programs_to_install = len(programs_to_install)
printer.verbose("Found " + MAGENTA(num_files_to_deploy) + " files to deploy and " + MAGENTA(
    num_programs_to_install) + " programs to install.")
if len(files_to_deploy) == 0 and len(programs_to_install) == 0:
    printer.verbose("No changes to " + MAGENTA(server_name) + ". Skipping deployment.")
    sys.exit(0)

config_deployer = ConfigDeployer(server_name, programs_to_install, files_to_deploy, printer)
success = config_deployer.deploy()
if success:
    printer.info(GREEN("Configuration successfully deployed."))
    settings.SERVER_STATUS.update(server_name)
    settings.SERVER_STATUS.save()
