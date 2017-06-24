import fnmatch
import os.path
import signal
import sys

from configuration import settings
from configuration.settings import config
from deployment import ConfigDeployer
from formatting.colors import *
from formatting.printer import Printer

printer = Printer(settings.VERBOSE)


def modified_files(all_files, last_modified):
    modified_files.res = []

    def modified(file):
        for ignore in config['ignore_files']:
            if fnmatch.fnmatch(file, ignore):
                return
        if os.path.isdir(file):
            for f in os.listdir(file):
                modified(file + '/' + f)
            return

        if os.path.getctime(file) > last_modified:
            modified_files.res.append(os.path.abspath(file))

    for f in all_files:
        printer.verbose("Checking timestamp of " + MAGENTA(f))
        modified(settings.HOME + '/' + f)

    return modified_files.res


def missing_programs(programs, installed):
    return [prog for prog in programs if prog not in installed]


def signal_handler(signal, frame):
    printer.info(RED("Received Ctrl+C, exiting..."))
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

server_name = settings.SERVER

server_status = settings.SERVER_STATUS.initial_status() if settings.FORCE else settings.SERVER_STATUS[server_name]

programs_to_install = missing_programs(config['programs'], server_status['installed_programs'])
files_to_deploy = modified_files(config['files'], server_status['last_modified'])

printer.verbose("Found " + MAGENTA(len(files_to_deploy)) + " files to deploy and " + MAGENTA(
    len(programs_to_install)) + " programs to install.")
if len(files_to_deploy) == 0 and len(programs_to_install) == 0:
    printer.verbose("No changes to " + MAGENTA(server_name) + ". Skipping deployment.")
    sys.exit(0)

config_deployer = ConfigDeployer(server_name, programs_to_install, files_to_deploy, printer)
success = config_deployer.deploy()
if success:
    printer.info(GREEN("Configuration successfully deployed."))
    settings.SERVER_STATUS.update(server_name)
    settings.SERVER_STATUS.save()
